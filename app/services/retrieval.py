from __future__ import annotations

import json
from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Chunk
from app.services.embeddings import EmbeddingService


@dataclass(slots=True)
class SearchHit:
    chunk: Chunk
    score: float


class RetrievalService:
    def __init__(self, settings: Settings, embedding_service: EmbeddingService):
        self.settings = settings
        self.embedding_service = embedding_service

    def search(
        self,
        session: Session,
        book_id: int,
        query: str,
        top_k: int | None = None,
        chapter: str | None = None,
    ) -> list[SearchHit]:
        stmt = select(Chunk).where(Chunk.book_id == book_id).order_by(Chunk.position)
        if chapter:
            stmt = stmt.where(Chunk.chapter == chapter)
        chunks = list(session.scalars(stmt))
        if not chunks:
            return []

        texts = [chunk.text for chunk in chunks]
        lexical_scores = self._lexical_scores(texts, query)
        semantic_scores = self._semantic_scores(chunks, query)

        if semantic_scores is None:
            final = lexical_scores
        else:
            final = 0.45 * lexical_scores + 0.55 * semantic_scores

        k = min(top_k or self.settings.top_k, len(chunks))
        indices = np.argsort(final)[::-1][:k]
        return [SearchHit(chunks[int(i)], float(final[int(i)])) for i in indices if final[int(i)] > 0]

    @staticmethod
    def _lexical_scores(texts: list[str], query: str) -> np.ndarray:
        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=1,
            max_features=20000,
            analyzer="word",
        )
        matrix = vectorizer.fit_transform(texts + [query])
        scores = cosine_similarity(matrix[-1], matrix[:-1]).ravel()
        max_score = scores.max(initial=0.0)
        return scores / max_score if max_score > 0 else scores

    def _semantic_scores(self, chunks: list[Chunk], query: str) -> np.ndarray | None:
        if not self.embedding_service.enabled:
            return None
        query_vector = self.embedding_service.embed_one(query)
        if query_vector is None:
            return None
        vectors: list[list[float]] = []
        valid_indices: list[int] = []
        for index, chunk in enumerate(chunks):
            if not chunk.embedding_json:
                continue
            try:
                vectors.append(json.loads(chunk.embedding_json))
                valid_indices.append(index)
            except json.JSONDecodeError:
                continue
        if not vectors:
            return None
        matrix = np.asarray(vectors, dtype=float)
        q = np.asarray(query_vector, dtype=float).reshape(1, -1)
        partial = cosine_similarity(q, matrix).ravel()
        scores = np.zeros(len(chunks), dtype=float)
        for index, value in zip(valid_indices, partial, strict=True):
            scores[index] = value
        minimum = scores.min(initial=0.0)
        maximum = scores.max(initial=0.0)
        if maximum > minimum:
            scores = (scores - minimum) / (maximum - minimum)
        return scores
