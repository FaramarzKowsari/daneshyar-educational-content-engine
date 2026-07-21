from __future__ import annotations

from dataclasses import dataclass

from app.services.pdf_ingestion import PageText
from app.services.text_utils import normalize_text


@dataclass(slots=True)
class TextChunk:
    chapter: str
    page_start: int
    page_end: int
    position: int
    text: str


def build_chunks(
    pages: list[PageText], chunk_size: int = 1200, overlap: int = 180
) -> list[TextChunk]:
    if chunk_size < 300:
        raise ValueError("chunk_size must be at least 300")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be between 0 and chunk_size")

    chunks: list[TextChunk] = []
    position = 0

    for page in pages:
        text = normalize_text(page.text)
        if not text:
            continue
        start = 0
        while start < len(text):
            end = min(len(text), start + chunk_size)
            if end < len(text):
                boundary = max(
                    text.rfind(". ", start, end),
                    text.rfind("؟ ", start, end),
                    text.rfind("\n", start, end),
                )
                if boundary > start + chunk_size // 2:
                    end = boundary + 1
            piece = text[start:end].strip()
            if piece:
                chunks.append(
                    TextChunk(
                        chapter=page.chapter,
                        page_start=page.page_number,
                        page_end=page.page_number,
                        position=position,
                        text=piece,
                    )
                )
                position += 1
            if end >= len(text):
                break
            start = max(start + 1, end - overlap)

    return chunks
