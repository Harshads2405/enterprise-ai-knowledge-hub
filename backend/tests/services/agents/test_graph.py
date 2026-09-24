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


def test_agent_graph_handles_empty_question():
    result = agent_graph.invoke(
        {
            "question": ""
        }
    )

    assert result["answer"] == "No question was provided."