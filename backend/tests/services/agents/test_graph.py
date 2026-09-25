from langchain_core.messages import AIMessage, HumanMessage

from app.services.agents.graph import agent_graph


def test_agent_graph_builds():
    assert agent_graph is not None


def test_agent_graph_processes_question():
    result = agent_graph.invoke(
        {
            "question": "What is the employee leave policy?"
        }
    )

    assert result["question"] == "What is the employee leave policy?"
    assert result["answer"]
    assert result["answer"] == (
        "Agent received: What is the employee leave policy?"
    )

    assert result["messages"]
    assert len(result["messages"]) == 1
    assert isinstance(result["messages"][0], AIMessage)
    assert result["messages"][0].content == result["answer"]


def test_agent_graph_preserves_existing_messages():
    result = agent_graph.invoke(
        {
            "question": "What is the employee leave policy?",
            "messages": [
                HumanMessage(
                    content="Hello, I need information about company policies."
                )
            ],
        }
    )

    assert len(result["messages"]) == 2

    assert isinstance(result["messages"][0], HumanMessage)
    assert (
        result["messages"][0].content
        == "Hello, I need information about company policies."
    )

    assert isinstance(result["messages"][1], AIMessage)
    assert (
        result["messages"][1].content
        == "Agent received: What is the employee leave policy?"
    )


def test_agent_graph_handles_empty_question():
    result = agent_graph.invoke(
        {
            "question": ""
        }
    )

    assert result["answer"] == "No question was provided."
    assert result["messages"]
    assert isinstance(result["messages"][0], AIMessage)
    assert result["messages"][0].content == "No question was provided."
