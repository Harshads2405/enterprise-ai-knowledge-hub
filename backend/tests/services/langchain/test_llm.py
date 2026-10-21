
from unittest.mock import patch

from langchain_core.messages import HumanMessage

from app.services.langchain.llm import EnterpriseChatModel
from app.services.llm.llm_metrics import LLMRequestMetrics


def test_enterprise_chat_model_generates_response():
    metrics = LLMRequestMetrics(
        model="openai/gpt-oss-20b",
        latency_ms=12.5,
        success=True,
    )

    with patch(
        "app.services.langchain.llm.groq_client.chat_with_metrics",
        return_value=(
            "RAG retrieves relevant information for an LLM.",
            metrics,
        ),
    ):
        llm = EnterpriseChatModel()
        response = llm.invoke(
            [HumanMessage(content="Explain what RAG is.")]
        )

    assert response.content == (
        "RAG retrieves relevant information for an LLM."
    )
    assert isinstance(response.content, str)
    assert response.response_metadata["latency_ms"] == 12.5


def test_enterprise_chat_model_forwards_usage_and_latency():
    metrics = LLMRequestMetrics(
        model="openai/gpt-oss-20b",
        latency_ms=123.45,
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
        success=True,
    )

    with patch(
        "app.services.langchain.llm.groq_client.chat_with_metrics",
        return_value=(
            "RAG is retrieval-augmented generation.",
            metrics,
        ),
    ):
        llm = EnterpriseChatModel()
        response = llm.invoke(
            [HumanMessage(content="Explain what RAG is.")]
        )

    assert response.content == (
        "RAG is retrieval-augmented generation."
    )
    assert response.usage_metadata == {
        "input_tokens": 10,
        "output_tokens": 20,
        "total_tokens": 30,
    }
    assert response.response_metadata["model"] == (
        "openai/gpt-oss-20b"
    )
    assert response.response_metadata["latency_ms"] == 123.45
