from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    ToolMessage,
)
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from app.services.agents.llm import AgentChatModel
from app.services.agents.state import AgentState
from app.services.agents.tools import search_knowledge_base

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

    model = AgentChatModel().bind_tools(
        [search_knowledge_base]
    )

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
        return "tools"

    return END

def build_agent_graph():
    graph = StateGraph(AgentState)

    graph.add_node("agent", agent_node)

    tool_node = ToolNode(
        [search_knowledge_base]
    )

    graph.add_node("tools", tool_node)
    graph.add_node("tool_results", tool_result_node)

    graph.add_edge(START, "agent")
    graph.add_conditional_edges(
        "agent",
        route_after_agent,
        {
            "tools": "tools",
            END: END,
        },
    )

    graph.add_edge("tools", "tool_results")
    graph.add_edge("tool_results", "agent")

    return graph.compile()


agent_graph = build_agent_graph()