import sys
from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage, ToolMessage


retrieval_pipeline_module = MagicMock()
retrieval_pipeline_module.retrieval_pipeline = MagicMock()

sys.modules[
    "app.services.retrieval.retrieval_pipeline"
] = retrieval_pipeline_module

from app.services.agents.graph import agent_graph
from app.services.agents.tools import search_knowledge_base

def test_agent_graph_builds():
    assert agent_graph is not None


def test_agent_graph_executes_knowledge_base_tool():
    mock_result = [
        {
            "content": (
                "Employees receive 20 days of annual leave."
            ),
            "metadata": {
                "document_id": 1,
                "chunk_id": 10,
                "document_title": "Employee Leave Policy",
            },
        }
    ]

    with patch.object(
        search_knowledge_base,
        "func",
        return_value=mock_result,
    ) as mock_func:
        result = agent_graph.invoke(
            {
                "question": "What is the employee leave policy?"
            }
        )

    assert result["question"] == (
        "What is the employee leave policy?"
    )

    assert result["messages"]

    assert isinstance(
        result["messages"][0],
        AIMessage,
    )

    assert result["messages"][0].tool_calls

    tool_call = result["messages"][0].tool_calls[0]

    assert tool_call["name"] == "search_knowledge_base"
    assert tool_call["args"]["query"] == (
        "What is the employee leave policy?"
    )

    assert isinstance(
        result["messages"][1],
        ToolMessage,
    )

    assert result["messages"][1].name == (
        "search_knowledge_base"
    )

    assert (
        "20 days of annual leave"
        in result["messages"][1].content
    )

    assert result["answer"]
    assert "20 days of annual leave" in result["answer"]

    assert result["tool_results"]
    assert (
        "20 days of annual leave"
        in str(result["tool_results"])
    )

    mock_func.assert_called_once()

def test_agent_graph_handles_empty_question():
    result = agent_graph.invoke(
        {
            "question": ""
        }
    )

    assert result["answer"] == "No question was provided."

    assert result["messages"]

    assert isinstance(
        result["messages"][0],
        AIMessage,
    )

    assert result["messages"][0].content == (
        "No question was provided."
    )


def test_agent_state_supports_tool_confirmation():
    state = {
        "question": "Create a leave request",
        "pending_tool_name": "create_leave_request",
        "pending_tool_call_id": "call-1",
        "pending_tool_args": {
            "days": 3,
        },
        "confirmation_required": True,
    }

    assert state["pending_tool_name"] == "create_leave_request"
    assert state["pending_tool_call_id"] == "call-1"
    assert state["pending_tool_args"] == {"days": 3}
    assert state["confirmation_required"] is True
