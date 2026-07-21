from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.factory import create_app


def test_health(tmp_path: Path):
    app = create_app(Settings(data_dir=tmp_path))
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
