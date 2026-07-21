from __future__ import annotations

import json
from pathlib import Path

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

    def ingest(
        self,
        session: Session,
        path: Path,
        original_filename: str,
        title: str | None,
        author: str | None,
    ) -> Book:
        parsed: ParsedBook = parse_pdf(path)
        chunks = build_chunks(
            parsed.pages,
            chunk_size=self.settings.chunk_size,
            overlap=self.settings.chunk_overlap,
        )
        vectors = self.embeddings.embed_many([chunk.text for chunk in chunks])

        book = Book(
            title=(title or parsed.detected_title or original_filename).strip()[:300],
            author=author.strip()[:200] if author and author.strip() else None,
            filename=original_filename,
            stored_path=str(path),
            page_count=parsed.page_count,
            status="ready",
        )
        try:
            session.add(book)
            session.flush()
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
