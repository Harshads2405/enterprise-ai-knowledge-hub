from langchain_core.messages import AIMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from app.services.agents.llm import AgentChatModel
from app.services.agents.state import AgentState
from app.services.agents.tools import search_knowledge_base


def agent_node(state: AgentState) -> AgentState:
    """
    Agent decision node.

    The LLM decides whether the question requires a knowledge-base
    search. For this development milestone, the model is deterministic
    and produces the knowledge-base tool call.
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

    model = AgentChatModel().bind_tools(
        [search_knowledge_base]
    )

    response = model.invoke(
        [
            {
                "role": "user",
                "content": question,
            }
        ]
    )

    return {
        **state,
        "messages": [response],
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

    graph.add_edge(START, "agent")
    graph.add_conditional_edges(
        "agent",
        route_after_agent,
        {
            "tools": "tools",
            END: END,
        },
    )

    graph.add_edge("tools", END)

    return graph.compile()


agent_graph = build_agent_graph()