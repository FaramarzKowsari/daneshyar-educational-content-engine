from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _csv(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(item.strip() for item in value.split(",") if item.strip())


@dataclass(slots=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "دانشیار | موتور هوشمند محتوای آموزشی")
    app_env: str = os.getenv("APP_ENV", "development")
    host: str = os.getenv("APP_HOST", "0.0.0.0")
    port: int = int(os.getenv("APP_PORT", os.getenv("PORT", "8000")))
    data_dir: Path = Path(os.getenv("DATA_DIR", "./data")).resolve()
    database_url: str | None = os.getenv("DATABASE_URL") or None

    max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "25"))
    max_pdf_pages: int = int(os.getenv("MAX_PDF_PAGES", "250"))
    public_book_ttl_hours: int = int(os.getenv("PUBLIC_BOOK_TTL_HOURS", "24"))
    public_uploads_per_hour: int = int(os.getenv("PUBLIC_UPLOADS_PER_HOUR", "3"))
    public_chat_per_hour: int = int(os.getenv("PUBLIC_CHAT_PER_HOUR", "30"))
    public_generations_per_hour: int = int(os.getenv("PUBLIC_GENERATIONS_PER_HOUR", "12"))

    chunk_size: int = int(os.getenv("CHUNK_SIZE", "1200"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "180"))
    top_k: int = int(os.getenv("TOP_K", "6"))

    openai_api_key: str | None = os.getenv("OPENAI_API_KEY") or None
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5-mini")
    openai_embedding_model: str = os.getenv(
        "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
    )
    use_openai_embeddings: bool = _as_bool(os.getenv("USE_OPENAI_EMBEDDINGS"), False)

    enable_ocr: bool = _as_bool(os.getenv("ENABLE_OCR"), True)
    ocr_languages: str = os.getenv("OCR_LANGUAGES", "fas+eng")
    ocr_max_pages: int = int(os.getenv("OCR_MAX_PAGES", "60"))
    ocr_dpi: int = int(os.getenv("OCR_DPI", "180"))

    allowed_origins: tuple[str, ...] = _csv(os.getenv("ALLOWED_ORIGINS"))
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

    @property
    def public_dir(self) -> Path:
        return Path(__file__).resolve().parent / "public"

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.export_dir.mkdir(parents=True, exist_ok=True)
