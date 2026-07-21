from __future__ import annotations

from dataclasses import dataclass

from app.services.book_service import BookService
from app.services.embeddings import EmbeddingService
from app.services.generators import ContentGenerator
from app.services.llm import LLMService
from app.services.pptx_export import SlideExporter
from app.services.retrieval import RetrievalService


@dataclass(slots=True)
class Services:
    embeddings: EmbeddingService
    llm: LLMService
    retrieval: RetrievalService
    generator: ContentGenerator
    book: BookService
    slides: SlideExporter
