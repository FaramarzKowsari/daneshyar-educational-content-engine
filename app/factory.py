from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import Settings
from app.db import Database
from app.routes import router
from app.service_container import Services
from app.services.book_service import BookService
from app.services.embeddings import EmbeddingService
from app.services.generators import ContentGenerator
from app.services.llm import LLMService
from app.services.pptx_export import SlideExporter
from app.services.retrieval import RetrievalService


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

    app = FastAPI(
        title="Daneshyar Educational Content Engine",
        description="Grounded educational assistant for university PDF textbooks.",
        version="0.1.0",
    )
    app.state.settings = settings
    app.state.database = database
    app.state.services = services
    package_dir = Path(__file__).resolve().parent
    app.state.templates = Jinja2Templates(directory=str(package_dir / "templates"))

    app.mount("/static", StaticFiles(directory=str(package_dir / "static")), name="static")
    app.include_router(router)
    return app
