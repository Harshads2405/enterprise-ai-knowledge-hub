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
                "question": "What is the employee leave policy?",
            },
            {
                "configurable": {
                    "thread_id": "test-knowledge-search-1",
                }
            },
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
            "question": "",
        },
        {
            "configurable": {
                "thread_id": "test-empty-question-1",
            }
        },
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
    from langchain_core.tools import tool
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.graph import END, START, StateGraph
    from langgraph.prebuilt import ToolNode
    from langgraph.types import Command

    from app.services.agents.graph import (
        route_after_confirmation,
        tool_confirmation_node,
    )
    from app.services.agents.state import AgentState
    from app.services.agents.tools import (
        AGENT_TOOL_METADATA,
        AgentToolMetadata,
    )

    execution_log = []

    @tool
    def test_write_tool(value: str) -> str:
        """Test write operation used to verify human confirmation."""
        execution_log.append(value)
        return f"write completed: {value}"

    original_metadata = AGENT_TOOL_METADATA.get("test_write_tool")

    AGENT_TOOL_METADATA["test_write_tool"] = AgentToolMetadata(
        requires_confirmation=True,
    )

    tool_call = {
        "name": "test_write_tool",
        "args": {"value": "important"},
        "id": "test-call-1",
        "type": "tool_call",
    }

    def test_agent_node(state: AgentState) -> AgentState:
        return {
            **state,
            "messages": [
                AIMessage(
                    content="",
                    tool_calls=[tool_call],
                )
            ],
        }

    try:
        graph = StateGraph(AgentState)

        graph.add_node("agent", test_agent_node)
        graph.add_node("confirmation", tool_confirmation_node)
        graph.add_node(
            "tools",
            ToolNode([test_write_tool]),
        )

        graph.add_edge(START, "agent")

        graph.add_conditional_edges(
            "agent",
            lambda state: "confirmation",
            {
                "confirmation": "confirmation",
            },
        )

        graph.add_conditional_edges(
            "confirmation",
            route_after_confirmation,
            {
                "tools": "tools",
                END: END,
            },
        )

        graph.add_edge("tools", END)

        checkpointer = MemorySaver()
        compiled_graph = graph.compile(
            checkpointer=checkpointer,
        )

        config = {
            "configurable": {
                "thread_id": "confirmation-test-1",
            }
        }

        result = compiled_graph.invoke(
            {
                "question": "Perform a write operation",
                "messages": [],
            },
            config,
        )

        assert "__interrupt__" in result

        interrupt_payload = result["__interrupt__"][0].value

        assert interrupt_payload["type"] == "tool_confirmation"
        assert interrupt_payload["tool_name"] == "test_write_tool"
        assert interrupt_payload["tool_call_id"] == "test-call-1"
        assert interrupt_payload["tool_args"] == {
            "value": "important",
        }

        assert execution_log == []

        result = compiled_graph.invoke(
            Command(resume="approved"),
            config,
        )

        assert execution_log == ["important"]

    finally:
        if original_metadata is None:
            AGENT_TOOL_METADATA.pop("test_write_tool", None)
        else:
            AGENT_TOOL_METADATA["test_write_tool"] = original_metadata

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


def test_route_after_confirmation_decision_approved():
    from app.services.agents.graph import route_after_confirmation_decision

    state = {
        "confirmation_decision": "approved",
    }

    assert route_after_confirmation_decision(state) == "tools"


def test_route_after_confirmation_decision_rejected():
    from app.services.agents.graph import route_after_confirmation_decision

    state = {
        "confirmation_decision": "rejected",
    }

    assert route_after_confirmation_decision(state) == "__end__"


def test_route_after_confirmation_decision_invalid():
    from app.services.agents.graph import route_after_confirmation_decision

    assert route_after_confirmation_decision({}) == "__end__"

def test_agent_graph_memory_is_isolated_by_thread_id():
    first_thread_config = {
        "configurable": {
            "thread_id": "memory-thread-1",
        }
    }
    second_thread_config = {
        "configurable": {
            "thread_id": "memory-thread-2",
        }
    }

    first_result = agent_graph.invoke(
        {
            "question": "What is the employee leave policy?",
        },
        first_thread_config,
    )

    second_result = agent_graph.invoke(
        {
            "question": "What is the employee leave policy?",
        },
        first_thread_config,
    )

    isolated_result = agent_graph.invoke(
        {
            "question": "What is the employee leave policy?",
        },
        second_thread_config,
    )

    assert first_result["answer"]
    assert second_result["answer"]
    assert isolated_result["answer"]

    assert first_result["messages"]
    assert second_result["messages"]
    assert isolated_result["messages"]

    assert len(second_result["messages"]) > len(first_result["messages"])
    assert len(isolated_result["messages"]) == len(first_result["messages"])
