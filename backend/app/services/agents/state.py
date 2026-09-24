from typing import TypedDict


class AgentState(TypedDict, total=False):
    """
    Shared state passed between LangGraph agent nodes.
    """

    question: str
    answer: str