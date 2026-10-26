from app.services.langchain.retriever import EnterpriseRetriever
import pytest


def test_enterprise_retriever_returns_langchain_documents():
    retriever = EnterpriseRetriever(
        organization_id=9,
        limit=3,
    )

    documents = retriever.invoke(
        "employee leave policy"
    )

    assert documents
    assert len(documents) <= 3

    for document in documents:
        assert document.page_content
        assert "document_id" in document.metadata
        assert "chunk_id" in document.metadata


@pytest.mark.parametrize("organization_id", [0, -1, True, "9"])
def test_enterprise_retriever_rejects_invalid_organization_id(organization_id):
    with pytest.raises(Exception):
        EnterpriseRetriever(organization_id=organization_id)
