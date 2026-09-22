from fastapi.testclient import TestClient

from app.main import app
from app.services.rag.rag_service import rag_service
from app.schemas.rag.citation import Citation
from app.schemas.rag.response import RAGResponse


client = TestClient(app)


def test_rag_query_api_returns_page_in_citation(monkeypatch):
    def fake_generate(question, limit=None, department=None):
        return RAGResponse(
            answer="The security team investigates reported incidents.",
            sources=[
                Citation(
                    document_id=1,
                    chunk_id=10,
                    chunk_index=0,
                    source_name="security-policy.pdf",
                    page=4,
                    retrieval_score=0.95,
                    reranker_score=0.91,
                )
            ],
        )

    monkeypatch.setattr(
        rag_service,
        "generate",
        fake_generate,
    )

    response = client.post(
        "/api/v1/rag/query",
        json={
            "question": "Who investigates reported security incidents?",
            "limit": 3,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["answer"] == (
        "The security team investigates reported incidents."
    )

    assert len(data["sources"]) == 1

    citation = data["sources"][0]

    assert citation["document_id"] == 1
    assert citation["chunk_id"] == 10
    assert citation["chunk_index"] == 0
    assert citation["source_name"] == "security-policy.pdf"
    assert citation["page"] == 4
    assert citation["retrieval_score"] == 0.95
    assert citation["reranker_score"] == 0.91