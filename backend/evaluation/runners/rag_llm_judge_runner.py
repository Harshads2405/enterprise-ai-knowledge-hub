import json
import time
from pathlib import Path

from evaluation.evaluators.llm_judge import LLMJudge, LLMJudgeError


BASE_DIR = Path(__file__).resolve().parents[2]

DATASET_PATH = (
    BASE_DIR
    / "evaluation"
    / "datasets"
    / "rag_evaluation.json"
)

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
    / "llm_judge_baseline.json"
)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_dataset():
    return load_json(DATASET_PATH)


def load_baseline():
    return load_json(BASELINE_PATH)


def evaluate():
    dataset_cases = load_dataset()
    baseline_cases = load_baseline()

    expected_answers = {
        case["id"]: case["expected_answer"]
        for case in dataset_cases
    }

    judge = LLMJudge()

    results = []

    total = len(baseline_cases)

    for index, case in enumerate(baseline_cases, start=1):
        case_id = case["id"]

        print(f"[{index}/{total}] {case_id}")

        expected_answer = expected_answers.get(case_id, "")
        generated_answer = case.get("answer", "")
        should_clarify = case.get("should_clarify", False)

        result = {
            "id": case_id,
            "question": case["question"],
            "expected_answer": expected_answer,
            "generated_answer": generated_answer,
            "should_clarify": should_clarify,
            "answer_correctness": None,
            "answer_relevance": None,
            "reason": "",
            "error": None,
            "judge_latency_ms": None,
        }

        # Ambiguous questions intentionally produce clarification
        # instead of a direct answer. Do not score an empty answer
        # as incorrect.
        if should_clarify:
            result["reason"] = (
                "Answer scoring skipped because the RAG system "
                "correctly requested clarification."
            )

            print("  clarification case - answer scoring skipped")

            results.append(result)
            continue

        try:
            started_at = time.perf_counter()

            judge_result = judge.evaluate_answer(
                question=case["question"],
                expected_answer=expected_answer,
                generated_answer=generated_answer,
            )

            result["judge_latency_ms"] = round(
                (time.perf_counter() - started_at) * 1000,
                2,
            )

            result["answer_correctness"] = (
                judge_result["answer_correctness"]
            )

            result["answer_relevance"] = (
                judge_result["answer_relevance"]
            )

            result["reason"] = judge_result["reason"]

            print(
                f"  correctness={result['answer_correctness']}/5 "
                f"relevance={result['answer_relevance']}/5"
            )

        except LLMJudgeError as exc:
            result["error"] = str(exc)

            print(f"  ERROR: {exc}")

        results.append(result)

    answer_scored = [
        result
        for result in results
        if (
            result["error"] is None
            and result["answer_correctness"] is not None
            and result["answer_relevance"] is not None
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

    correctness_scores = [
        result["answer_correctness"]
        for result in answer_scored
    ]

    relevance_scores = [
        result["answer_relevance"]
        for result in answer_scored
    ]

    judge_latencies = [
        result["judge_latency_ms"]
        for result in answer_scored
        if result["judge_latency_ms"] is not None
    ]

    summary = {
        "total_cases": total,
        "answer_scored_cases": len(answer_scored),
        "clarification_cases": len(clarification_cases),
        "failed_cases": len(failed),
        "average_answer_correctness": (
            round(
                sum(correctness_scores) / len(correctness_scores),
                4,
            )
            if correctness_scores
            else None
        ),
        "average_answer_relevance": (
            round(
                sum(relevance_scores) / len(relevance_scores),
                4,
            )
            if relevance_scores
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

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            output,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print()
    print("=" * 60)
    print("LLM JUDGE EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Total cases:                 {summary['total_cases']}")
    print(
        "Answer-scored cases:         "
        f"{summary['answer_scored_cases']}"
    )
    print(
        "Clarification cases:         "
        f"{summary['clarification_cases']}"
    )
    print(f"Failed cases:                {summary['failed_cases']}")
    print(
        "Average correctness:         "
        f"{summary['average_answer_correctness']}/5"
    )
    print(
        "Average relevance:           "
        f"{summary['average_answer_relevance']}/5"
    )
    print(
        "Average judge latency:       "
        f"{summary['average_judge_latency_ms']} ms"
    )
    print(f"Results saved to:            {OUTPUT_PATH}")


if __name__ == "__main__":
    evaluate()