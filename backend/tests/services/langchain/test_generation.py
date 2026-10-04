from app.services.langchain.generation import (
    langchain_generation_service,
)
from app.services.langchain.prompt import (
    enterprise_rag_prompt,
)


def test_langchain_generation_service_generates_response():
    response = langchain_generation_service.generate(
        "Explain RAG in one sentence."
    )

    assert response
    assert isinstance(response, str)


def test_langchain_generation_service_generates_from_prompt():
    prompt = enterprise_rag_prompt.build()

    response = langchain_generation_service.generate_from_prompt(
        prompt=prompt,
        variables={
            "question": "What is the leave policy?",
            "context": (
                "[Source 1]\n"
                "Employees must submit leave requests."
            ),
        },
    )

    assert response
    assert isinstance(response, str)
