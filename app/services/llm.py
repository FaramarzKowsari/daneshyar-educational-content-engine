from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

try:
    from openai import OpenAI
except ImportError:  # optional at runtime when local fallback is used
    OpenAI = None  # type: ignore[assignment,misc]

from app.config import Settings
from app.services.text_utils import sentence_split


@dataclass(slots=True)
class LLMResult:
    text: str
    mode: str


class LLMService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.enabled = bool(settings.openai_api_key and OpenAI)
        self.client = OpenAI(api_key=settings.openai_api_key) if self.enabled and OpenAI else None

    def grounded_answer(self, question: str, context: str) -> LLMResult:
        if self.enabled and self.client is not None:
            response = self.client.responses.create(
                model=self.settings.openai_model,
                store=False,
                instructions=(
                    "You are a Persian university teaching assistant. Answer only from the supplied "
                    "textbook excerpts. If the answer is not supported, say that the book does not "
                    "provide enough evidence. Be precise, readable, and do not invent page numbers."
                ),
                input=f"پرسش دانشجو:\n{question}\n\nبخش‌های بازیابی‌شده از کتاب:\n{context}",
            )
            return LLMResult(response.output_text.strip(), "openai")
        return LLMResult(self._extractive_answer(question, context), "local-fallback")

    def generate_text(self, task: str, context: str) -> LLMResult:
        if self.enabled and self.client is not None:
            response = self.client.responses.create(
                model=self.settings.openai_model,
                store=False,
                instructions=(
                    "You are an expert instructional designer. Work only with the supplied textbook "
                    "context. Write in clear modern Persian. Never claim unsupported facts."
                ),
                input=f"وظیفه:\n{task}\n\nمتن کتاب:\n{context}",
            )
            return LLMResult(response.output_text.strip(), "openai")
        return LLMResult(self._fallback_text(task, context), "local-fallback")

    def generate_json(self, task: str, context: str, fallback: Any) -> tuple[Any, str]:
        result = self.generate_text(
            task + "\nOnly return valid JSON. Do not wrap it in markdown code fences.", context
        )
        if result.mode == "openai":
            try:
                return json.loads(self._strip_code_fence(result.text)), result.mode
            except json.JSONDecodeError:
                return fallback, "local-fallback"
        return fallback, result.mode

    @staticmethod
    def _strip_code_fence(text: str) -> str:
        match = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else text.strip()

    @staticmethod
    def _extractive_answer(question: str, context: str) -> str:
        question_words = {w for w in re.findall(r"\w+", question.lower()) if len(w) > 2}
        sentences = sentence_split(context)
        ranked = sorted(
            sentences,
            key=lambda sentence: sum(word in sentence.lower() for word in question_words),
            reverse=True,
        )
        chosen = [sentence for sentence in ranked[:4] if sentence]
        if not chosen:
            return "در بخش‌های بازیابی‌شده از کتاب، شواهد کافی برای پاسخ دقیق پیدا نشد."
        return "بر اساس متن کتاب: " + " ".join(chosen)

    @staticmethod
    def _fallback_text(task: str, context: str) -> str:
        sentences = sentence_split(context)
        if "خلاصه" in task:
            return "\n".join(f"• {sentence}" for sentence in sentences[:10])
        return "\n".join(sentences[:12])
