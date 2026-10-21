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

        response, metrics = groq_client.chat_with_metrics(prompt)

        usage_metadata = None
        response_metadata = {
            "model": self.model_name,
        }

        if metrics is not None:
            response_metadata["latency_ms"] = metrics.latency_ms

            if metrics.model:
                response_metadata["model"] = metrics.model

            if (
                    metrics.prompt_tokens is not None
                    and metrics.completion_tokens is not None
            ):
                usage_metadata = {
                    "input_tokens": metrics.prompt_tokens,
                    "output_tokens": metrics.completion_tokens,
                    "total_tokens": (
                        metrics.total_tokens
                        if metrics.total_tokens is not None
                        else (
                                metrics.prompt_tokens
                                + metrics.completion_tokens
                        )
                    ),
                }

        generation = ChatGeneration(
            message=AIMessage(
                content=response,
                response_metadata=response_metadata,
                usage_metadata=usage_metadata,
            )
        )

        return ChatResult(
            generations=[generation]
        )