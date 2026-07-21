from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz

from app.services.text_utils import detect_heading, normalize_text

try:
    import pytesseract
    from PIL import Image
except ImportError:  # OCR is optional outside the Docker image
    pytesseract = None  # type: ignore[assignment]
    Image = None  # type: ignore[assignment,misc]


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
    used_ocr: bool = False


def _ocr_page(page: fitz.Page, languages: str, dpi: int) -> str:
    if pytesseract is None or Image is None:
        return ""
    scale = dpi / 72
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
    image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    return normalize_text(pytesseract.image_to_string(image, lang=languages))


def parse_pdf(
    path: Path,
    *,
    max_pages: int = 250,
    enable_ocr: bool = False,
    ocr_languages: str = "fas+eng",
    ocr_max_pages: int = 60,
    ocr_dpi: int = 180,
) -> ParsedBook:
    try:
        document = fitz.open(path)
    except Exception as exc:
        raise PDFIngestionError("فایل PDF قابل بازشدن نیست.") from exc

    if document.needs_pass:
        document.close()
        raise PDFIngestionError("PDF رمزگذاری شده است؛ ابتدا رمز را حذف کنید.")

    page_count = len(document)
    if page_count == 0:
        document.close()
        raise PDFIngestionError("PDF هیچ صفحه‌ای ندارد.")
    if page_count > max_pages:
        document.close()
        raise PDFIngestionError(f"حداکثر تعداد صفحه برای نسخهٔ عمومی {max_pages} صفحه است.")

    pages: list[PageText] = []
    current_chapter = "مقدمه"
    detected_title: str | None = None
    total_chars = 0
    used_ocr = False

    try:
        for index, page in enumerate(document):
            blocks = page.get_text("blocks", sort=True)
            block_texts = [
                normalize_text(str(block[4])) for block in blocks if str(block[4]).strip()
            ]
            text = normalize_text("\n".join(block_texts))

            # OCR only pages whose text layer is nearly empty. This keeps textual PDFs fast.
            if (
                enable_ocr
                and len(text) < 35
                and index < ocr_max_pages
                and pytesseract is not None
            ):
                ocr_text = _ocr_page(page, ocr_languages, ocr_dpi)
                if len(ocr_text) > len(text):
                    text = ocr_text
                    used_ocr = True

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
        document.close()

    if total_chars < max(100, page_count * 20):
        if enable_ocr and page_count > ocr_max_pages:
            raise PDFIngestionError(
                "متن کافی استخراج نشد. فایل احتمالاً اسکن‌شده است و تعداد صفحات آن از سقف OCR "
                f"نسخهٔ عمومی ({ocr_max_pages} صفحه) بیشتر است."
            )
        raise PDFIngestionError(
            "متن کافی از PDF استخراج نشد. PDF باید لایهٔ متن داشته باشد یا OCR آن با زبان‌های "
            "فارسی/انگلیسی قابل تشخیص باشد."
        )

    return ParsedBook(
        page_count=page_count,
        pages=pages,
        detected_title=detected_title,
        used_ocr=used_ocr,
    )
