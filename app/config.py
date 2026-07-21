from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "دانشیار | موتور هوشمند محتوای آموزشی")
    app_env: str = os.getenv("APP_ENV", "development")
    host: str = os.getenv("APP_HOST", "0.0.0.0")
    port: int = int(os.getenv("APP_PORT", "8000"))
    data_dir: Path = Path(os.getenv("DATA_DIR", "./data")).resolve()
    max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "50"))
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "1200"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "180"))
    top_k: int = int(os.getenv("TOP_K", "6"))
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY") or None
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5-mini")
    openai_embedding_model: str = os.getenv(
        "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
    )
    use_openai_embeddings: bool = _as_bool(os.getenv("USE_OPENAI_EMBEDDINGS"), False)
    trust_proxy_headers: bool = _as_bool(os.getenv("TRUST_PROXY_HEADERS"), False)

    @property
    def db_path(self) -> Path:
        return self.data_dir / "daneshyar.sqlite3"

    @property
    def upload_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def export_dir(self) -> Path:
        return self.data_dir / "exports"

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.export_dir.mkdir(parents=True, exist_ok=True)
