import sys
from unittest.mock import MagicMock, patch

import pytest

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


def test_tool_confirmation_node_pauses_confirmation_required_tool():
    from langchain_core.messages import AIMessage

    from app.services.agents.graph import tool_confirmation_node
    from app.services.agents.tools import (
        AGENT_TOOL_METADATA,
        AgentToolMetadata,
    )

    tool_call = {
        "name": "test_write_tool",
        "args": {"value": "important"},
        "id": "test-call-1",
        "type": "tool_call",
    }

    state = {
        "question": "Perform a write operation",
        "messages": [
            AIMessage(
                content="",
                tool_calls=[tool_call],
            )
        ],
    }

    original_metadata = AGENT_TOOL_METADATA.get("test_write_tool")

    AGENT_TOOL_METADATA["test_write_tool"] = AgentToolMetadata(
        requires_confirmation=True,
    )

    try:
        result = tool_confirmation_node(state)
    finally:
        if original_metadata is None:
            AGENT_TOOL_METADATA.pop("test_write_tool", None)
        else:
            AGENT_TOOL_METADATA["test_write_tool"] = original_metadata

    assert result["confirmation_required"] is True
    assert result["pending_tool_name"] == "test_write_tool"
    assert result["pending_tool_call_id"] == "test-call-1"
    assert result["pending_tool_args"] == {
        "value": "important",
    }

def test_agent_state_supports_confirmation_decision():
    state = {
        "pending_tool_name": "create_leave_request",
        "pending_tool_call_id": "call-1",
        "pending_tool_args": {
            "days": 3,
        },
        "confirmation_required": True,
        "confirmation_decision": "approved",
    }

    assert state["confirmation_decision"] == "approved"


def test_agent_state_supports_confirmation_rejection():
    state = {
        "pending_tool_name": "create_leave_request",
        "pending_tool_call_id": "call-2",
        "pending_tool_args": {
            "days": 3,
        },
        "confirmation_required": True,
        "confirmation_decision": "rejected",
    }

    assert state["confirmation_decision"] == "rejected"


def test_confirmation_decision_approved():
    from app.services.agents.graph import confirmation_decision_node

    state = {
        "pending_tool_name": "create_leave_request",
        "pending_tool_call_id": "call-1",
        "pending_tool_args": {"days": 3},
        "confirmation_required": True,
        "confirmation_decision": "approved",
    }

    result = confirmation_decision_node(state)

    assert result["confirmation_required"] is False
    assert result["confirmation_decision"] == "approved"


def test_confirmation_decision_rejected():
    from app.services.agents.graph import confirmation_decision_node

    state = {
        "pending_tool_name": "create_leave_request",
        "pending_tool_call_id": "call-2",
        "pending_tool_args": {"days": 3},
        "confirmation_required": True,
        "confirmation_decision": "rejected",
    }

    result = confirmation_decision_node(state)

    assert result["confirmation_required"] is False
    assert result["confirmation_decision"] == "rejected"
    assert result["answer"] == (
        "The requested tool action was rejected."
    )


def test_confirmation_decision_rejects_invalid_value():
    from app.services.agents.graph import confirmation_decision_node

    state = {
        "confirmation_decision": "maybe",
    }

    with pytest.raises(
        ValueError,
        match="Confirmation decision must be 'approved' or 'rejected'",
    ):
        confirmation_decision_node(state)
