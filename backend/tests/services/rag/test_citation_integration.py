
from unittest.mock import patch

from app.services.rag.rag_service import rag_service
from app.services.llm.llm_metrics import LLMRequestMetrics


def test_invalid_llm_citation_triggers_safe_fallback(monkeypatch):
    def fake_chat_with_metrics(prompt: str, model=None):
        return (
            "The IT security team investigates reported security incidents. "
            "[Source 99]",
            LLMRequestMetrics(
                model="openai/gpt-oss-20b",
                latency_ms=10.0,
                success=True,
            ),
        )

    with patch(
        "app.services.langchain.llm.groq_client.chat_with_metrics",
        side_effect=fake_chat_with_metrics,
    ):
        result = rag_service.generate(
            "Who investigates reported security incidents?",
            organization_id=9,
            limit=3,
        )

    assert result.answer == (
        "I couldn't safely verify the source citations for this answer. "
        "Please try the question again."
    )

    assert result.should_clarify is False
    assert len(result.sources) == 3
