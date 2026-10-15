
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class LLMRequestMetrics:
    """Metadata collected for one LLM request."""

    model: str
    latency_ms: float
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    success: bool = True
    error_type: Optional[str] = None
