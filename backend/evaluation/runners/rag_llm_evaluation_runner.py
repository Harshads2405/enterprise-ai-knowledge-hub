
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
from app.services.llm.groq_client import groq_client


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

    # Prevent metrics from a previous case being reported for this one.
    groq_client.last_request_metrics = None

    try:
        response = rag_service.generate(case["question"])
        error = None

    except Exception as exc:
        response = None
        error = f"{type(exc).__name__}: {exc}"

    latency_ms = (time.perf_counter() - start) * 1000
    llm_observability = collect_llm_metrics()

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
    print(f"ID: {result['id']}")
    print(f"Question: {result['question']}")
    print(f"Expected chunks: {result['expected_chunk_ids']}")
    print(f"Retrieved chunks: {result['retrieved_chunk_ids']}")
    print(f"Should clarify: {result['should_clarify']}")
    print(f"RAG latency: {result['latency_ms']:.2f} ms")

    metrics = result["llm_observability"]
    print(f"LLM model: {metrics['model']}")
    print(f"LLM latency: {metrics['latency_ms']} ms")
    print(f"Prompt tokens: {metrics['prompt_tokens']}")
    print(f"Completion tokens: {metrics['completion_tokens']}")
    print(f"Total tokens: {metrics['total_tokens']}")

    if result["error"]:
        print(f"ERROR: {result['error']}")
    else:
        print(f"Answer: {result['answer']}")


def print_summary(results: list) -> None:
    total = len(results)
    successful = [r for r in results if r["error"] is None]
    failed = [r for r in results if r["error"] is not None]

    latencies = [r["latency_ms"] for r in successful]
    average_latency = (
        sum(latencies) / len(latencies) if latencies else 0.0
    )

    token_records = [
        r["llm_observability"]
        for r in results
        if r["llm_observability"]["total_tokens"] is not None
    ]

    total_tokens = sum(
        record["total_tokens"] for record in token_records
    )

    print()
    print("=" * 80)
    print("LLM RAG EVALUATION SUMMARY")
    print("=" * 80)
    print(f"Evaluation cases: {total}")
    print(f"Successful:       {len(successful)}")
    print(f"Failed:           {len(failed)}")
    print(f"Average RAG latency: {average_latency:.2f} ms")
    print(f"Cases with token usage: {len(token_records)}")
    print(f"Recorded token total:  {total_tokens}")

    if failed:
        print()
        print("Failed cases:")
        for result in failed:
            print(f"- {result['id']}: {result['error']}")


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
            "LLM metrics represent the latest LLM call captured per RAG "
            "case, not necessarily all LLM calls in that case. Token totals "
            "may therefore undercount multi-call RAG requests."
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
