from types import SimpleNamespace

import pytest

from app.services.ingestion.ingestion_service import IngestionService


class FakeSession:
    def __init__(self, document):
        self.document = document
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def get(self, model, document_id):
        if self.document is not None and self.document.id == document_id:
            return self.document
        return None

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def make_document(document_id=42):
    return SimpleNamespace(
        id=document_id,
        status="pending",
        document_metadata={
            "department": "HR",
            "document_type": "policy",
            "version": "1.0",
            "access_level": "internal",
        },
    )


def test_ingest_success_updates_document_status(monkeypatch):
    document = make_document()
    fake_session = FakeSession(document)

    monkeypatch.setattr(
        "app.services.ingestion.ingestion_service.SessionLocal",
        lambda: fake_session,
    )

    monkeypatch.setattr(
        "app.services.ingestion.ingestion_service.document_loader.load",
        lambda file_path: "Employee leave policy content.",
    )

    monkeypatch.setattr(
        "app.services.ingestion.ingestion_service.text_chunker.split",
        lambda text: [
            "Employee leave policy chunk 1.",
            "Employee leave policy chunk 2.",
        ],
    )

    indexed_chunks = [
        SimpleNamespace(id=1),
        SimpleNamespace(id=2),
    ]

    captured = {}

    def fake_index_chunks(
        document_id,
        chunks,
        document_metadata,
    ):
        captured["document_id"] = document_id
        captured["chunks"] = chunks
        captured["metadata"] = document_metadata
        return indexed_chunks

    monkeypatch.setattr(
        "app.services.ingestion.ingestion_service.document_indexer.index_chunks",
        fake_index_chunks,
    )

    service = IngestionService()

    result = service.ingest(
        document_id=42,
        file_path="policy.pdf",
    )

    assert result == indexed_chunks
    assert document.status == "completed"
    assert fake_session.committed is True
    assert fake_session.rolled_back is False
    assert fake_session.closed is True

    assert captured["document_id"] == 42
    assert captured["chunks"] == [
        "Employee leave policy chunk 1.",
        "Employee leave policy chunk 2.",
    ]
    assert captured["metadata"] == document.document_metadata


def test_ingest_missing_document_raises_error(monkeypatch):
    fake_session = FakeSession(document=None)

    monkeypatch.setattr(
        "app.services.ingestion.ingestion_service.SessionLocal",
        lambda: fake_session,
    )

    service = IngestionService()

    with pytest.raises(
        ValueError,
        match="Document not found: 999",
    ):
        service.ingest(
            document_id=999,
            file_path="missing.pdf",
        )

    assert fake_session.closed is True


def test_ingest_empty_document_marks_failed(monkeypatch):
    document = make_document()
    fake_session = FakeSession(document)

    monkeypatch.setattr(
        "app.services.ingestion.ingestion_service.SessionLocal",
        lambda: fake_session,
    )

    monkeypatch.setattr(
        "app.services.ingestion.ingestion_service.document_loader.load",
        lambda file_path: "   ",
    )

    service = IngestionService()

    with pytest.raises(
        ValueError,
        match="Document contains no extractable text",
    ):
        service.ingest(
            document_id=42,
            file_path="empty.pdf",
        )

    assert document.status == "failed"
    assert fake_session.rolled_back is True
    assert fake_session.closed is True


def test_ingest_no_chunks_marks_failed(monkeypatch):
    document = make_document()
    fake_session = FakeSession(document)

    monkeypatch.setattr(
        "app.services.ingestion.ingestion_service.SessionLocal",
        lambda: fake_session,
    )

    monkeypatch.setattr(
        "app.services.ingestion.ingestion_service.document_loader.load",
        lambda file_path: "Some document text.",
    )

    monkeypatch.setattr(
        "app.services.ingestion.ingestion_service.text_chunker.split",
        lambda text: [],
    )

    service = IngestionService()

    with pytest.raises(
        ValueError,
        match="Document produced no chunks",
    ):
        service.ingest(
            document_id=42,
            file_path="policy.pdf",
        )

    assert document.status == "failed"
    assert fake_session.rolled_back is True
    assert fake_session.closed is True


def test_ingest_indexing_failure_marks_failed(monkeypatch):
    document = make_document()
    fake_session = FakeSession(document)

    monkeypatch.setattr(
        "app.services.ingestion.ingestion_service.SessionLocal",
        lambda: fake_session,
    )

    monkeypatch.setattr(
        "app.services.ingestion.ingestion_service.document_loader.load",
        lambda file_path: "Some document text.",
    )

    monkeypatch.setattr(
        "app.services.ingestion.ingestion_service.text_chunker.split",
        lambda text: ["Some document chunk."],
    )

    def failing_indexer(**kwargs):
        raise RuntimeError("Indexing failed")

    monkeypatch.setattr(
        "app.services.ingestion.ingestion_service.document_indexer.index_chunks",
        failing_indexer,
    )

    service = IngestionService()

    with pytest.raises(
        RuntimeError,
        match="Indexing failed",
    ):
        service.ingest(
            document_id=42,
            file_path="policy.pdf",
        )

    assert document.status == "failed"
    assert fake_session.rolled_back is True
    assert fake_session.closed is True