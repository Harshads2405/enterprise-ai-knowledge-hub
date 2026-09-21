from app.services.rag.rag_service import rag_service


def test_invalid_llm_citation_triggers_safe_fallback(monkeypatch):
    def fake_chat(prompt: str) -> str:
        return (
            "The IT security team investigates reported security incidents. "
            "[Source 99]"
        )

    monkeypatch.setattr(
        "app.services.rag.rag_service.groq_client.chat",
        fake_chat,
    )

    result = rag_service.generate(
        "Who investigates reported security incidents?",
        limit=3,
    )

    assert result.answer == (
        "I couldn't safely verify the source citations for this answer. "
        "Please try the question again."
    )

    assert result.should_clarify is False
    assert len(result.sources) == 3