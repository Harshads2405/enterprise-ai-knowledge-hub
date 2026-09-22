from types import SimpleNamespace

from app.services.ingestion.indexing.document_indexer import DocumentIndexer


class FakeQuery:
    def __init__(self, document_chunks):
        self.document_chunks = document_chunks

    def filter(self, *args, **kwargs):
        return self

    def all(self):
        return self.document_chunks


class FakeSession:
    def __init__(self):
        self.added = []
        self.committed = False
        self.refreshed = []
        self.rolled_back = False
        self.closed = False

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.committed = True

    def refresh(self, obj):
        self.refreshed.append(obj)

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def test_index_chunks_creates_document_chunks(monkeypatch):
    fake_session = FakeSession()

    monkeypatch.setattr(
        "app.services.ingestion.indexing.document_indexer.SessionLocal",
        lambda: fake_session,
    )

    monkeypatch.setattr(
        "app.services.ingestion.indexing.document_indexer.embedding_service.embed_document",
        lambda content: [0.1, 0.2, 0.3],
    )

    indexer = DocumentIndexer()

    chunks = [
        "First employee policy chunk.",
        "Second employee policy chunk.",
    ]

    metadata = {
        "department": "HR",
        "document_type": "policy",
        "version": "1.0",
        "access_level": "internal",
    }

    result = indexer.index_chunks(
        document_id=42,
        chunks=chunks,
        document_metadata=metadata,
    )

    assert len(result) == 2
    assert len(fake_session.added) == 2
    assert fake_session.committed is True
    assert fake_session.closed is True

    first = fake_session.added[0]
    second = fake_session.added[1]

    assert first.document_id == 42
    assert first.chunk_index == 0
    assert first.content == chunks[0]
    assert first.token_count == len(chunks[0].split())
    assert first.embedding == [0.1, 0.2, 0.3]

    assert second.document_id == 42
    assert second.chunk_index == 1
    assert second.content == chunks[1]
    assert second.token_count == len(chunks[1].split())

    assert first.chunk_metadata == metadata
    assert second.chunk_metadata == metadata


def test_index_chunks_copies_metadata_per_chunk(monkeypatch):
    fake_session = FakeSession()

    monkeypatch.setattr(
        "app.services.ingestion.indexing.document_indexer.SessionLocal",
        lambda: fake_session,
    )

    monkeypatch.setattr(
        "app.services.ingestion.indexing.document_indexer.embedding_service.embed_document",
        lambda content: [0.1, 0.2, 0.3],
    )

    indexer = DocumentIndexer()

    metadata = {
        "department": "IT",
        "document_type": "security",
        "version": "2.0",
        "access_level": "restricted",
    }

    result = indexer.index_chunks(
        document_id=10,
        chunks=["Chunk one", "Chunk two"],
        document_metadata=metadata,
    )

    assert result[0].chunk_metadata is not result[1].chunk_metadata
    assert result[0].chunk_metadata == result[1].chunk_metadata


def test_index_chunks_rolls_back_on_embedding_failure(monkeypatch):
    fake_session = FakeSession()

    monkeypatch.setattr(
        "app.services.ingestion.indexing.document_indexer.SessionLocal",
        lambda: fake_session,
    )

    def failing_embedding(content):
        raise RuntimeError("Embedding failed")

    monkeypatch.setattr(
        "app.services.ingestion.indexing.document_indexer.embedding_service.embed_document",
        failing_embedding,
    )

    indexer = DocumentIndexer()

    try:
        indexer.index_chunks(
            document_id=42,
            chunks=["Test chunk"],
            document_metadata={},
        )
        assert False, "Expected RuntimeError"
    except RuntimeError as exc:
        assert str(exc) == "Embedding failed"

    assert fake_session.rolled_back is True
    assert fake_session.committed is False
    assert fake_session.closed is True