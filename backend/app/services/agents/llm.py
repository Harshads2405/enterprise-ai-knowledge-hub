from typing import Any, List, Optional, Sequence

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import BaseTool


class AgentChatModel(BaseChatModel):
    """
    Minimal chat-model adapter for the LangGraph agent layer.

    This development implementation deterministically creates a
    knowledge-base tool call for non-empty questions.
    """

    model_name: str = "agent-development-model"

    _bound_tools: Optional[List[BaseTool]] = None

    @property
    def _llm_type(self) -> str:
        return "enterprise-agent-development"

    def bind_tools(
        self,
        tools: Sequence[BaseTool],
        *,
        tool_choice: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Bind tools to the development model.

        The actual tool metadata is not sent to a remote model yet.
        The adapter uses the bound tools to construct a deterministic
        tool call during this milestone.
        """
        return self.model_copy(
            update={
                "_bound_tools": list(tools),
            }
        )

    def _generate(
            self,
            messages: List[BaseMessage],
            stop: Optional[List[str]] = None,
            run_manager: Any = None,
            **kwargs: Any,
    ) -> ChatResult:

        question = ""
        tool_result = ""

        for message in messages:
            if message.type == "human":
                question = str(message.content)

            elif isinstance(message, ToolMessage):
                tool_result = str(message.content)

        if not question.strip():
            response = AIMessage(
                content="No question was provided."
            )

        elif tool_result.strip():
            response = AIMessage(
                content=(
                    "Based on the enterprise knowledge base: "
                    f"{tool_result}"
                )
            )

        elif self._bound_tools:
            tool = self._bound_tools[0]

            response = AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": tool.name,
                        "args": {
                            "query": question,
                            "limit": 3,
                        },
                        "id": "knowledge-search-1",
                        "type": "tool_call",
                    }
                ],
            )

        else:
            response = AIMessage(
                content=(
                    "I need to search the enterprise knowledge base "
                    "before answering this question."
                )
            )

        return ChatResult(
            generations=[
                ChatGeneration(message=response)
            ]
        )