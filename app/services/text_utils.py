from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")

# Directional controls are useful for display, but they damage indexing/search when
# they are embedded in extracted PDF text.
_BIDI_CONTROLS_RE = re.compile(r"[\u200e\u200f\u202a-\u202e\u2066-\u2069\ufeff]")
_SPACE_BEFORE_PUNCT_RE = re.compile(r"\s+([،؛:؟!.,])")
_SPACE_AFTER_OPEN_RE = re.compile(r"([(\[«])\s+")
_SPACE_BEFORE_CLOSE_RE = re.compile(r"\s+([)\]»])")


def normalize_text(text: str) -> str:
    # NFKC converts many Arabic presentation-form glyphs and ligatures to their
    # normal Unicode characters. This is important for Persian PDFs.
    text = unicodedata.normalize("NFKC", text)
    text = _BIDI_CONTROLS_RE.sub("", text)
    text = text.replace("\u200c", " ").replace("\u00a0", " ")

    # Arabic-to-Persian character normalization.
    replacements = {
        "ي": "ی",
        "ى": "ی",
        "ئ": "ئ",
        "ك": "ک",
        "ۀ": "ه",
        "ة": "ه",
        "ؤ": "و",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)

    text = re.sub(r"[ \t]+", " ", text)
    text = _SPACE_BEFORE_PUNCT_RE.sub(r"\1", text)
    text = _SPACE_AFTER_OPEN_RE.sub(r"\1", text)
    text = _SPACE_BEFORE_CLOSE_RE.sub(r"\1", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
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
