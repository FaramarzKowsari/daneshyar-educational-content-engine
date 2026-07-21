from __future__ import annotations

from pathlib import Path

import fitz
from fastapi.testclient import TestClient

from app.config import Settings
from app.factory import create_app


def _pdf_bytes() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Chapter One Learning")
    page.insert_text(
        (72, 105),
        "Deep learning connects concepts, uses feedback, and transfers knowledge to new problems. "
        "Formative assessment helps students improve before the final examination.",
    )
    page2 = doc.new_page()
    page2.insert_text((72, 72), "Chapter Two Feedback")
    page2.insert_text(
        (72, 105),
        "Effective feedback describes strengths, identifies gaps, and recommends the next learning step. "
        "Students can use self assessment to monitor their progress.",
    )
    data = doc.tobytes()
    doc.close()
    return data


def test_public_upload_chat_generate_and_delete(tmp_path: Path):
    settings = Settings(
        data_dir=tmp_path,
        enable_ocr=False,
        max_upload_mb=5,
        max_pdf_pages=10,
        public_book_ttl_hours=1,
    )
    app = create_app(settings)
    with TestClient(app) as client:
        upload = client.post(
            "/api/public/books",
            data={"accepted_terms": "true", "title": "Public Test Book"},
            files={"file": ("book.pdf", _pdf_bytes(), "application/pdf")},
        )
        assert upload.status_code == 202, upload.text
        payload = upload.json()
        token = payload["access_token"]
        public_id = payload["public_id"]
        headers = {"X-Daneshyar-Token": token}

        status = client.get(f"/api/public/books/{public_id}", headers=headers)
        assert status.status_code == 200
        assert status.json()["status"] == "ready"
        assert status.json()["page_count"] == 2

        chat = client.post(
            f"/api/public/books/{public_id}/chat",
            headers=headers,
            json={"question": "What is effective feedback?"},
        )
        assert chat.status_code == 200
        assert chat.json()["citations"]

        generated = client.post(
            f"/api/public/books/{public_id}/generate/summary",
            headers=headers,
            json={"chapter": None, "count": 5},
        )
        assert generated.status_code == 200
        assert generated.json()["status"] == "draft"

        assets = client.get(f"/api/public/books/{public_id}/assets", headers=headers)
        assert assets.status_code == 200
        assert len(assets.json()) == 1

        deleted = client.delete(f"/api/public/books/{public_id}", headers=headers)
        assert deleted.status_code == 200
        assert deleted.json() == {"deleted": True}


def test_public_access_requires_token(tmp_path: Path):
    app = create_app(Settings(data_dir=tmp_path, enable_ocr=False))
    with TestClient(app) as client:
        response = client.get("/api/public/books/not-a-book")
    assert response.status_code == 401
