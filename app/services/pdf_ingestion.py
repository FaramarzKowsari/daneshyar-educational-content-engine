from __future__ import annotations

import re
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


_WORD_RE = re.compile(r"[A-Za-z\u0600-\u06FF]+", flags=re.UNICODE)
_PERSIAN_RE = re.compile(r"[\u0600-\u06FF]", flags=re.UNICODE)
_PRIVATE_USE_RE = re.compile(r"[\uE000-\uF8FF]")


def _text_metrics(text: str) -> tuple[int, float, float, float]:
    """Return token count, one-letter ratio, short-token ratio and average token length."""
    tokens = _WORD_RE.findall(normalize_text(text))
    if not tokens:
        return 0, 1.0, 1.0, 0.0
    one_letter = sum(len(token) == 1 for token in tokens) / len(tokens)
    short = sum(len(token) <= 2 for token in tokens) / len(tokens)
    average = sum(len(token) for token in tokens) / len(tokens)
    return len(tokens), one_letter, short, average


def _looks_corrupted(text: str) -> bool:
    """Detect the common Persian-PDF failure where words become spaced-out letters."""
    normalized = normalize_text(text)
    if not normalized:
        return True

    token_count, one_letter_ratio, short_ratio, average_length = _text_metrics(normalized)
    persian_chars = len(_PERSIAN_RE.findall(normalized))
    replacement_count = normalized.count("\ufffd")
    private_use_count = len(_PRIVATE_USE_RE.findall(normalized))

    if replacement_count or private_use_count:
        return True

    # A Persian prose page should not consist mostly of one-character tokens.
    # This catches text such as: "ه د ف ا ز ی ا د گ ی ر ی ..."
    if persian_chars >= 20 and token_count >= 10:
        if one_letter_ratio >= 0.28:
            return True
        if short_ratio >= 0.68 and average_length < 2.35:
            return True

    return False


def _quality_score(text: str) -> float:
    """Higher means a more readable extraction candidate."""
    normalized = normalize_text(text)
    token_count, one_letter_ratio, short_ratio, average_length = _text_metrics(normalized)
    if token_count == 0:
        return -100.0

    score = min(average_length, 8.0) * 1.6
    score += (1.0 - one_letter_ratio) * 7.0
    score += (1.0 - short_ratio) * 2.0
    score += min(token_count, 80) / 40.0
    if _looks_corrupted(normalized):
        score -= 12.0
    return score


def _native_text_candidates(page: fitz.Page) -> list[str]:
    candidates: list[str] = []

    # Different PDFs preserve Persian reading order differently. Trying both
    # sorted and original order often repairs RTL extraction without OCR.
    for sort in (False, True):
        try:
            candidates.append(normalize_text(page.get_text("text", sort=sort)))
        except Exception:
            pass

        try:
            blocks = page.get_text("blocks", sort=sort)
            block_text = "\n".join(
                normalize_text(str(block[4]))
                for block in blocks
                if len(block) > 4 and str(block[4]).strip()
            )
            candidates.append(normalize_text(block_text))
        except Exception:
            pass

    return [candidate for candidate in candidates if candidate]


def _best_native_text(page: fitz.Page) -> str:
    candidates = _native_text_candidates(page)
    if not candidates:
        return ""
    return max(candidates, key=_quality_score)


def _ocr_page(page: fitz.Page, languages: str, dpi: int) -> str:
    if pytesseract is None or Image is None:
        return ""
    scale = dpi / 72
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
    image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    result = pytesseract.image_to_string(
        image,
        lang=languages,
        config="--oem 1 --psm 3 -c preserve_interword_spaces=1",
    )
    return normalize_text(result)


def parse_pdf(
    path: Path,
    *,
    max_pages: int = 250,
    enable_ocr: bool = False,
    ocr_languages: str = "fas+eng",
    ocr_max_pages: int = 60,
    ocr_dpi: int = 160,
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
    corrupted_pages = 0

    try:
        for index, page in enumerate(document):
            native_text = _best_native_text(page)
            text = native_text
            native_corrupted = _looks_corrupted(native_text)

            # Previous behavior only ran OCR when the text layer was nearly empty.
            # Persian PDFs can contain a long but unusable text layer, so OCR must
            # also run when the extracted words are fragmented or malformed.
            should_ocr = (
                enable_ocr
                and index < ocr_max_pages
                and pytesseract is not None
                and (len(native_text) < 35 or native_corrupted)
            )

            if should_ocr:
                ocr_text = _ocr_page(page, ocr_languages, ocr_dpi)
                if ocr_text and (
                    len(native_text) < 35
                    or native_corrupted
                    or _quality_score(ocr_text) > _quality_score(native_text)
                ):
                    text = ocr_text
                    used_ocr = True

            if _looks_corrupted(text):
                corrupted_pages += 1
                # Do not index obviously broken glyph sequences.
                text = ""

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

    if corrupted_pages and corrupted_pages > max(2, page_count // 3):
        raise PDFIngestionError(
            "لایهٔ متن فارسی این PDF به‌هم‌ریخته است و OCR کافی انجام نشد. "
            "نسخهٔ OCRشدهٔ PDF را بارگذاری کنید یا سقف OCR را برای این فایل افزایش دهید."
        )

    if total_chars < max(100, page_count * 20):
        if enable_ocr and page_count > ocr_max_pages:
            raise PDFIngestionError(
                "متن کافی استخراج نشد. فایل احتمالاً اسکن‌شده یا دارای فونت فارسی ناسازگار است "
                f"و تعداد صفحات آن از سقف OCR نسخهٔ عمومی ({ocr_max_pages} صفحه) بیشتر است."
            )
        raise PDFIngestionError(
            "متن سالم کافی از PDF استخراج نشد. PDF باید لایهٔ متن استاندارد داشته باشد "
            "یا OCR فارسی/انگلیسی آن قابل تشخیص باشد."
        )

    return ParsedBook(
        page_count=page_count,
        pages=pages,
        detected_title=detected_title,
        used_ocr=used_ocr,
    )
