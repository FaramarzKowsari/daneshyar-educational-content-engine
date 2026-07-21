from __future__ import annotations

import hashlib
import json
import secrets
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    Header,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.responses import FileResponse
from sqlalchemy import distinct, select
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_services
from app.models import Asset, Book, ChatLog, Chunk, PublicAccess
from app.schemas import ChatRequest, Citation, GenerateRequest
from app.service_container import Services
from app.services.pdf_ingestion import PDFIngestionError
from app.services.text_utils import slugify

router = APIRouter(prefix="/api/public", tags=["public-beta"])
DBSession = Annotated[Session, Depends(get_db)]
ServiceSet = Annotated[Services, Depends(get_services)]
PDFUpload = Annotated[UploadFile, File(...)]
OptionalForm = Annotated[str | None, Form()]
TermsForm = Annotated[bool, Form()]


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _client_ip(request: Request) -> str:
    if request.app.state.settings.trust_proxy_headers:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",", 1)[0].strip()
    return request.client.host if request.client else "unknown"


def _limit(request: Request, category: str, maximum: int, subject: str | None = None) -> None:
    key = f"{category}:{subject or _client_ip(request)}"
    if not request.app.state.rate_limiter.allow(key, maximum):
        raise HTTPException(
            429,
            "سقف استفادهٔ آزمایشی شما در این بازه تکمیل شده است. کمی بعد دوباره تلاش کنید.",
        )


def _authorized_access(
    session: Session,
    public_id: str,
    token: str | None,
) -> tuple[PublicAccess, Book]:
    if not token:
        raise HTTPException(401, "کلید دسترسی این کتاب در مرورگر پیدا نشد.")
    access = session.scalar(select(PublicAccess).where(PublicAccess.public_id == public_id))
    if not access or not secrets.compare_digest(access.token_hash, _hash_token(token)):
        raise HTTPException(403, "دسترسی به این کتاب معتبر نیست.")
    if access.expires_at <= datetime.utcnow():
        raise HTTPException(410, "زمان نگه‌داری این کتاب پایان یافته است.")
    book = session.get(Book, access.book_id)
    if not book:
        raise HTTPException(404, "کتاب پیدا نشد.")
    return access, book


def _asset_dict(asset: Asset) -> dict:
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
        "created_at": asset.created_at.isoformat() if asset.created_at else None,
    }


def process_public_book(app, book_id: int, title: str | None, author: str | None) -> None:
    with app.state.database.session_factory() as session:
        book = session.get(Book, book_id)
        if not book:
            return
        try:
            app.state.services.book.ingest_existing(session, book, title=title, author=author)
        except (PDFIngestionError, ValueError) as exc:
            session.rollback()
            book = session.get(Book, book_id)
            if book:
                book.status = "failed"
                book.processing_error = str(exc)[:2000]
                session.commit()
        except Exception:
            session.rollback()
            book = session.get(Book, book_id)
            if book:
                book.status = "failed"
                book.processing_error = "پردازش کتاب با خطای غیرمنتظره متوقف شد."
                session.commit()


@router.get("/config")
def public_config(request: Request) -> dict:
    settings = request.app.state.settings
    return {
        "max_upload_mb": settings.max_upload_mb,
        "max_pdf_pages": settings.max_pdf_pages,
        "ttl_hours": settings.public_book_ttl_hours,
        "ocr_enabled": settings.enable_ocr,
        "llm_enabled": request.app.state.services.llm.enabled,
        "embeddings_enabled": request.app.state.services.embeddings.enabled,
    }


@router.post("/books", status_code=202)
async def create_public_book(
    request: Request,
    background_tasks: BackgroundTasks,
    session: DBSession,
    file: PDFUpload,
    title: OptionalForm = None,
    author: OptionalForm = None,
    accepted_terms: TermsForm = False,
):
    settings = request.app.state.settings
    _limit(request, "upload", settings.public_uploads_per_hour)
    if not accepted_terms:
        raise HTTPException(400, "پذیرش شرایط استفاده و حقوق نشر الزامی است.")

    filename = file.filename or "book.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(400, "فقط فایل PDF پذیرفته می‌شود.")
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(400, "نوع فایل معتبر نیست.")

    content = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"حداکثر حجم فایل {settings.max_upload_mb} مگابایت است.")
    if not content.startswith(b"%PDF"):
        raise HTTPException(400, "امضای فایل PDF معتبر نیست.")

    token = secrets.token_urlsafe(32)
    public_id = uuid.uuid4().hex
    safe_name = slugify(Path(filename).stem) + ".pdf"
    stored = settings.upload_dir / f"{public_id}-{safe_name}"
    stored.write_bytes(content)

    book = Book(
        title=(title or Path(filename).stem).strip()[:300],
        author=author.strip()[:200] if author and author.strip() else None,
        filename=filename[:300],
        stored_path=str(stored),
        page_count=0,
        status="processing",
    )
    session.add(book)
    session.flush()
    expires_at = datetime.utcnow() + timedelta(hours=settings.public_book_ttl_hours)
    session.add(
        PublicAccess(
            book_id=book.id,
            public_id=public_id,
            token_hash=_hash_token(token),
            expires_at=expires_at,
        )
    )
    session.commit()

    background_tasks.add_task(process_public_book, request.app, book.id, title, author)
    return {
        "public_id": public_id,
        "access_token": token,
        "status": "processing",
        "title": book.title,
        "expires_at": expires_at.isoformat() + "Z",
    }


