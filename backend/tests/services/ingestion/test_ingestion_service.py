from types import SimpleNamespace

import pytest

from pathlib import Path

from app.db.session import SessionLocal
from app.models.document import Document
from app.services.ingestion.document_unit import DocumentUnit
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
        "app.services.ingestion.ingestion_service.document_loader.load_with_metadata",
        lambda file_path: [
            DocumentUnit(
                content="Employee leave policy content.",
                metadata={"page": 3},
            )
        ],
    )

    monkeypatch.setattr(
        "app.services.ingestion.ingestion_service.text_chunker.split_units",
        lambda units: [
            DocumentUnit(
                content="Employee leave policy chunk 1.",
                metadata={"page": 3},
            ),
            DocumentUnit(
                content="Employee leave policy chunk 2.",
                metadata={"page": 3},
            ),
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
    assert len(captured["chunks"]) == 2

    assert captured["chunks"][0].content == (
        "Employee leave policy chunk 1."
    )
    assert captured["chunks"][0].metadata == {"page": 3}

    assert captured["chunks"][1].content == (
        "Employee leave policy chunk 2."
    )
    assert captured["chunks"][1].metadata == {"page": 3}

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
        "app.services.ingestion.ingestion_service.document_loader.load_with_metadata",
        lambda file_path: [],
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
        "app.services.ingestion.ingestion_service.document_loader.load_with_metadata",
        lambda file_path: [
            DocumentUnit(
                content="Some document text.",
                metadata={"page": 1},
            )
        ],
    )

    monkeypatch.setattr(
        "app.services.ingestion.ingestion_service.text_chunker.split_units",
        lambda units: [],
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
        "app.services.ingestion.ingestion_service.document_loader.load_with_metadata",
        lambda file_path: [
            DocumentUnit(
                content="Some document text.",
                metadata={"page": 1},
            )
        ],
    )

    monkeypatch.setattr(
        "app.services.ingestion.ingestion_service.text_chunker.split_units",
        lambda units: [
            DocumentUnit(
                content="Some document chunk.",
                metadata={"page": 1},
            )
        ],
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

def test_ingest_csv_uses_standard_text_pipeline(monkeypatch):
    document = make_document()
    fake_session = FakeSession(document)

    monkeypatch.setattr(
        "app.services.ingestion.ingestion_service.SessionLocal",
        lambda: fake_session,
    )

    captured = {}

    def fake_load(file_path):
        captured["file_path"] = file_path
        return (
            "Name | Department | Role\n"
            "John | IT | Developer\n"
            "Sarah | HR | Manager"
        )

    monkeypatch.setattr(
        "app.services.ingestion.ingestion_service.document_loader.load",
        fake_load,
    )

    def fake_split(text):
        captured["text"] = text
        return [
            "Name | Department | Role\n"
            "John | IT | Developer",
            "Sarah | HR | Manager",
        ]

    monkeypatch.setattr(
        "app.services.ingestion.ingestion_service.text_chunker.split",
        fake_split,
    )

    indexed_chunks = [
        SimpleNamespace(id=1),
        SimpleNamespace(id=2),
    ]

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
        file_path="employees.csv",
    )

    assert result == indexed_chunks
    assert document.status == "completed"
    assert fake_session.committed is True
    assert fake_session.rolled_back is False
    assert fake_session.closed is True

    assert captured["file_path"] == "employees.csv"

    assert captured["text"] == (
        "Name | Department | Role\n"
        "John | IT | Developer\n"
        "Sarah | HR | Manager"
    )

    assert captured["chunks"] == [
        "Name | Department | Role\n"
        "John | IT | Developer",
        "Sarah | HR | Manager",
    ]

    assert captured["document_id"] == 42
    assert captured["metadata"] == document.document_metadata

def test_ingest_html_uses_standard_text_pipeline(monkeypatch):
    document = make_document()
    fake_session = FakeSession(document)

    monkeypatch.setattr(
        "app.services.ingestion.ingestion_service.SessionLocal",
        lambda: fake_session,
    )

    captured = {}

    def fake_load(file_path):
        captured["file_path"] = file_path
        return (
            "Employee Leave Policy\n"
            "Employees must submit leave requests."
        )

    monkeypatch.setattr(
        "app.services.ingestion.ingestion_service.document_loader.load",
        fake_load,
    )

    def fake_split(text):
        captured["text"] = text
        return [
            "Employee Leave Policy",
            "Employees must submit leave requests.",
        ]

    monkeypatch.setattr(
        "app.services.ingestion.ingestion_service.text_chunker.split",
        fake_split,
    )

    indexed_chunks = [
        SimpleNamespace(id=1),
        SimpleNamespace(id=2),
    ]

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
        file_path="policy.html",
    )

    assert result == indexed_chunks
    assert document.status == "completed"
    assert fake_session.committed is True
    assert fake_session.rolled_back is False
    assert fake_session.closed is True

    assert captured["file_path"] == "policy.html"

    assert captured["text"] == (
        "Employee Leave Policy\n"
        "Employees must submit leave requests."
    )

    assert captured["chunks"] == [
        "Employee Leave Policy",
        "Employees must submit leave requests.",
    ]

    assert captured["document_id"] == 42
    assert captured["metadata"] == document.document_metadata

