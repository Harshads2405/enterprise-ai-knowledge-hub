from langchain_core.messages import AIMessage
from langgraph.graph import END, START, StateGraph

from app.services.agents.state import AgentState


def agent_node(state: AgentState) -> AgentState:
    """
    Initial agent node that processes the current question
    and appends an AI response to the message history.
    """

    question = state.get("question", "").strip()

    if not question:
        return {
            **state,
            "answer": "No question was provided.",
            "messages": [
                AIMessage(content="No question was provided.")
            ],
        }

    answer = f"Agent received: {question}"

    return {
        **state,
        "answer": answer,
        "messages": [
            AIMessage(content=answer)
        ],
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