from typing import Any, List, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from app.services.llm.groq_client import groq_client


class EnterpriseChatModel(BaseChatModel):
    """LangChain adapter for the existing Groq client."""

    model_name: str = "openai/gpt-oss-20b"

    @property
    def _llm_type(self) -> str:
        return "enterprise-groq"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:

        prompt_parts = []

        for message in messages:
            content = message.content

            if isinstance(content, str):
                prompt_parts.append(content)
            else:
                prompt_parts.append(str(content))

        prompt = "\n\n".join(prompt_parts)

        response = groq_client.chat(prompt)

        generation = ChatGeneration(
            message=AIMessage(content=response)
        )

        return ChatResult(
            generations=[generation]
        )