import json
import time
from pathlib import Path

from app.services.context_compression.context_compressor import (
    context_compressor,
)
from app.services.rag.rag_service import rag_service

from evaluation.evaluators.faithfulness_judge import (
    FaithfulnessJudge,
    FaithfulnessJudgeError,
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
    / "faithfulness_baseline.json"
)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_baseline():
    return load_json(BASELINE_PATH)


def build_retrieved_context(case):
    results = rag_service.retrieve(
        query=case["question"],
        limit=len(case["retrieved_chunk_ids"]),
    )

    compressed_results = context_compressor.compress(
        query=case["question"],
        results=results,
    )

    return rag_service.build_context(compressed_results)


def evaluate():
    baseline_cases = load_baseline()

    judge = FaithfulnessJudge()

    results = []

    total = len(baseline_cases)

    for index, case in enumerate(baseline_cases, start=1):
        case_id = case["id"]

        print(f"[{index}/{total}] {case_id}")

        generated_answer = case.get("answer", "")
        should_clarify = case.get("should_clarify", False)

        result = {
            "id": case_id,
            "question": case["question"],
            "generated_answer": generated_answer,
            "retrieved_chunk_ids": case.get(
                "retrieved_chunk_ids",
                [],
            ),
            "should_clarify": should_clarify,
            "faithfulness": None,
            "reason": "",
            "error": None,
            "judge_latency_ms": None,
        }

        # Ambiguous questions intentionally produce clarification
        # instead of a direct answer. Do not score them as unfaithful.
        if should_clarify:
            result["reason"] = (
                "Faithfulness scoring skipped because the RAG system "
                "correctly requested clarification."
            )

            print("  clarification case - faithfulness scoring skipped")

            results.append(result)
            continue

        try:
            retrieved_context = build_retrieved_context(case)

            if not retrieved_context:
                result["error"] = (
                    "No retrieved context was available for faithfulness evaluation."
                )

                print("  ERROR: no retrieved context")

                results.append(result)
                continue

            started_at = time.perf_counter()

            judge_result = judge.evaluate(
                question=case["question"],
                retrieved_context=retrieved_context,
                generated_answer=generated_answer,
            )

            result["judge_latency_ms"] = round(
                (time.perf_counter() - started_at) * 1000,
                2,
            )

            result["faithfulness"] = judge_result["faithfulness"]
            result["reason"] = judge_result["reason"]

            print(
                f"  faithfulness={result['faithfulness']}/5"
            )

        except FaithfulnessJudgeError as exc:
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
            and result["faithfulness"] is not None
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

    faithfulness_scores = [
        result["faithfulness"]
        for result in scored_cases
    ]

    judge_latencies = [
        result["judge_latency_ms"]
        for result in scored_cases
        if result["judge_latency_ms"] is not None
    ]

    summary = {
        "total_cases": total,
        "faithfulness_scored_cases": len(scored_cases),
        "clarification_cases": len(clarification_cases),
        "failed_cases": len(failed),
        "average_faithfulness": (
            round(
                sum(faithfulness_scores)
                / len(faithfulness_scores),
                4,
            )
            if faithfulness_scores
            else None
        ),
        "average_judge_latency_ms": (
            round(
                sum(judge_latencies)
                / len(judge_latencies),
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

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print()
    print("=" * 60)
    print("FAITHFULNESS EVALUATION SUMMARY")
    print("=" * 60)
    print(
        f"Total cases:                 "
        f"{summary['total_cases']}"
    )
    print(
        "Faithfulness-scored cases:   "
        f"{summary['faithfulness_scored_cases']}"
    )
    print(
        "Clarification cases:         "
        f"{summary['clarification_cases']}"
    )
    print(
        f"Failed cases:                "
        f"{summary['failed_cases']}"
    )
    print(
        "Average faithfulness:        "
        f"{summary['average_faithfulness']}/5"
    )
    print(
        "Average judge latency:       "
        f"{summary['average_judge_latency_ms']} ms"
    )
    print(
        f"Results saved to:            "
        f"{OUTPUT_PATH}"
    )


if __name__ == "__main__":
    evaluate()