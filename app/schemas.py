from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)


class Citation(BaseModel):
    chunk_id: int
    page_start: int
    page_end: int
    chapter: str
    excerpt: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    mode: str


class GenerateRequest(BaseModel):
    chapter: str | None = None
    count: int = Field(default=8, ge=3, le=30)


class AssetResponse(BaseModel):
    id: int
    asset_type: str
    chapter: str
    title: str
    content: Any
    status: str
