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
    tool_results: list

    # Human-in-the-loop confirmation state.
    pending_tool_name: str
    pending_tool_call_id: str
    pending_tool_args: dict
    confirmation_required: bool