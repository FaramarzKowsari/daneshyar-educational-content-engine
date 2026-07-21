from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Book, Chunk
from app.services.chunking import build_chunks
from app.services.embeddings import EmbeddingService
from app.services.pdf_ingestion import ParsedBook, parse_pdf


class BookService:
    def __init__(self, settings: Settings, embeddings: EmbeddingService):
        self.settings = settings
        self.embeddings = embeddings

    def _parse(self, path: Path) -> ParsedBook:
        return parse_pdf(
            path,
            max_pages=self.settings.max_pdf_pages,
            enable_ocr=self.settings.enable_ocr,
            ocr_languages=self.settings.ocr_languages,
            ocr_max_pages=self.settings.ocr_max_pages,
            ocr_dpi=self.settings.ocr_dpi,
        )

    def ingest(
        self,
        session: Session,
        path: Path,
        original_filename: str,
        title: str | None,
        author: str | None,
    ) -> Book:
        book = Book(
            title=(title or original_filename).strip()[:300],
            author=author.strip()[:200] if author and author.strip() else None,
            filename=original_filename,
            stored_path=str(path),
            page_count=0,
            status="processing",
        )
        session.add(book)
        session.commit()
        session.refresh(book)
        return self.ingest_existing(session, book, title=title, author=author)

    def ingest_existing(
        self,
        session: Session,
        book: Book,
        *,
        title: str | None = None,
        author: str | None = None,
    ) -> Book:
        path = Path(book.stored_path)
        parsed = self._parse(path)
        chunks = build_chunks(
            parsed.pages,
            chunk_size=self.settings.chunk_size,
            overlap=self.settings.chunk_overlap,
        )
        if not chunks:
            raise ValueError("هیچ قطعهٔ متنی قابل استفاده‌ای از کتاب ساخته نشد.")
        vectors = self.embeddings.embed_many([chunk.text for chunk in chunks])

        try:
            session.execute(delete(Chunk).where(Chunk.book_id == book.id))
            book.title = (title or parsed.detected_title or book.filename).strip()[:300]
            if author and author.strip():
                book.author = author.strip()[:200]
            book.page_count = parsed.page_count
            book.language = "fa"
            book.status = "ready"
            book.processing_error = None

            for chunk, vector in zip(chunks, vectors, strict=True):
                session.add(
                    Chunk(
                        book_id=book.id,
                        chapter=chunk.chapter,
                        page_start=chunk.page_start,
                        page_end=chunk.page_end,
                        position=chunk.position,
                        text=chunk.text,
                        embedding_json=json.dumps(vector) if vector else None,
                    )
                )
            session.commit()
            session.refresh(book)
            return book
        except Exception:
            session.rollback()
            raise