def test_ingest_markdown_uses_standard_text_pipeline(tmp_path: Path):
    file_path = tmp_path / "policy.md"

    file_path.write_text(
        """
        # Employee Leave Policy

        Employees must submit leave requests.
        Leave requests require manager approval.
        """,
        encoding="utf-8",
    )

    db = SessionLocal()

    try:
        document = Document(
            organization_id=9,
            uploaded_by=9,
            title="Employee Leave Policy",
            source_type="upload",
            source_name="policy.md",
            status="uploaded",
            document_metadata={
                "department": "HR",
                "document_type": "policy",
                "version": "1.0",
                "access_level": "internal",
            },
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        document_id = document.id
    finally:
        db.close()

    service = IngestionService()

    chunks = service.ingest(
        document_id=document_id,
        file_path=str(file_path),
    )

    assert len(chunks) >= 1

    combined_content = "\n".join(chunk.content for chunk in chunks)

    assert "Employee Leave Policy" in combined_content
    assert "Employees must submit leave requests." in combined_content
    assert "# " not in combined_content

    db = SessionLocal()

    try:
        document = db.get(Document, document_id)

        assert document is not None
        assert document.status == "completed"
    finally:
        db.close()

def test_ingest_txt_uses_metadata_aware_pipeline(tmp_path: Path):
    file_path = tmp_path / "policy.txt"

    file_path.write_text(
        """
        Employee Leave Policy

        Employees must submit leave requests.
        Leave requests require manager approval.
        """,
        encoding="utf-8",
    )

    db = SessionLocal()

    try:
        document = Document(
            organization_id=9,
            uploaded_by=9,
            title="Employee Leave Policy",
            source_type="upload",
            source_name="policy.txt",
            status="uploaded",
            document_metadata={
                "department": "HR",
                "document_type": "policy",
                "version": "1.0",
                "access_level": "internal",
            },
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        document_id = document.id
    finally:
        db.close()

    service = IngestionService()

    chunks = service.ingest(
        document_id=document_id,
        file_path=str(file_path),
    )

    assert len(chunks) >= 1

    combined_content = "\n".join(
        chunk.content for chunk in chunks
    )

    assert "Employee Leave Policy" in combined_content
    assert "Employees must submit leave requests." in combined_content
    assert "# " not in combined_content

    for chunk in chunks:
        assert chunk.chunk_metadata["department"] == "HR"
        assert chunk.chunk_metadata["document_type"] == "policy"
        assert chunk.chunk_metadata["version"] == "1.0"
        assert chunk.chunk_metadata["access_level"] == "internal"

    db = SessionLocal()

    try:
        document = db.get(Document, document_id)

        assert document is not None
        assert document.status == "completed"
    finally:
        db.close()