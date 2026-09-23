from app.db.session import SessionLocal
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.embeddings.embedding_service import embedding_service
from app.services.retrieval.vector_search import vector_search


def create_document_with_chunk(
    db,
    title,
    content,
    department,
    document_type,
    version,
    access_level,
):
    document = Document(
        organization_id=9,
        uploaded_by=9,
        title=title,
        source_type="test",
        source_name=f"{title}.txt",
        status="completed",
        document_metadata={
            "department": department,
            "document_type": document_type,
            "version": version,
            "access_level": access_level,
        },
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    embedding = embedding_service.embed_document(content)

    chunk = DocumentChunk(
        document_id=document.id,
        chunk_index=0,
        content=content,
        token_count=len(content.split()),
        chunk_metadata={
            "department": department,
            "document_type": document_type,
            "version": version,
            "access_level": access_level,
        },
        embedding=embedding,
    )

    db.add(chunk)
    db.commit()
    db.refresh(chunk)

    return document, chunk


def test_vector_search_filters_by_all_metadata_fields():
    db = SessionLocal()

    try:
        create_document_with_chunk(
            db=db,
            title="HR Leave Policy",
            content="Employees must submit leave requests through HR.",
            department="HR",
            document_type="policy",
            version="1.0",
            access_level="internal",
        )

        create_document_with_chunk(
            db=db,
            title="Engineering Leave Policy",
            content="Employees must submit leave requests through Engineering.",
            department="Engineering",
            document_type="policy",
            version="1.0",
            access_level="internal",
        )

        query_embedding = embedding_service.embed_query(
            "employee leave request policy"
        )

        results = vector_search.search(
            query_embedding=query_embedding,
            limit=10,
            department="HR",
            document_type="policy",
            version="1.0",
            access_level="internal",
        )

        assert results

        for result in results:
            metadata = result.chunk.chunk_metadata

            assert metadata["department"] == "HR"
            assert metadata["document_type"] == "policy"
            assert metadata["version"] == "1.0"
            assert metadata["access_level"] == "internal"

        for result in results:
            metadata = result.chunk.chunk_metadata

            assert metadata["department"] == "HR"
            assert metadata["document_type"] == "policy"
            assert metadata["version"] == "1.0"
            assert metadata["access_level"] == "internal"

    finally:
        db.close()


def test_keyword_search_filters_by_metadata():
    db = SessionLocal()

    try:
        matching_document, matching_chunk = create_document_with_chunk(
            db=db,
            title="Finance Policy",
            content="Finance employees must follow the expense policy.",
            department="Finance",
            document_type="policy",
            version="2.0",
            access_level="confidential",
        )

        create_document_with_chunk(
            db=db,
            title="HR Policy",
            content="HR employees must follow the expense policy.",
            department="HR",
            document_type="policy",
            version="2.0",
            access_level="confidential",
        )

        results = vector_search.keyword_search(
            query="expense policy",
            limit=10,
            department="Finance",
            document_type="policy",
            version="2.0",
            access_level="confidential",
        )

        result_ids = [result.chunk.id for result in results]

        assert matching_chunk.id in result_ids

        for result in results:
            metadata = result.chunk.chunk_metadata

            assert metadata["department"] == "Finance"
            assert metadata["document_type"] == "policy"
            assert metadata["version"] == "2.0"
            assert metadata["access_level"] == "confidential"

    finally:
        db.close()


def test_hybrid_search_filters_by_metadata():
    db = SessionLocal()

    try:
        matching_document, matching_chunk = create_document_with_chunk(
            db=db,
            title="Restricted Security Policy",
            content="Security access requires administrator approval.",
            department="Security",
            document_type="policy",
            version="3.0",
            access_level="restricted",
        )

        create_document_with_chunk(
            db=db,
            title="Public Security Policy",
            content="Security access information is publicly available.",
            department="Security",
            document_type="policy",
            version="3.0",
            access_level="public",
        )

        query = "security access administrator approval"

        query_embedding = embedding_service.embed_query(query)

        results = vector_search.hybrid_search(
            query_embedding=query_embedding,
            query=query,
            limit=10,
            department="Security",
            document_type="policy",
            version="3.0",
            access_level="restricted",
        )

        result_ids = [result.chunk.id for result in results]

        assert matching_chunk.id in result_ids

        for result in results:
            metadata = result.chunk.chunk_metadata

            assert metadata["department"] == "Security"
            assert metadata["document_type"] == "policy"
            assert metadata["version"] == "3.0"
            assert metadata["access_level"] == "restricted"

    finally:
        db.close()