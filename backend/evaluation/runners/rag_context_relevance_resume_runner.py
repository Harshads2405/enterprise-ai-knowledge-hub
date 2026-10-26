
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
)


BASE_DIR = Path(__file__).resolve().parents[2]

BASELINE_PATH = (
    BASE_DIR
    / "evaluation"
    / "results"
    / "real_llm_rag_baseline.json"
)

REPORT_PATH = (
    BASE_DIR
    / "evaluation"
    / "results"
    / "context_relevance_consolidated.json"
)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_report(report):
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with REPORT_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False,
        )


def is_rate_limit_error(error: str) -> bool:
    message = error.lower()

    indicators = (
        "429",
        "rate limit",
        "rate_limit",
        "tokens per day",
        "tokens/day",
        "tokens per minute",
    )

    return any(indicator in message for indicator in indicators)


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


def update_summary(report):
    results = report["results"]

    scored = [
        item
        for item in results
        if (
            item.get("error") is None
            and item.get("context_relevance") is not None
        )
    ]

    clarification = [
        item for item in results
        if item.get("should_clarify", False)
    ]

    pending = [
        item for item in results
        if item.get("evaluation_status") == "pending_rate_limit"
    ]

    failed = [
        item for item in results
        if (
            item.get("error") is not None
            and item.get("evaluation_status") != "pending_rate_limit"
        )
    ]

    scores = [item["context_relevance"] for item in scored]

    latencies = [
        item["judge_latency_ms"]
        for item in scored
        if item.get("judge_latency_ms") is not None
    ]

    report["summary"] = {
        "total_cases": len(results),
        "context_relevance_scored_cases": len(scored),
        "clarification_cases": len(clarification),
        "pending_cases": len(pending),
        "failed_cases": len(failed),
        "failed_attempts_pending_retry": len(pending),
        "average_context_relevance": (
            round(sum(scores) / len(scores), 4)
            if scores
            else None
        ),
        "average_judge_latency_ms": (
            round(sum(latencies) / len(latencies), 2)
            if latencies
            else None
        ),
        "note": (
            "Partial evaluation. Pending cases have not been scored; "
            "averages include scored cases only."
            if pending or failed
            else "All eligible cases have been evaluated."
        ),
    }


def evaluate():
    baseline_cases = load_json(BASELINE_PATH)
    report = load_json(REPORT_PATH)

    results_by_id = {
        item["id"]: item
        for item in report["results"]
    }

    # Preserve existing results and add any missing baseline cases.
    for case in baseline_cases:
        case_id = case["id"]

        if case_id not in results_by_id:
            results_by_id[case_id] = {
                "id": case_id,
                "question": case["question"],
                "retrieved_chunk_ids": case.get(
                    "retrieved_chunk_ids", []
                ),
                "should_clarify": case.get("should_clarify", False),
                "context_relevance": None,
                "reason": "",
                "error": None,
                "judge_latency_ms": None,
                "evaluation_status": (
                    "clarification_skipped"
                    if case.get("should_clarify", False)
                    else "pending"
                ),
            }

    # Keep the same order as the original evaluation dataset.
    ordered_results = [
        results_by_id[case["id"]]
        for case in baseline_cases
    ]
    report["results"] = ordered_results

    pending_cases = [
        case
        for case in baseline_cases
        if (
            results_by_id[case["id"]].get("evaluation_status")
            == "pending_rate_limit"
        )
    ]

    if not pending_cases:
        print(
            "No cases marked pending_rate_limit. "
            "No judge calls will be made."
        )
        update_summary(report)
        save_report(report)
        return

    print(f"Cases pending retry: {len(pending_cases)}")

    judge = ContextRelevanceJudge()

    for index, case in enumerate(pending_cases, start=1):
        result = results_by_id[case["id"]]

        print(
            f"[{index}/{len(pending_cases)}] "
            f"{case['id']}"
        )

        try:
            retrieved_context = build_retrieved_context(case)

            if not retrieved_context:
                result["error"] = (
                    "No retrieved context was available "
                    "for context relevance evaluation."
                )
                result["evaluation_status"] = "failed"
                print("  ERROR: no retrieved context")

            else:
                started_at = time.perf_counter()

                try:
                    judge_result = judge.evaluate(
                        question=case["question"],
                        retrieved_context=retrieved_context,
                    )
                finally:
                    result["judge_latency_ms"] = round(
                        (time.perf_counter() - started_at) * 1000,
                        2,
                    )

                result["context_relevance"] = (
                    judge_result["context_relevance"]
                )
                result["reason"] = judge_result["reason"]
                result["error"] = None
                result["evaluation_status"] = "scored"

                print(
                    "  context_relevance="
                    f"{result['context_relevance']}/5"
                )

        except Exception as exc:
            error_message = str(exc)
            result["error"] = error_message

            if is_rate_limit_error(error_message):
                result["evaluation_status"] = "pending_rate_limit"

                update_summary(report)
                save_report(report)

                print(f"  RATE LIMIT: {error_message}")
                print("  Stopping to avoid further quota-consuming calls.")
                print(f"  Progress saved to: {REPORT_PATH}")
                break

            result["evaluation_status"] = "failed"
            print(f"  ERROR: {error_message}")

        # Persist every attempt so completed work is not lost.
        update_summary(report)
        save_report(report)

    update_summary(report)
    save_report(report)

    print()
    print("=" * 55)
    print("CONTEXT RELEVANCE RESUME SUMMARY")
    print("=" * 55)

    for key, value in report["summary"].items():
        print(f"{key}: {value}")

    print(f"Report saved to: {REPORT_PATH}")


if __name__ == "__main__":
    evaluate()
