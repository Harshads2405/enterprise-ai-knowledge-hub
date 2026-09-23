from app.services.langchain.generation import (
    langchain_generation_service,
)


def test_langchain_generation_service_generates_response():
    response = langchain_generation_service.generate(
        "Explain RAG in one sentence."
    )

    assert response
    assert isinstance(response, str)
