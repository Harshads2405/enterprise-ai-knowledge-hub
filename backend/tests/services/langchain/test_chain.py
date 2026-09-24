from app.services.langchain.chain import build_rag_chain


def test_build_rag_chain():
    chain = build_rag_chain(limit=3)

    assert chain is not None


def test_rag_chain_invocation():
    chain = build_rag_chain(limit=3)

    result = chain.invoke(
        {
            "input": "What is the employee leave policy?",
        }
    )

    assert result["input"] == "What is the employee leave policy?"
    assert result["answer"]
    assert isinstance(result["answer"], str)

    assert result["context"]
    assert len(result["context"]) <= 3

    for document in result["context"]:
        assert document.page_content
        assert "document_id" in document.metadata
        assert "chunk_id" in document.metadata
