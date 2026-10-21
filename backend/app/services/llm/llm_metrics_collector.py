
from contextvars import ContextVar, Token
from typing import List, Optional

from app.services.llm.llm_metrics import LLMRequestMetrics


_current_metrics: ContextVar = ContextVar(
    "current_llm_request_metrics",
    default=None,
)


class LLMRequestMetricsCollector:
    """Collect LLM call metrics within one request context."""

    def __init__(self):
        self.metrics: List[LLMRequestMetrics] = []

    def __enter__(self):
        self._token: Token = _current_metrics.set(self.metrics)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        _current_metrics.reset(self._token)

    @staticmethod
    def record(metrics: LLMRequestMetrics) -> None:
        current = _current_metrics.get()
        if current is not None:
            current.append(metrics)
