from langgraph.graph import END, START, StateGraph

from app.services.agents.state import AgentState


def agent_node(state: AgentState) -> AgentState:
    """
    Minimal agent node used to validate the LangGraph foundation.
    """

    question = state.get("question", "").strip()

    if not question:
        return {
            **state,
            "answer": "No question was provided.",
        }

    return {
        **state,
        "answer": f"Agent received: {question}",
    }


def build_agent_graph():
    """
    Build and compile the initial LangGraph workflow.
    """

    graph = StateGraph(AgentState)

    graph.add_node("agent", agent_node)

    graph.add_edge(START, "agent")
    graph.add_edge("agent", END)

    return graph.compile()


agent_graph = build_agent_graph()