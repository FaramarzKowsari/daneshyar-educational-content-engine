from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, suppress
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from app.config import Settings
from app.db import Database
from app.models import Book, PublicAccess
from app.public_pages import router as public_pages_router
from app.public_routes import router as public_api_router
from app.rate_limit import SlidingWindowLimiter
from app.routes import router as classic_router
from app.service_container import Services
from app.services.book_service import BookService
from app.services.embeddings import EmbeddingService
from app.services.generators import ContentGenerator
from app.services.llm import LLMService
from app.services.pptx_export import SlideExporter
from app.services.retrieval import RetrievalService


def _cleanup_expired(app: FastAPI) -> None:
    now = datetime.utcnow()
    with app.state.database.session_factory() as session:
        expired = list(session.scalars(select(PublicAccess).where(PublicAccess.expires_at <= now)))
        for access in expired:
            book = session.get(Book, access.book_id)
            if book:
                Path(book.stored_path).unlink(missing_ok=True)
                session.delete(book)
        session.commit()


async def _cleanup_loop(app: FastAPI) -> None:
    while True:
        await asyncio.sleep(3600)
        await asyncio.to_thread(_cleanup_expired, app)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    settings.ensure_directories()
    database = Database(settings)
    database.create_all()

    embeddings = EmbeddingService(settings)
    llm = LLMService(settings)
    services = Services(
        embeddings=embeddings,
        llm=llm,
        retrieval=RetrievalService(settings, embeddings),
        generator=ContentGenerator(llm),
        book=BookService(settings, embeddings),
        slides=SlideExporter(llm, settings.export_dir),
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        cleanup_task = asyncio.create_task(_cleanup_loop(app))
        await asyncio.to_thread(_cleanup_expired, app)
        try:
            yield
        finally:
            cleanup_task.cancel()
            with suppress(asyncio.CancelledError):
                await cleanup_task

    app = FastAPI(
        title="Daneshyar Educational Content Engine",
        description="Public beta for turning user-supplied university PDFs into grounded learning assets.",
        version="0.2.0",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.database = database
    app.state.services = services
    app.state.rate_limiter = SlidingWindowLimiter()

    package_dir = Path(__file__).resolve().parent
    app.state.templates = Jinja2Templates(directory=str(package_dir / "templates"))
    app.mount("/static", StaticFiles(directory=str(package_dir / "static")), name="static")

    if settings.allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.allowed_origins),
            allow_credentials=False,
            allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
            allow_headers=["Content-Type", "X-Daneshyar-Token"],
        )

    app.include_router(public_pages_router)
    app.include_router(public_api_router)
    app.include_router(classic_router)
    return app
