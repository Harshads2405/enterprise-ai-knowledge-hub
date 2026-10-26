
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import app.api.documents as documents
from app.core.security import get_current_user
from app.db.session import get_db
from app.main import app


@pytest.mark.parametrize(
    ("error", "expected_status"),
    [
        (RuntimeError("internal database details"), 500),
        (
            HTTPException(status_code=503, detail="Ingestion unavailable."),
            503,
        ),
    ],
)
def test_upload_cleans_file_when_ingestion_fails(
    tmp_path,
    monkeypatch,
    error,
    expected_status,
):
    current_user = SimpleNamespace(id=9, organization_id=3)
    db = MagicMock()

    def override_get_db():
        yield db

    def fake_document(**kwargs):
        return SimpleNamespace(id=123, **kwargs)

    def fail_ingestion(**kwargs):
        raise error

    monkeypatch.setattr(documents, "STORAGE_DIR", tmp_path)
    monkeypatch.setattr(documents, "Document", fake_document)
    monkeypatch.setattr(
        documents.ingestion_service,
        "ingest",
        fail_ingestion,
    )
    monkeypatch.setitem(app.dependency_overrides, get_db, override_get_db)
    monkeypatch.setitem(
        app.dependency_overrides,
        get_current_user,
        lambda: current_user,
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("report.txt", b"sample document", "text/plain")},
        )

    assert response.status_code == expected_status
    assert list(tmp_path.iterdir()) == []

    if expected_status == 500:
        assert response.json()["detail"] == "Document ingestion failed."
