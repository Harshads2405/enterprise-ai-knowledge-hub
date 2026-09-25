from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    """
    Shared state passed between LangGraph agent nodes.
    """

    messages: Annotated[list[BaseMessage], add_messages]
    question: str
    answer: str
