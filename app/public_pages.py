from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse

router = APIRouter(include_in_schema=False)


@router.get("/")
def public_home(request: Request):
    return FileResponse(request.app.state.settings.public_dir / "index.html")


@router.get("/author.html")
def author_page(request: Request):
    return FileResponse(request.app.state.settings.public_dir / "author.html")
