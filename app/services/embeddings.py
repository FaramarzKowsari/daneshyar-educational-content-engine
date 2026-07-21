from __future__ import annotations

from collections.abc import Sequence

try:
    from openai import OpenAI
except ImportError:  # optional at runtime when local fallback is used
    OpenAI = None  # type: ignore[assignment,misc]

from app.config import Settings


class EmbeddingService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.enabled = bool(settings.openai_api_key and settings.use_openai_embeddings and OpenAI)
        self.client = OpenAI(api_key=settings.openai_api_key) if self.enabled and OpenAI else None

    def embed_many(self, texts: Sequence[str], batch_size: int = 64) -> list[list[float] | None]:
        if not self.enabled or self.client is None:
            return [None] * len(texts)
        output: list[list[float] | None] = []
        try:
            for start in range(0, len(texts), batch_size):
                batch = list(texts[start : start + batch_size])
                response = self.client.embeddings.create(
                    model=self.settings.openai_embedding_model,
                    input=batch,
                )
                output.extend(item.embedding for item in response.data)
            return output
        except Exception:
            # Embeddings improve semantic retrieval, but ingestion must remain available
            # when the external provider is unavailable or quota-limited.
            return [None] * len(texts)

    def embed_one(self, text: str) -> list[float] | None:
        vectors = self.embed_many([text], batch_size=1)
        return vectors[0]
