from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    ToolMessage,
)
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt
from langgraph.prebuilt import ToolNode

from app.services.agents.llm import AgentChatModel
from app.services.agents.state import AgentState
from app.services.agents.tools import (
    AGENT_TOOL_METADATA,
    AGENT_TOOLS,
)


def agent_node(state: AgentState) -> AgentState:
    """
    Agent decision and answer-generation node.

    The agent receives the complete message history so that it can
    either request a tool or generate a final answer from the tool result.
    """
    question = state.get("question", "").strip()
    messages = state.get("messages", [])

    # Recover the question from the previous tool call when the graph
    # reaches the agent for the second time.
    if not question and messages:
        for message in messages:
            if isinstance(message, AIMessage) and message.tool_calls:
                tool_args = message.tool_calls[0].get("args", {})
                question = str(tool_args.get("query", "")).strip()
                if question:
                    break

    if not question:
        return {
            **state,
            "answer": "No question was provided.",
            "messages": [
                AIMessage(content="No question was provided.")
            ],
        }

    model = AgentChatModel().bind_tools(AGENT_TOOLS)

    # The first agent call needs a HumanMessage.
    # On the second call, messages already contain the AI tool call
    # and ToolMessage, so we prepend the original question only for
    # model invocation.
    model_messages = messages

    if not model_messages:
        model_messages = [
            HumanMessage(content=question)
        ]
    elif not any(
        isinstance(message, HumanMessage)
        for message in model_messages
    ):
        model_messages = [
            HumanMessage(content=question),
            *model_messages,
        ]

    response = model.invoke(model_messages)

    return {
        **state,
        "messages": [response],
        "answer": response.content or state.get("answer", ""),
    }


def tool_confirmation_node(state: AgentState) -> AgentState:
    """
    Inspect the requested tool and pause execution when human
    confirmation is required.
    """
    messages = state.get("messages", [])

    if not messages:
        return state

    last_message = messages[-1]

    if not isinstance(last_message, AIMessage):
        return state

    if not last_message.tool_calls:
        return state

    tool_call = last_message.tool_calls[0]
    tool_name = tool_call["name"]

    metadata = AGENT_TOOL_METADATA.get(tool_name)

    if metadata is None:
        raise ValueError(f"Unknown agent tool: {tool_name}")

    if not metadata.requires_confirmation:
        return {
            **state,
            "confirmation_required": False,
        }

    decision = interrupt(
        {
            "type": "tool_confirmation",
            "tool_name": tool_name,
            "tool_call_id": tool_call["id"],
            "tool_args": tool_call.get("args", {}),
        }
    )

    if decision not in {"approved", "rejected"}:
        raise ValueError(
            "Confirmation decision must be 'approved' or 'rejected'."
        )

    return {
        **state,
        "confirmation_decision": decision,
        "confirmation_required": False,
        "pending_tool_name": tool_name,
        "pending_tool_call_id": tool_call["id"],
        "pending_tool_args": tool_call.get("args", {}),
    }


def tool_result_node(state: AgentState) -> AgentState:
    """
    Extract tool execution results from the message history
    and store them explicitly in agent state.
    """
    messages = state.get("messages", [])

    tool_results = [
        message.content
        for message in messages
        if isinstance(message, ToolMessage)
    ]

    return {
        **state,
        "tool_results": tool_results,
    }


def route_after_agent(state: AgentState) -> str:
    """
    Route the graph based on whether the agent requested a tool.
    """
    messages = state.get("messages", [])

    if not messages:
        return END

    last_message = messages[-1]

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "confirmation"

    return END


def route_after_confirmation(state: AgentState) -> str:
    """
    Route the graph after checking whether the requested tool requires
    human confirmation.
    """
    if state.get("confirmation_required", False):
        return END

    return "tools"


def confirmation_decision_node(state: AgentState) -> AgentState:
    """
    Process the human confirmation decision for a pending tool call.
    """
    decision = state.get("confirmation_decision")

    if decision not in {"approved", "rejected"}:
        raise ValueError(
            "Confirmation decision must be 'approved' or 'rejected'."
        )

    if decision == "rejected":
        return {
            **state,
            "confirmation_required": False,
            "answer": "The requested tool action was rejected.",
        }

    return {
        **state,
        "confirmation_required": False,
    }


def route_after_confirmation_decision(state: AgentState) -> str:
    """
    Route the graph based on the human confirmation decision.
    """
    decision = state.get("confirmation_decision")

    if decision == "approved":
        return "tools"

    if decision == "rejected":
        return END

    return END


def build_agent_graph(checkpointer=None):
    graph = StateGraph(AgentState)

    graph.add_node("agent", agent_node)
    graph.add_node("confirmation", tool_confirmation_node)

    tool_node = ToolNode(AGENT_TOOLS)
    graph.add_node("tools", tool_node)

    graph.add_node("tool_results", tool_result_node)

    graph.add_edge(START, "agent")

    graph.add_conditional_edges(
        "agent",
        route_after_agent,
        {
            "confirmation": "confirmation",
            END: END,
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

    graph.add_edge("tools", "tool_results")
    graph.add_edge("tool_results", "agent")

    return graph.compile(checkpointer=checkpointer)


agent_graph = build_agent_graph()

