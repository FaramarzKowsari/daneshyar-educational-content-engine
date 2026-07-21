from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Asset, Chunk
from app.services.llm import LLMService
from app.services.text_utils import sentence_split


@dataclass(slots=True)
class GeneratedAsset:
    asset_type: str
    chapter: str
    title: str
    content: str
    mode: str


class ContentGenerator:
    def __init__(self, llm: LLMService):
        self.llm = llm

    def get_context(self, session: Session, book_id: int, chapter: str | None) -> tuple[str, str]:
        stmt = select(Chunk).where(Chunk.book_id == book_id).order_by(Chunk.position)
        if chapter:
            stmt = stmt.where(Chunk.chapter == chapter)
        chunks = list(session.scalars(stmt))
        if not chunks:
            raise ValueError("برای فصل انتخاب‌شده محتوایی پیدا نشد.")
        selected = chunks[:30]
        context = "\n\n".join(
            f"[صفحه {c.page_start} | {c.chapter}]\n{c.text}" for c in selected
        )
        label = chapter or "کل کتاب"
        return context[:30000], label

    def summary(self, session: Session, book_id: int, chapter: str | None) -> GeneratedAsset:
        context, label = self.get_context(session, book_id, chapter)
        task = (
            "یک خلاصه دانشگاهی سه‌لایه تولید کن: ۱) مرور سریع، ۲) نکات امتحانی، "
            "۳) مفاهیم کلیدی. فقط از متن استفاده کن و ارجاع صفحه را حفظ کن."
        )
        result = self.llm.generate_text(task, context)
        return GeneratedAsset("summary", label, f"خلاصهٔ {label}", result.text, result.mode)

    def quiz(
        self, session: Session, book_id: int, chapter: str | None, count: int
    ) -> GeneratedAsset:
        context, label = self.get_context(session, book_id, chapter)
        fallback = self._fallback_quiz(context, count)
        task = f"""{count} سؤال آموزشی تولید کن. دست‌کم نیمی چهارگزینه‌ای و بقیه تشریحی باشند.
خروجی باید آرایه JSON با این فیلدها باشد:
type, question, options, answer, explanation, difficulty, source_page
options برای سؤال تشریحی آرایه خالی باشد. source_page باید فقط از شماره صفحه‌های متن باشد."""
        data, mode = self.llm.generate_json(task, context, fallback)
        return GeneratedAsset(
            "quiz", label, f"آزمون {label}", json.dumps(data, ensure_ascii=False, indent=2), mode
        )

    def flashcards(
        self, session: Session, book_id: int, chapter: str | None, count: int
    ) -> GeneratedAsset:
        context, label = self.get_context(session, book_id, chapter)
        fallback = self._fallback_flashcards(context, count)
        task = f"""{count} فلش‌کارت تولید کن. خروجی آرایه JSON با فیلدهای
question, answer, hint, difficulty, source_page باشد. پاسخ‌ها کوتاه، دقیق و مبتنی بر متن باشند."""
        data, mode = self.llm.generate_json(task, context, fallback)
        return GeneratedAsset(
            "flashcards",
            label,
            f"فلش‌کارت‌های {label}",
            json.dumps(data, ensure_ascii=False, indent=2),
            mode,
        )

    def mindmap(self, session: Session, book_id: int, chapter: str | None) -> GeneratedAsset:
        context, label = self.get_context(session, book_id, chapter)
        fallback = self._fallback_mindmap(context, label)
        task = """یک نقشه مفهومی سلسله‌مراتبی بساز. خروجی JSON باشد:
{"root":"...","children":[{"label":"...","children":[{"label":"..."}]}]}
حداکثر 6 شاخه اصلی و برای هر شاخه حداکثر 4 زیرشاخه."""
        data, mode = self.llm.generate_json(task, context, fallback)
        return GeneratedAsset(
            "mindmap", label, f"نقشهٔ مفهومی {label}", json.dumps(data, ensure_ascii=False), mode
        )

    @staticmethod
    def save(session: Session, book_id: int, generated: GeneratedAsset) -> Asset:
        asset = Asset(
            book_id=book_id,
            asset_type=generated.asset_type,
            chapter=generated.chapter,
            title=generated.title,
            content=generated.content,
            status="draft",
        )
        session.add(asset)
        session.commit()
        session.refresh(asset)
        return asset

    @staticmethod
    def _fallback_quiz(context: str, count: int) -> list[dict]:
        sentences = [s for s in sentence_split(context) if len(s) > 35]
        pages = re.findall(r"\[صفحه\s+(\d+)", context)
        page = int(pages[0]) if pages else 1
        questions = []
        for sentence in sentences[:count]:
            questions.append(
                {
                    "type": "descriptive",
                    "question": f"بر اساس متن، مفهوم عبارت زیر را توضیح دهید: «{sentence[:90]}…»",
                    "options": [],
                    "answer": sentence,
                    "explanation": "پاسخ مستقیماً از متن کتاب استخراج شده است.",
                    "difficulty": "متوسط",
                    "source_page": page,
                }
            )
        return questions

    @staticmethod
    def _fallback_flashcards(context: str, count: int) -> list[dict]:
        sentences = [s for s in sentence_split(context) if 30 < len(s) < 240]
        pages = re.findall(r"\[صفحه\s+(\d+)", context)
        page = int(pages[0]) if pages else 1
        return [
            {
                "question": f"نکتهٔ اصلی این گزاره چیست؟ «{sentence[:75]}…»",
                "answer": sentence,
                "hint": sentence.split()[0] if sentence.split() else "کتاب",
                "difficulty": "متوسط",
                "source_page": page,
            }
            for sentence in sentences[:count]
        ]

    @staticmethod
    def _fallback_mindmap(context: str, label: str) -> dict:
        words = re.findall(r"[\wآ-ی]{4,}", context.lower())
        stop = {"برای", "اینکه", "است", "شود", "شده", "دارد", "صفحه", "کتاب", "متن", "یک", "های"}
        common = [word for word, _ in Counter(w for w in words if w not in stop).most_common(20)]
        return {
            "root": label,
            "children": [
                {"label": word, "children": []} for word in common[:6]
            ],
        }
