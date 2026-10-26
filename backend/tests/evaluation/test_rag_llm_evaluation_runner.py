from app.services.llm.llm_metrics import LLMRequestMetrics
from app.services.llm.llm_metrics_collector import (
    LLMRequestMetricsCollector,
)
from types import SimpleNamespace
from unittest.mock import patch

from evaluation.runners.rag_llm_evaluation_runner import evaluate_case

def test_collector_records_multiple_llm_calls():
    with LLMRequestMetricsCollector() as collector:
        LLMRequestMetricsCollector.record(
            LLMRequestMetrics(
                model="openai/gpt-oss-20b",
                latency_ms=100.0,
                prompt_tokens=10,
                completion_tokens=20,
                total_tokens=30,
                success=True,
            )
        )
        LLMRequestMetricsCollector.record(
            LLMRequestMetrics(
                model="openai/gpt-oss-20b",
                latency_ms=150.0,
                prompt_tokens=15,
                completion_tokens=25,
                total_tokens=40,
                success=True,
            )
        )

    assert len(collector.metrics) == 2
    assert sum(item.latency_ms for item in collector.metrics) == 250.0
    assert sum(item.prompt_tokens for item in collector.metrics) == 25
    assert sum(item.completion_tokens for item in collector.metrics) == 45
    assert sum(item.total_tokens for item in collector.metrics) == 70


def test_collector_does_not_record_outside_active_context():
    LLMRequestMetricsCollector.record(
        LLMRequestMetrics(
            model="mock",
            latency_ms=1.0,
            success=True,
        )
    )

    with LLMRequestMetricsCollector() as collector:
        assert collector.metrics == []


def summarize_llm_metrics(metrics_list: list) -> dict:
    """Summarize every LLM call recorded for one RAG request."""
    total_tokens_values = [
        item.total_tokens
        for item in metrics_list
        if item.total_tokens is not None
    ]
    prompt_tokens_values = [
        item.prompt_tokens
        for item in metrics_list
        if item.prompt_tokens is not None
    ]
    completion_tokens_values = [
        item.completion_tokens
        for item in metrics_list
        if item.completion_tokens is not None
    ]

    return {
        "call_count": len(metrics_list),
        "total_latency_ms": round(
            sum(item.latency_ms for item in metrics_list), 2
        ),
        "prompt_tokens": (
            sum(prompt_tokens_values)
            if prompt_tokens_values else None
        ),
        "completion_tokens": (
            sum(completion_tokens_values)
            if completion_tokens_values else None
        ),
        "total_tokens": (
            sum(total_tokens_values)
            if total_tokens_values else None
        ),
        "failed_calls": sum(
            1 for item in metrics_list if not item.success
        ),
        "calls": [
            {
                "model": item.model,
                "latency_ms": item.latency_ms,
                "prompt_tokens": item.prompt_tokens,
                "completion_tokens": item.completion_tokens,
                "total_tokens": item.total_tokens,
                "success": item.success,
                "error_type": item.error_type,
            }
            for item in metrics_list
        ],
    }


def test_evaluate_case_aggregates_multiple_llm_calls():
    case = {
        "id": "test-001",
        "question": "What is the leave policy?",
        "relevant_chunk_ids": ["chunk-1"],
    }

    def fake_generate(question, organization_id):
        assert organization_id == 7
        LLMRequestMetricsCollector.record(
            LLMRequestMetrics(
                model="openai/gpt-oss-20b",
                latency_ms=100.0,
                prompt_tokens=10,
                completion_tokens=20,
                total_tokens=30,
                success=True,
            )
        )
        LLMRequestMetricsCollector.record(
            LLMRequestMetrics(
                model="openai/gpt-oss-20b",
                latency_ms=150.0,
                prompt_tokens=15,
                completion_tokens=25,
                total_tokens=40,
                success=True,
            )
        )

        return SimpleNamespace(
            answer="Employees receive annual leave.",
            sources=[],
            should_clarify=False,
        )

    with patch(
        "evaluation.runners.rag_llm_evaluation_runner.rag_service.generate",
        side_effect=fake_generate,
    ), patch(
        "evaluation.runners.rag_llm_evaluation_runner.get_evaluation_organization_id",
        return_value=7,
    ):
        result = evaluate_case(case)

    metrics = result["llm_observability"]

    assert result["error"] is None
    assert metrics["call_count"] == 2
    assert metrics["total_latency_ms"] == 250.0
    assert metrics["prompt_tokens"] == 25
    assert metrics["completion_tokens"] == 45
    assert metrics["total_tokens"] == 70
    assert metrics["failed_calls"] == 0
