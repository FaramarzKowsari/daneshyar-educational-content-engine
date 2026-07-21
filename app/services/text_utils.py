from __future__ import annotations

import re
from collections.abc import Iterable

PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")


def normalize_text(text: str) -> str:
    text = text.replace("\u200c", " ").replace("\u00a0", " ")
    text = text.replace("ي", "ی").replace("ك", "ک")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def sentence_split(text: str) -> list[str]:
    text = normalize_text(text)
    parts = re.split(r"(?<=[.!؟?؛;])\s+|\n+", text)
    return [p.strip() for p in parts if len(p.strip()) > 12]


def detect_heading(lines: Iterable[str]) -> str | None:
    patterns = [
        r"^(فصل|بخش)\s+[\w\d۰-۹]+(?:\s*[:：-]\s*|\s+).{0,100}$",
        r"^(chapter|unit|part)\s+[\w\d]+(?:\s*[:：-]\s*|\s+).{0,100}$",
    ]
    for raw in lines:
        line = normalize_text(raw).strip("-–—• ")
        if not (3 <= len(line) <= 120):
            continue
        if any(re.match(p, line, flags=re.IGNORECASE) for p in patterns):
            return line
        letters = [c for c in line if c.isalpha()]
        if letters and len(line.split()) <= 10 and line.upper() == line and len(line) > 4:
            return line.title()
    return None


def slugify(value: str) -> str:
    value = value.translate(PERSIAN_DIGITS)
    value = re.sub(r"[^\w\-]+", "-", value, flags=re.UNICODE)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "export"