@router.get("/books/{public_id}")
def public_book_status(
    public_id: str,
    session: DBSession,
    x_daneshyar_token: str | None = Header(default=None),
):
    access, book = _authorized_access(session, public_id, x_daneshyar_token)
    chapters: list[str] = []
    if book.status == "ready":
        chapters = list(
            session.scalars(
                select(distinct(Chunk.chapter))
                .where(Chunk.book_id == book.id)
                .order_by(Chunk.chapter)
            )
        )
    return {
        "public_id": access.public_id,
        "title": book.title,
        "author": book.author,
        "filename": book.filename,
        "page_count": book.page_count,
        "status": book.status,
        "processing_error": book.processing_error,
        "chapters": chapters,
        "expires_at": access.expires_at.isoformat() + "Z",
    }


@router.post("/books/{public_id}/chat")
def public_chat(
    request: Request,
    public_id: str,
    payload: ChatRequest,
    session: DBSession,
    services: ServiceSet,
    x_daneshyar_token: str | None = Header(default=None),
):
    _, book = _authorized_access(session, public_id, x_daneshyar_token)
    if book.status != "ready":
        raise HTTPException(409, "کتاب هنوز آمادهٔ پرسش‌وپاسخ نیست.")
    _limit(request, "chat", request.app.state.settings.public_chat_per_hour, public_id)

    hits = services.retrieval.search(session, book.id, payload.question)
    if not hits:
        return {"answer": "در کتاب محتوای مرتبط کافی پیدا نشد.", "citations": [], "mode": "local-fallback"}

    context_parts: list[str] = []
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
    session.add(
        ChatLog(
            book_id=book.id,
            question=payload.question,
            answer=result.text,
            citations_json=json.dumps([c.model_dump() for c in citations], ensure_ascii=False),
        )
    )
    session.commit()
    return {"answer": result.text, "citations": [c.model_dump() for c in citations], "mode": result.mode}


@router.post("/books/{public_id}/generate/{asset_type}")
def public_generate(
    request: Request,
    public_id: str,
    asset_type: str,
    payload: GenerateRequest,
    session: DBSession,
    services: ServiceSet,
    x_daneshyar_token: str | None = Header(default=None),
):
    _, book = _authorized_access(session, public_id, x_daneshyar_token)
    if book.status != "ready":
        raise HTTPException(409, "کتاب هنوز آمادهٔ تولید محتوا نیست.")
    _limit(
        request,
        "generate",
        request.app.state.settings.public_generations_per_hour,
        public_id,
    )
    try:
        if asset_type == "summary":
            generated = services.generator.summary(session, book.id, payload.chapter)
        elif asset_type == "quiz":
            generated = services.generator.quiz(session, book.id, payload.chapter, payload.count)
        elif asset_type == "flashcards":
            generated = services.generator.flashcards(session, book.id, payload.chapter, payload.count)
        elif asset_type == "mindmap":
            generated = services.generator.mindmap(session, book.id, payload.chapter)
        else:
            raise HTTPException(400, "نوع خروجی پشتیبانی نمی‌شود.")
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    asset = services.generator.save(session, book.id, generated)
    return _asset_dict(asset)


@router.get("/books/{public_id}/assets")
def public_assets(
    public_id: str,
    session: DBSession,
    x_daneshyar_token: str | None = Header(default=None),
):
    _, book = _authorized_access(session, public_id, x_daneshyar_token)
    assets = list(
        session.scalars(select(Asset).where(Asset.book_id == book.id).order_by(Asset.created_at.desc()))
    )
    return [_asset_dict(asset) for asset in assets]


@router.get("/books/{public_id}/assets/{asset_id}")
def public_asset(
    public_id: str,
    asset_id: int,
    session: DBSession,
    x_daneshyar_token: str | None = Header(default=None),
):
    _, book = _authorized_access(session, public_id, x_daneshyar_token)
    asset = session.get(Asset, asset_id)
    if not asset or asset.book_id != book.id:
        raise HTTPException(404, "خروجی پیدا نشد.")
    return _asset_dict(asset)


@router.post("/books/{public_id}/assets/{asset_id}/approve")
def public_approve_asset(
    public_id: str,
    asset_id: int,
    session: DBSession,
    x_daneshyar_token: str | None = Header(default=None),
):
    _, book = _authorized_access(session, public_id, x_daneshyar_token)
    asset = session.get(Asset, asset_id)
    if not asset or asset.book_id != book.id:
        raise HTTPException(404, "خروجی پیدا نشد.")
    asset.status = "approved"
    session.commit()
    return _asset_dict(asset)


@router.post("/books/{public_id}/slides")
def public_slides(
    public_id: str,
    session: DBSession,
    services: ServiceSet,
    chapter: OptionalForm = None,
    x_daneshyar_token: str | None = Header(default=None),
):
    _, book = _authorized_access(session, public_id, x_daneshyar_token)
    if book.status != "ready":
        raise HTTPException(409, "کتاب هنوز آماده نیست.")
    try:
        context, label = services.generator.get_context(session, book.id, chapter)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    path = services.slides.build(f"{book.title} — {label}", label, context)
    asset = Asset(
        book_id=book.id,
        asset_type="slides",
        chapter=label,
        title=f"اسلایدهای {label}",
        content=json.dumps(
            {"filename": path.name, "note": "فایل PowerPoint تولید و دانلود شد."},
            ensure_ascii=False,
        ),
        status="draft",
    )
    session.add(asset)
    session.commit()
    session.refresh(asset)
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=path.name,
        headers={"X-Daneshyar-Asset-Id": str(asset.id)},
    )


@router.delete("/books/{public_id}")
def delete_public_book(
    public_id: str,
    session: DBSession,
    x_daneshyar_token: str | None = Header(default=None),
):
    _, book = _authorized_access(session, public_id, x_daneshyar_token)
    path = Path(book.stored_path)
    session.delete(book)
    session.commit()
    path.unlink(missing_ok=True)
    return {"deleted": True}
