from typing import Optional

from groq import Groq

from app.core.config import settings


class LLMClientError(Exception):
    """Raised when the LLM provider cannot generate a response."""


class GroqClient:
    DEFAULT_MODEL = "openai/gpt-oss-20b"

    def __init__(self):
        self.client: Optional[Groq] = None

        if settings.groq_api_key:
            self.client = Groq(
                api_key=settings.groq_api_key,
            )

    def chat(
        self,
        message: str,
        model: str = DEFAULT_MODEL,
    ) -> str:

        if not message or not message.strip():
            raise LLMClientError(
                "LLM request message cannot be empty."
            )

        if settings.llm_mode.lower() == "mock":
            return self._mock_response(message)

        if settings.llm_mode.lower() != "groq":
            raise LLMClientError(
                f"Unsupported LLM mode: {settings.llm_mode}"
            )

        if not self.client:
            raise LLMClientError(
                "Groq client is not configured."
            )

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": message,
                    }
                ],
                temperature=0.1,
            )

            content = response.choices[0].message.content

            if not content or not content.strip():
                raise LLMClientError(
                    "Groq returned an empty response."
                )

            return content.strip()

        except LLMClientError:
            raise

        except Exception as exc:
            raise LLMClientError(
                f"LLM generation failed: {exc}"
            ) from exc

    def _mock_response(self, message: str) -> str:
        return (
            "[MOCK LLM RESPONSE]\n\n"
            "This is a development-mode response. "
            "The RAG pipeline successfully generated "
            "a grounded prompt and reached the LLM layer."
        )


groq_client = GroqClient()