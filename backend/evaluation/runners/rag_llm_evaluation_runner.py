
import json
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

DATASET_PATH = (
    BASE_DIR
    / "evaluation"
    / "datasets"
    / "rag_evaluation.json"
)

RESULTS_DIR = BASE_DIR / "evaluation" / "results"

# Separate output files: do not overwrite the historical baseline.
RAG_OUTPUT_PATH = RESULTS_DIR / "real_llm_rag_observability_run.json"
METRICS_OUTPUT_PATH = RESULTS_DIR / "llm_observability_baseline.json"

sys.path.insert(0, str(BASE_DIR))

from app.services.rag.rag_service import rag_service
from app.core.config import get_evaluation_organization_id
from app.services.llm.groq_client import groq_client
from app.services.llm.llm_metrics_collector import (
    LLMRequestMetricsCollector,
)


def summarize_llm_metrics(metrics_list: list) -> dict:
    """Aggregate metrics for all LLM calls in one RAG request."""
    prompt_values = [
        item.prompt_tokens for item in metrics_list
        if item.prompt_tokens is not None
    ]
    completion_values = [
        item.completion_tokens for item in metrics_list
        if item.completion_tokens is not None
    ]
    total_values = [
        item.total_tokens for item in metrics_list
        if item.total_tokens is not None
    ]

    return {
        "call_count": len(metrics_list),
        "total_latency_ms": round(
            sum(item.latency_ms for item in metrics_list), 2
        ),
        "prompt_tokens": sum(prompt_values) if prompt_values else None,
        "completion_tokens": (
            sum(completion_values) if completion_values else None
        ),
        "total_tokens": sum(total_values) if total_values else None,
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

def load_dataset():
    with open(DATASET_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def collect_llm_metrics() -> dict:
    """Collect metrics for the latest LLM call, if available."""
    metrics = groq_client.last_request_metrics

    if metrics is None:
        return {
            "model": None,
            "latency_ms": None,
            "prompt_tokens": None,
            "completion_tokens": None,
            "total_tokens": None,
            "success": None,
            "error_type": None,
        }

    return {
        "model": metrics.model,
        "latency_ms": round(metrics.latency_ms, 2),
        "prompt_tokens": metrics.prompt_tokens,
        "completion_tokens": metrics.completion_tokens,
        "total_tokens": metrics.total_tokens,
        "success": metrics.success,
        "error_type": metrics.error_type,
    }



def evaluate_case(case: dict) -> dict:
    start = time.perf_counter()

    response = None
    error = None

    # Isolate metrics for this evaluation case.
    with LLMRequestMetricsCollector() as collector:
        try:
            response = rag_service.generate(
                question=case["question"],
                organization_id=get_evaluation_organization_id(),
            )
        except Exception as exc:
            error = "{}: {}".format(type(exc).__name__, exc)

    latency_ms = (time.perf_counter() - start) * 1000
    llm_observability = summarize_llm_metrics(collector.metrics)

    sources = []

    if response is not None:
        for source in response.sources or []:
            sources.append(
                {
                    "document_id": getattr(source, "document_id", None),
                    "chunk_id": getattr(source, "chunk_id", None),
                    "rank": getattr(source, "rank", None),
                }
            )

    retrieved_chunk_ids = [
        source["chunk_id"]
        for source in sources
        if source["chunk_id"] is not None
    ]

    return {
        "id": case["id"],
        "question": case["question"],
        "expected_chunk_ids": case["relevant_chunk_ids"],
        "retrieved_chunk_ids": retrieved_chunk_ids,
        "answer": response.answer if response is not None else None,
        "sources": sources,
        "should_clarify": (
            response.should_clarify if response is not None else None
        ),
        "latency_ms": round(latency_ms, 2),
        "error": error,
        "llm_observability": llm_observability,
    }


def print_case(result: dict) -> None:
    print()
    print("-" * 80)
    print("ID: {}".format(result["id"]))
    print("Question: {}".format(result["question"]))
    print("Expected chunks: {}".format(result["expected_chunk_ids"]))
    print("Retrieved chunks: {}".format(result["retrieved_chunk_ids"]))
    print("Should clarify: {}".format(result["should_clarify"]))
    print("RAG latency: {:.2f} ms".format(result["latency_ms"]))

    metrics = result["llm_observability"]
    print("LLM calls: {}".format(metrics["call_count"]))
    print("Total LLM latency: {} ms".format(metrics["total_latency_ms"]))
    print("Prompt tokens: {}".format(metrics["prompt_tokens"]))
    print("Completion tokens: {}".format(metrics["completion_tokens"]))
    print("Total tokens: {}".format(metrics["total_tokens"]))
    print("Failed LLM calls: {}".format(metrics["failed_calls"]))

    if result["error"]:
        print("ERROR: {}".format(result["error"]))
    else:
        print("Answer: {}".format(result["answer"]))


def print_summary(results: list) -> None:
    total = len(results)
    successful = [r for r in results if r["error"] is None]
    failed = [r for r in results if r["error"] is not None]

    latencies = [r["latency_ms"] for r in successful]
    average_latency = (
        sum(latencies) / len(latencies) if latencies else 0.0
    )

    all_calls = [
        call
        for result in results
        for call in result["llm_observability"]["calls"]
    ]
    token_calls = [
        call for call in all_calls
        if call["total_tokens"] is not None
    ]

    recorded_tokens = sum(
        call["total_tokens"] for call in token_calls
    )
    failed_llm_calls = sum(
        1 for call in all_calls if not call["success"]
    )

    print()
    print("=" * 80)
    print("LLM RAG EVALUATION SUMMARY")
    print("=" * 80)
    print("Evaluation cases: {}".format(total))
    print("Successful RAG cases: {}".format(len(successful)))
    print("Failed RAG cases: {}".format(len(failed)))
    print("Average RAG latency: {:.2f} ms".format(average_latency))
    print("Total LLM calls: {}".format(len(all_calls)))
    print("Failed LLM calls: {}".format(failed_llm_calls))
    print("Calls with token usage: {}".format(len(token_calls)))
    print("Recorded token total: {}".format(recorded_tokens))

    if failed:
        print()
        print("Failed RAG cases:")
        for result in failed:
            print("- {}: {}".format(result["id"], result["error"]))


def save_json(path: Path, data) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def main() -> None:
    dataset = load_dataset()

    print("=" * 80)
    print("REAL LLM RAG EVALUATION WITH OBSERVABILITY")
    print("=" * 80)
    print(f"Dataset: {DATASET_PATH}")
    print(f"Evaluation cases: {len(dataset)}")
    print("LLM_MODE should be set to 'groq'.")
    print()
    print("WARNING: Running this evaluates every case and may consume API quota.")
    print("The two output reports are saved separately.")
    print()

    results = []

    for index, case in enumerate(dataset, start=1):
        print(f"[{index}/{len(dataset)}] Running {case['id']}...")

        result = evaluate_case(case)
        results.append(result)

        print_case(result)

    print_summary(results)

    # Preserve the established RAG report format and save observability
    # separately. Both files are written only when this runner is executed.
    save_json(RAG_OUTPUT_PATH, results)

    metrics_report = {
        "dataset": str(DATASET_PATH),
        "evaluation_cases": len(results),
        "note": (
            "LLM metrics include calls recorded within each RAG request. "
            "Token totals "
            "include only calls for which the provider returned token usage."
        ),
        "results": [
            {
                "id": result["id"],
                "question": result["question"],
                "rag_latency_ms": result["latency_ms"],
                "llm_observability": result["llm_observability"],
                "error": result["error"],
            }
            for result in results
        ],
    }

    save_json(METRICS_OUTPUT_PATH, metrics_report)

    print()
    print(f"RAG results saved to: {RAG_OUTPUT_PATH}")
    print(f"LLM metrics saved to: {METRICS_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
