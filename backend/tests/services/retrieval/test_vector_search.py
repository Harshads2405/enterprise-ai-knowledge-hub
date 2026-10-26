from uuid import uuid4

from app.db.session import SessionLocal
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.organization import Organization
from app.models.user import User
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
    organization_id=9,
    uploaded_by=9,
):
    document = Document(
        organization_id=organization_id,
        uploaded_by=uploaded_by,
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


def create_organization_user(db, suffix):
    organization = Organization(
        name=f"Isolation Organization {suffix}",
        slug=f"isolation-organization-{suffix}",
    )
    db.add(organization)
    db.commit()
    db.refresh(organization)

    user = User(
        organization_id=organization.id,
        email=f"isolation-{suffix}@example.test",
        full_name="Isolation Test User",
        password_hash="not-used-by-this-test",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return organization, user


def test_searches_do_not_return_chunks_from_another_organization():
    db = SessionLocal()
    suffix = uuid4().hex
    chunk_ids = []
    document_ids = []
    user_ids = []
    organization_ids = []

    try:
        organization_a, user_a = create_organization_user(db, f"a-{suffix}")
        organization_b, user_b = create_organization_user(db, f"b-{suffix}")
        organization_ids.extend([organization_a.id, organization_b.id])
        user_ids.extend([user_a.id, user_b.id])
        document_a, chunk_a = create_document_with_chunk(
            db, "Organization A Policy", "isolation expense policy", "Finance",
            "policy", "1.0", "internal", organization_a.id, user_a.id,
        )
        document_b, chunk_b = create_document_with_chunk(
            db, "Organization B Policy", "isolation expense policy", "Finance",
            "policy", "1.0", "internal", organization_b.id, user_b.id,
        )
        document_ids.extend([document_a.id, document_b.id])
        chunk_ids.extend([chunk_a.id, chunk_b.id])

        query = "isolation expense policy"
        query_embedding = embedding_service.embed_query(query)

        vector_results = vector_search.search(
            query_embedding, organization_id=organization_a.id, limit=10,
        )
        keyword_results = vector_search.keyword_search(
            query, organization_id=organization_a.id, limit=10,
        )
        hybrid_results = vector_search.hybrid_search(
            query_embedding, query, organization_id=organization_a.id, limit=10,
        )

        for results in (vector_results, keyword_results, hybrid_results):
            result_ids = [result.chunk.id for result in results]
            assert chunk_a.id in result_ids
            assert chunk_b.id not in result_ids
            assert all(
                result.chunk.document.organization_id == organization_a.id
                for result in results
            )

    finally:
        try:
            if chunk_ids:
                db.query(DocumentChunk).filter(
                    DocumentChunk.id.in_(chunk_ids)
                ).delete(synchronize_session=False)
            if document_ids:
                db.query(Document).filter(
                    Document.id.in_(document_ids)
                ).delete(synchronize_session=False)
            db.flush()
            if user_ids:
                db.query(User).filter(User.id.in_(user_ids)).delete(
                    synchronize_session=False
                )
            db.flush()
            if organization_ids:
                db.query(Organization).filter(
                    Organization.id.in_(organization_ids)
                ).delete(synchronize_session=False)
            db.commit()
        finally:
            db.close()


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
            organization_id=9,
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
            organization_id=9,
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
            organization_id=9,
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
