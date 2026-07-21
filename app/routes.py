from __future__ import annotations

import json
import secrets
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from sqlalchemy import distinct, select
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_services
from app.models import Asset, Book, ChatLog, Chunk
from app.schemas import AssetResponse, ChatRequest, ChatResponse, Citation, GenerateRequest
from app.service_container import Services
from app.services.pdf_ingestion import PDFIngestionError
from app.services.text_utils import slugify

router = APIRouter()

DBSession = Annotated[Session, Depends(get_db)]
ServiceSet = Annotated[Services, Depends(get_services)]
PDFUpload = Annotated[UploadFile, File(...)]
OptionalForm = Annotated[str | None, Form()]


@router.get("/health")
def health(request: Request) -> dict:
    return {
        "status": "ok",
        "app": request.app.state.settings.app_name,
        "llm_enabled": request.app.state.services.llm.enabled,
        "semantic_embeddings_enabled": request.app.state.services.embeddings.enabled,
    }


@router.get("/classic", response_class=HTMLResponse)
def dashboard(request: Request, session: DBSession):
    books = list(session.scalars(select(Book).order_by(Book.created_at.desc())))
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"books": books, "settings": request.app.state.settings},
    )


@router.post("/books/upload")
async def upload_book(
    request: Request,
    session: DBSession,
    services: ServiceSet,
    file: PDFUpload,
    title: OptionalForm = None,
    author: OptionalForm = None,
):
    settings = request.app.state.settings
    filename = file.filename or "book.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(400, "فقط فایل PDF پذیرفته می‌شود.")
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(400, "نوع فایل معتبر نیست.")

    content = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"حداکثر حجم مجاز {settings.max_upload_mb} مگابایت است.")
    if not content.startswith(b"%PDF"):
        raise HTTPException(400, "امضای فایل PDF معتبر نیست.")

    safe_name = slugify(Path(filename).stem) + ".pdf"
    stored = settings.upload_dir / f"{secrets.token_hex(8)}-{safe_name}"
    stored.write_bytes(content)

    try:
        book = services.book.ingest(session, stored, filename, title, author)
    except PDFIngestionError as exc:
        stored.unlink(missing_ok=True)
        raise HTTPException(422, str(exc)) from exc
    except Exception:
        stored.unlink(missing_ok=True)
        raise
    return RedirectResponse(url=f"/books/{book.id}", status_code=303)


@router.get("/books/{book_id}", response_class=HTMLResponse)
def book_page(request: Request, book_id: int, session: DBSession):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(404, "کتاب پیدا نشد.")
    chapters = list(
        session.scalars(
            select(distinct(Chunk.chapter)).where(Chunk.book_id == book_id).order_by(Chunk.chapter)
        )
    )
    assets = list(
        session.scalars(select(Asset).where(Asset.book_id == book_id).order_by(Asset.created_at.desc()))
    )
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="book.html",
        context={"book": book, "chapters": chapters, "assets": assets},
    )


@router.post("/api/books/{book_id}/chat", response_model=ChatResponse)
def chat(
    book_id: int,
    payload: ChatRequest,
    session: DBSession,
    services: ServiceSet,
):
    if not session.get(Book, book_id):
        raise HTTPException(404, "کتاب پیدا نشد.")
    hits = services.retrieval.search(session, book_id, payload.question)
    if not hits:
        return ChatResponse(
            answer="در کتاب محتوای مرتبط کافی پیدا نشد.", citations=[], mode="local-fallback"
        )
    context_parts = []
    citations: list[Citation] = []
    for hit in hits:
        chunk = hit.chunk
        context_parts.append(f"[صفحه {chunk.page_start} | {chunk.chapter}]\n{chunk.text}")
        citations.append(
            Citation(
                chunk_id=chunk.id,
                page_start=chunk.page_start,
                page_end=chunk.page_end,
                chapter=chunk.chapter,
                excerpt=chunk.text[:280],
                score=round(hit.score, 4),
            )
        )
    result = services.llm.grounded_answer(payload.question, "\n\n".join(context_parts))
    log = ChatLog(
        book_id=book_id,
        question=payload.question,
        answer=result.text,
        citations_json=json.dumps([c.model_dump() for c in citations], ensure_ascii=False),
    )
    session.add(log)
    session.commit()
    return ChatResponse(answer=result.text, citations=citations, mode=result.mode)


@router.post("/api/books/{book_id}/generate/{asset_type}", response_model=AssetResponse)
def generate_asset(
    book_id: int,
    asset_type: str,
    payload: GenerateRequest,
    session: DBSession,
    services: ServiceSet,
):
    if not session.get(Book, book_id):
        raise HTTPException(404, "کتاب پیدا نشد.")
    try:
        if asset_type == "summary":
            generated = services.generator.summary(session, book_id, payload.chapter)
        elif asset_type == "quiz":
            generated = services.generator.quiz(session, book_id, payload.chapter, payload.count)
        elif asset_type == "flashcards":
            generated = services.generator.flashcards(session, book_id, payload.chapter, payload.count)
        elif asset_type == "mindmap":
            generated = services.generator.mindmap(session, book_id, payload.chapter)
        else:
            raise HTTPException(400, "نوع خروجی پشتیبانی نمی‌شود.")
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    asset = services.generator.save(session, book_id, generated)
    try:
        content = json.loads(asset.content)
    except json.JSONDecodeError:
        content = asset.content
    return AssetResponse(
        id=asset.id,
        asset_type=asset.asset_type,
        chapter=asset.chapter,
        title=asset.title,
        content=content,
        status=asset.status,
    )


@router.post("/api/assets/{asset_id}/approve")
def approve_asset(asset_id: int, session: DBSession):
    asset = session.get(Asset, asset_id)
    if not asset:
        raise HTTPException(404, "خروجی پیدا نشد.")
    asset.status = "approved"
    session.commit()
    return {"id": asset.id, "status": asset.status}


@router.get("/api/assets/{asset_id}")
def get_asset(asset_id: int, session: DBSession):
    asset = session.get(Asset, asset_id)
    if not asset:
        raise HTTPException(404, "خروجی پیدا نشد.")
    try:
        content = json.loads(asset.content)
    except json.JSONDecodeError:
        content = asset.content
    return {
        "id": asset.id,
        "asset_type": asset.asset_type,
        "chapter": asset.chapter,
        "title": asset.title,
        "content": content,
        "status": asset.status,
    }


@router.post("/books/{book_id}/slides")
def export_slides(
    book_id: int,
    session: DBSession,
    services: ServiceSet,
    chapter: OptionalForm = None,
):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(404, "کتاب پیدا نشد.")
    try:
        context, label = services.generator.get_context(session, book_id, chapter)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    path = services.slides.build(f"{book.title} — {label}", label, context)
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=path.name,
    )

