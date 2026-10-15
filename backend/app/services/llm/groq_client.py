import time
from typing import Optional

from app.services.llm.llm_metrics import LLMRequestMetrics

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

        self.last_request_metrics: Optional[LLMRequestMetrics] = None


    def chat(
        self,
        message: str,
        model: str = DEFAULT_MODEL,
    ) -> str:
        self.last_request_metrics = None

        if not message or not message.strip():
            raise LLMClientError(
                "LLM request message cannot be empty."
            )

        if settings.llm_mode.lower() == "mock":
            started_at = time.perf_counter()
            response = self._mock_response(message)

            self.last_request_metrics = LLMRequestMetrics(
                model="mock",
                latency_ms=round(
                    (time.perf_counter() - started_at) * 1000,
                    2,
                ),
                success=True,
            )
            return response

        if settings.llm_mode.lower() != "groq":
            raise LLMClientError(
                f"Unsupported LLM mode: {settings.llm_mode}"
            )

        if not self.client:
            raise LLMClientError(
                "Groq client is not configured."
            )

        started_at = time.perf_counter()

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

            latency_ms = round(
                (time.perf_counter() - started_at) * 1000,
                2,
            )

            usage = getattr(response, "usage", None)

            self.last_request_metrics = LLMRequestMetrics(
                model=model,
                latency_ms=latency_ms,
                prompt_tokens=getattr(
                    usage, "prompt_tokens", None
                ),
                completion_tokens=getattr(
                    usage, "completion_tokens", None
                ),
                total_tokens=getattr(
                    usage, "total_tokens", None
                ),
                success=True,
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
            self.last_request_metrics = LLMRequestMetrics(
                model=model,
                latency_ms=round(
                    (time.perf_counter() - started_at) * 1000,
                    2,
                ),
                success=False,
                error_type=type(exc).__name__,
            )

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