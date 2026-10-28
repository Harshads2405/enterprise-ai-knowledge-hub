
import time
from typing import Optional, Tuple

from groq import Groq

from app.core.config import settings
from app.services.llm.llm_metrics import LLMRequestMetrics
from app.services.llm.llm_metrics_collector import (
    LLMRequestMetricsCollector,
)

class LLMClientError(Exception):
    """Raised when the LLM provider cannot generate a response."""


class GroqClient:
    DEFAULT_MODEL = "openai/gpt-oss-20b"

    def __init__(self):
        self.client: Optional[Groq] = None

        if settings.groq_api_key:
            self.client = Groq(api_key=settings.groq_api_key)

        # Kept for compatibility with existing callers.
        self.last_request_metrics: Optional[LLMRequestMetrics] = None

    def chat(self, message: str, model: str = DEFAULT_MODEL) -> str:
        """Generate a response while preserving the existing interface."""
        self.last_request_metrics = None
        response, metrics = self._chat_with_metrics(message, model)
        self.last_request_metrics = metrics
        LLMRequestMetricsCollector.record(metrics)
        return response

    def chat_with_metrics(
            self,
            message: str,
            model: str = DEFAULT_MODEL,
    ) -> Tuple[str, LLMRequestMetrics]:
        """Generate a response and return metrics for this specific call."""
        self.last_request_metrics = None
        response, metrics = self._chat_with_metrics(message, model)
        self.last_request_metrics = metrics
        LLMRequestMetricsCollector.record(metrics)
        return response, metrics


    def _chat_with_metrics(
        self,
        message: str,
        model: str,
    ) -> Tuple[str, LLMRequestMetrics]:
        """Generate a response and record metrics for each provider call."""
        if not message or not message.strip():
            raise LLMClientError("LLM request message cannot be empty.")

        if settings.llm_mode.lower() == "mock":
            started_at = time.perf_counter()
            response = self._mock_response(message)

            metrics = LLMRequestMetrics(
                model="mock",
                latency_ms=round(
                    (time.perf_counter() - started_at) * 1000, 2
                ),
                success=True,
            )
            return response, metrics

        if settings.llm_mode.lower() != "groq":
            raise LLMClientError(
                "Unsupported LLM mode: {}".format(settings.llm_mode)
            )

        if not self.client:
            raise LLMClientError("Groq client is not configured.")

        started_at = time.perf_counter()

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": message}],
                temperature=0.1,
            )

            usage = getattr(response, "usage", None)
            content = (
                response.choices[0].message.content
                if response.choices
                else None
            )

            if not content or not content.strip():
                metrics = LLMRequestMetrics(
                    model=model,
                    latency_ms=round(
                        (time.perf_counter() - started_at) * 1000, 2
                    ),
                    prompt_tokens=getattr(usage, "prompt_tokens", None),
                    completion_tokens=getattr(
                        usage, "completion_tokens", None
                    ),
                    total_tokens=getattr(usage, "total_tokens", None),
                    success=False,
                    error_type="EmptyResponse",
                )
                self.last_request_metrics = metrics
                LLMRequestMetricsCollector.record(metrics)
                raise LLMClientError("Groq returned an empty response.")

            metrics = LLMRequestMetrics(
                model=model,
                latency_ms=round(
                    (time.perf_counter() - started_at) * 1000, 2
                ),
                prompt_tokens=getattr(usage, "prompt_tokens", None),
                completion_tokens=getattr(
                    usage, "completion_tokens", None
                ),
                total_tokens=getattr(usage, "total_tokens", None),
                success=True,
            )

            return content.strip(), metrics

        except LLMClientError:
            raise

        except Exception as exc:
            metrics = LLMRequestMetrics(
                model=model,
                latency_ms=round(
                    (time.perf_counter() - started_at) * 1000, 2
                ),
                success=False,
                error_type=type(exc).__name__,
            )
            self.last_request_metrics = metrics
            LLMRequestMetricsCollector.record(metrics)

            raise LLMClientError(
                "LLM generation failed: {}".format(exc)
            ) from exc


    def _mock_response(self, message: str) -> str:
        return (
            "[MOCK LLM RESPONSE]\n\n"
            "This is a development-mode response. "
            "The RAG pipeline successfully generated "
            "a grounded prompt and reached the LLM layer."
        )


groq_client = GroqClient()
