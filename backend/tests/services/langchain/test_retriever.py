from app.services.langchain.retriever import EnterpriseRetriever


def test_enterprise_retriever_returns_langchain_documents():
    retriever = EnterpriseRetriever(
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