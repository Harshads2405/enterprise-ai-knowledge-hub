from app.services.rag.rag_service import RAGService


def test_langchain_rag_end_to_end():
    service = RAGService()

    response = service.generate(
        question="What is the employee leave policy?"
    )

    assert response is not None
    assert response.answer
    assert isinstance(response.answer, str)

