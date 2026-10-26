
from app.core.config import settings
from app.services.rag.rag_service import RAGService


def test_langchain_rag_end_to_end(monkeypatch):
    monkeypatch.setattr(settings, "llm_mode", "mock")

    service = RAGService()

    response = service.generate(
        question="What is the employee leave policy?",
        organization_id=9,
    )

    assert response is not None
    assert response.answer
    assert isinstance(response.answer, str)
