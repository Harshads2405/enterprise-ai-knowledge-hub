from app.services.langchain.prompt import (
    enterprise_rag_prompt,
)


def test_enterprise_rag_prompt_contains_grounding_rules():
    prompt = enterprise_rag_prompt.build()

    messages = prompt.format_messages(
        question="What is the leave policy?",
        context="[Source 1]\nEmployees must submit leave requests.",
    )

    rendered = "\n".join(
        message.content
        for message in messages
    )

    assert "ONLY the information contained" in rendered
    assert "Do not invent" in rendered
    assert "[Source 1]" in rendered
    assert "What is the leave policy?" in rendered
    assert "Employees must submit leave requests." in rendered
