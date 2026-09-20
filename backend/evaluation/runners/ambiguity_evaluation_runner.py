import json
from pathlib import Path
from typing import Dict, List

from app.services.ambiguity.ambiguity_analysis_service import (
    ambiguity_analysis_service,
)
from app.services.ambiguity.ambiguity_detector import (
    ambiguity_detector,
)
from app.services.retrieval.retrieval_pipeline import (
    retrieval_pipeline,
)


BASE_DIR = Path(__file__).resolve().parents[2]

DATASET_PATH = (
    BASE_DIR
    / "evaluation"
    / "datasets"
    / "rag_evaluation.json"
)


# Ground-truth labels used ONLY for evaluation metrics.
#
# These labels must never be used to influence the ambiguity
# decision itself.
EXPECTED_AMBIGUOUS_CASES = {
    "ambiguous_003",
    "ambiguous_004",
}


def load_dataset() -> List[Dict]:
    with open(
        DATASET_PATH,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def evaluate_case(case: Dict) -> Dict:
    query = case["question"]
    department = case.get("department")

    # ---------------------------------------------------------
    # 1. Retrieve evidence
    # ---------------------------------------------------------

    results = retrieval_pipeline.retrieve(
        search_queries=[query],
        limit=10,
        department=department,
    )

    # ---------------------------------------------------------
    # 2. Determine whether the query explicitly identifies
    #    a knowledge-base topic.
    #
    # IMPORTANT:
    # This comes from the actual query.
    #
    # It does NOT use the expected evaluation label.
    # ---------------------------------------------------------

    explicit_topic = ambiguity_detector.has_explicit_topic(
        query
    )

    # ---------------------------------------------------------
    # 3. Analyze ambiguity
    #
    # The ambiguity analyzer receives:
    # - retrieval evidence
    # - query-derived explicit topic signal
    # - original query
    #
    # It does NOT receive the expected answer.
    # ---------------------------------------------------------

    analysis = ambiguity_analysis_service.analyze(
        results,
        explicit_topic=explicit_topic,
        query=query,
    )

    # ---------------------------------------------------------
    # 4. Ground-truth label
    #
    # This is used ONLY after prediction has been generated,
    # for calculating evaluation metrics.
    # ---------------------------------------------------------

    expected_ambiguous = (
        case["id"] in EXPECTED_AMBIGUOUS_CASES
    )

    predicted_ambiguous = analysis.is_ambiguous

    return {
        "id": case["id"],
        "question": query,
        "department": department,

        # Evaluation ground truth
        "expected_ambiguous": expected_ambiguous,

        # Model/system prediction
        "predicted_ambiguous": predicted_ambiguous,

        # Useful diagnostic information
        "explicit_topic": explicit_topic,

        "result": (
            "PASS"
            if expected_ambiguous == predicted_ambiguous
            else "FAIL"
        ),

        "strong_candidate_count": (
            analysis.strong_candidate_count
        ),

        "distinct_document_count": (
            analysis.distinct_document_count
        ),

        "top_score": analysis.top_score,

        "second_score": analysis.second_score,

        "score_gap": analysis.score_gap,

        "reason": analysis.reason,
    }


def calculate_metrics(
    results: List[Dict],
) -> Dict:

    true_positive = 0
    false_positive = 0
    true_negative = 0
    false_negative = 0

    for result in results:

        expected = result["expected_ambiguous"]
        predicted = result["predicted_ambiguous"]

        if expected and predicted:
            true_positive += 1

        elif not expected and predicted:
            false_positive += 1

        elif not expected and not predicted:
            true_negative += 1

        elif expected and not predicted:
            false_negative += 1

    precision = (
        true_positive
        / (true_positive + false_positive)
        if (true_positive + false_positive)
        else 0.0
    )

    recall = (
        true_positive
        / (true_positive + false_negative)
        if (true_positive + false_negative)
        else 0.0
    )

    f1 = (
        2 * precision * recall
        / (precision + recall)
        if (precision + recall)
        else 0.0
    )

    return {
        "true_positive": true_positive,
        "false_positive": false_positive,
        "true_negative": true_negative,
        "false_negative": false_negative,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def main():
    dataset = load_dataset()

    results = []

    print("=" * 80)
    print("AMBIGUITY EVALUATION")
    print("=" * 80)

    for case in dataset:

        result = evaluate_case(case)

        results.append(result)

        expected = (
            "AMBIGUOUS"
            if result["expected_ambiguous"]
            else "CLEAR"
        )

        predicted = (
            "AMBIGUOUS"
            if result["predicted_ambiguous"]
            else "CLEAR"
        )

        print(
            f"{result['id']:<22}"
            f"{expected:<12}"
            f"{predicted:<12}"
            f"{result['result']}"
        )

    metrics = calculate_metrics(results)

    print()
    print("=" * 80)
    print("METRICS")
    print("=" * 80)

    print(
        f"True Positives  : "
        f"{metrics['true_positive']}"
    )

    print(
        f"False Positives : "
        f"{metrics['false_positive']}"
    )

    print(
        f"True Negatives  : "
        f"{metrics['true_negative']}"
    )

    print(
        f"False Negatives : "
        f"{metrics['false_negative']}"
    )

    print()

    print(
        f"Ambiguity Precision : "
        f"{metrics['precision'] * 100:.2f}%"
    )

    print(
        f"Ambiguity Recall    : "
        f"{metrics['recall'] * 100:.2f}%"
    )

    print(
        f"Ambiguity F1        : "
        f"{metrics['f1'] * 100:.2f}%"
    )

    print()

    # ---------------------------------------------------------
    # Failures
    # ---------------------------------------------------------

    failures = [
        result
        for result in results
        if result["result"] == "FAIL"
    ]

    if failures:

        print("=" * 80)
        print("FAILURES")
        print("=" * 80)

        for failure in failures:

            print()

            print(
                f"ID       : "
                f"{failure['id']}"
            )

            print(
                f"Question : "
                f"{failure['question']}"
            )

            print(
                f"Expected : "
                f"{'AMBIGUOUS' if failure['expected_ambiguous'] else 'CLEAR'}"
            )

            print(
                f"Predicted: "
                f"{'AMBIGUOUS' if failure['predicted_ambiguous'] else 'CLEAR'}"
            )

            print(
                f"Explicit : "
                f"{failure['explicit_topic']}"
            )

            print(
                f"Top score: "
                f"{failure['top_score']}"
            )

            print(
                f"2nd score: "
                f"{failure['second_score']}"
            )

            print(
                f"Score gap: "
                f"{failure['score_gap']}"
            )

            print(
                f"Reason   : "
                f"{failure['reason']}"
            )

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()