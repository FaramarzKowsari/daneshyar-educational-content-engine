from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz

from app.services.text_utils import detect_heading, normalize_text


class PDFIngestionError(ValueError):
    pass


@dataclass(slots=True)
class PageText:
    page_number: int
    text: str
    chapter: str


@dataclass(slots=True)
class ParsedBook:
    page_count: int
    pages: list[PageText]
    detected_title: str | None


def parse_pdf(path: Path) -> ParsedBook:
    try:
        document = fitz.open(path)
    except Exception as exc:
        raise PDFIngestionError("فایل PDF قابل بازشدن نیست.") from exc

    if document.needs_pass:
        document.close()
        raise PDFIngestionError("PDF رمزگذاری شده است؛ ابتدا رمز را حذف کنید.")

    pages: list[PageText] = []
    current_chapter = "مقدمه"
    detected_title: str | None = None
    total_chars = 0

    try:
        for index, page in enumerate(document):
            blocks = page.get_text("blocks", sort=True)
            block_texts = [normalize_text(str(block[4])) for block in blocks if str(block[4]).strip()]
            text = normalize_text("\n".join(block_texts))
            total_chars += len(text)

            if index == 0:
                first_lines = [line.strip() for line in text.splitlines() if line.strip()]
                if first_lines:
                    detected_title = max(first_lines[:8], key=len)[:300]

            heading = detect_heading(text.splitlines()[:12])
            if heading:
                current_chapter = heading

            pages.append(PageText(index + 1, text, current_chapter))
    finally:
        page_count = len(document)
        document.close()

    if page_count == 0:
        raise PDFIngestionError("PDF هیچ صفحه‌ای ندارد.")
    if total_chars < max(100, page_count * 20):
        raise PDFIngestionError(
            "متن کافی از PDF استخراج نشد. این نسخهٔ MVP برای PDFهای متنی طراحی شده است؛ "
            "برای فایل اسکن‌شده ابتدا OCR انجام دهید."
        )

    return ParsedBook(page_count=page_count, pages=pages, detected_title=detected_title)
