from langchain_core.messages import AIMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from app.services.agents.state import AgentState
from app.services.agents.tools import search_knowledge_base


def agent_node(state: AgentState) -> AgentState:
    """
    Initial agent node.

    For this milestone, the node deterministically creates a tool call
    for the knowledge-base search.
    """

    question = state.get("question", "").strip()

    if not question:
        return {
            **state,
            "answer": "No question was provided.",
            "messages": [
                AIMessage(
                    content="No question was provided."
                )
            ],
        }

    tool_call = {
        "name": search_knowledge_base.name,
        "args": {
            "query": question,
            "limit": 3,
        },
        "id": "knowledge-search-1",
        "type": "tool_call",
    }

    return {
        **state,
        "messages": [
            AIMessage(
                content="",
                tool_calls=[tool_call],
            )
        ],
    }


def build_agent_graph():
    """
    Build and compile the LangGraph workflow.
    """

    graph = StateGraph(AgentState)

    graph.add_node("agent", agent_node)

    tool_node = ToolNode(
        [search_knowledge_base]
    )

    graph.add_node("tools", tool_node)

    graph.add_edge(START, "agent")
    graph.add_edge("agent", "tools")
    graph.add_edge("tools", END)

    return graph.compile()


agent_graph = build_agent_graph()