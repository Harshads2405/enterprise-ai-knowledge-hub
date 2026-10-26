
import json
import time
from pathlib import Path

from app.services.context_compression.context_compressor import (
    context_compressor,
)
from app.services.rag.rag_service import rag_service
from app.core.config import get_evaluation_organization_id

from evaluation.evaluators.context_relevance_judge import (
    ContextRelevanceJudge,
    ContextRelevanceJudgeError,
)


BASE_DIR = Path(__file__).resolve().parents[2]

BASELINE_PATH = (
    BASE_DIR
    / "evaluation"
    / "results"
    / "real_llm_rag_baseline.json"
)

OUTPUT_PATH = (
    BASE_DIR
    / "evaluation"
    / "results"
    / "context_relevance_baseline.json"
)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_baseline():
    return load_json(BASELINE_PATH)


def build_retrieved_context(case):
    results = rag_service.retrieve(
        query=case["question"],
        organization_id=get_evaluation_organization_id(),
        limit=len(case.get("retrieved_chunk_ids", [])),
    )

    compressed_results = context_compressor.compress(
        query=case["question"],
        results=results,
    )

    return rag_service.build_context(compressed_results)


def evaluate():
    baseline_cases = load_baseline()
    judge = ContextRelevanceJudge()
    results = []

    total = len(baseline_cases)

    for index, case in enumerate(baseline_cases, start=1):
        case_id = case["id"]
        should_clarify = case.get("should_clarify", False)

        print(f"[{index}/{total}] {case_id}")

        result = {
            "id": case_id,
            "question": case["question"],
            "retrieved_chunk_ids": case.get(
                "retrieved_chunk_ids",
                [],
            ),
            "should_clarify": should_clarify,
            "context_relevance": None,
            "reason": "",
            "error": None,
            "judge_latency_ms": None,
        }

        if should_clarify:
            result["reason"] = (
                "Context relevance scoring skipped because the "
                "RAG system requested clarification."
            )

            print("  clarification case - scoring skipped")
            results.append(result)
            continue

        try:
            retrieved_context = build_retrieved_context(case)

            if not retrieved_context:
                result["error"] = (
                    "No retrieved context was available "
                    "for context relevance evaluation."
                )

                print("  ERROR: no retrieved context")
                results.append(result)
                continue

            started_at = time.perf_counter()

            judge_result = judge.evaluate(
                question=case["question"],
                retrieved_context=retrieved_context,
            )

            result["judge_latency_ms"] = round(
                (time.perf_counter() - started_at) * 1000,
                2,
            )

            result["context_relevance"] = (
                judge_result["context_relevance"]
            )
            result["reason"] = judge_result["reason"]

            print(
                f"  context_relevance="
                f"{result['context_relevance']}/5"
            )

        except ContextRelevanceJudgeError as exc:
            result["error"] = str(exc)
            print(f"  ERROR: {exc}")

        except Exception as exc:
            result["error"] = str(exc)
            print(f"  ERROR: {exc}")

        results.append(result)

    scored_cases = [
        result
        for result in results
        if (
            result["error"] is None
            and result["context_relevance"] is not None
        )
    ]

    failed = [
        result
        for result in results
        if result["error"] is not None
    ]

    clarification_cases = [
        result
        for result in results
        if result["should_clarify"]
    ]

    scores = [
        result["context_relevance"]
        for result in scored_cases
    ]

    judge_latencies = [
        result["judge_latency_ms"]
        for result in scored_cases
        if result["judge_latency_ms"] is not None
    ]

    summary = {
        "total_cases": total,
        "context_relevance_scored_cases": len(scored_cases),
        "clarification_cases": len(clarification_cases),
        "failed_cases": len(failed),
        "average_context_relevance": (
            round(sum(scores) / len(scores), 4)
            if scores
            else None
        ),
        "average_judge_latency_ms": (
            round(
                sum(judge_latencies) / len(judge_latencies),
                2,
            )
            if judge_latencies
            else None
        ),
    }

    output = {
        "summary": summary,
        "results": results,
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            output,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print()
    print("=" * 60)
    print("CONTEXT RELEVANCE EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Total cases:                  {summary['total_cases']}")
    print(
        "Context relevance scored:     "
        f"{summary['context_relevance_scored_cases']}"
    )
    print(
        f"Clarification cases:          "
        f"{summary['clarification_cases']}"
    )
    print(f"Failed cases:                  {summary['failed_cases']}")
    print(
        "Average context relevance:    "
        f"{summary['average_context_relevance']}/5"
    )
    print(
        "Average judge latency:        "
        f"{summary['average_judge_latency_ms']} ms"
    )
    print(f"Results saved to:              {OUTPUT_PATH}")


if __name__ == "__main__":
    evaluate()
