from langchain_core.messages import HumanMessage

from app.services.agents.llm import AgentChatModel


def test_agent_chat_model_returns_response():
    model = AgentChatModel()

    response = model.invoke(
        [
            HumanMessage(
                content="What is the employee leave policy?"
            )
        ]
    )

    assert response.content
    assert isinstance(response.content, str)


def test_agent_chat_model_handles_empty_question():
    model = AgentChatModel()

    response = model.invoke(
        [
            HumanMessage(content="")
        ]
    )

    assert response.content == "No question was provided."