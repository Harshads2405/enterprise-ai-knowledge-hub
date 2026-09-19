import json
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(BASE_DIR))


from app.services.rag.rag_service import rag_service


DATASET_PATH = BASE_DIR / "evaluation" / "datasets" / "rag_evaluation.json"


def load_dataset():
    with open(DATASET_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def evaluate_retrieval(case):
    question = case["question"]
    department = case.get("department")

    retrieved = rag_service.retrieve(
        query=question,
        limit=5,
        department=department,
    )

    retrieved_chunk_ids = [
        result.chunk.id
        for result in retrieved
    ]

    expected_chunk_ids = case["relevant_chunk_ids"]
    relevance_type = case.get("relevance_type", "all")

    if relevance_type == "any":
        relevant_retrieved = [
            chunk_id
            for chunk_id in retrieved_chunk_ids
            if chunk_id in expected_chunk_ids
        ]

        is_relevant = len(relevant_retrieved) > 0

    else:
        relevant_retrieved = [
            chunk_id
            for chunk_id in retrieved_chunk_ids
            if chunk_id in expected_chunk_ids
        ]

        is_relevant = set(expected_chunk_ids).issubset(
            set(retrieved_chunk_ids)
        )

    return {
        "id": case["id"],
        "question": question,
        "expected_chunk_ids": expected_chunk_ids,
        "retrieved_chunk_ids": retrieved_chunk_ids,
        "relevant_retrieved_chunk_ids": relevant_retrieved,
        "relevance_type": relevance_type,
        "is_relevant": is_relevant,
    }

def is_retrieval_successful(result, k):
    expected_chunk_ids = set(
        result["expected_chunk_ids"]
    )

    retrieved_chunk_ids = set(
        result["retrieved_chunk_ids"][:k]
    )

    relevance_type = result.get(
        "relevance_type",
        "all",
    )

    if relevance_type == "all":
        return expected_chunk_ids.issubset(
            retrieved_chunk_ids
        )

    return bool(
        expected_chunk_ids.intersection(
            retrieved_chunk_ids
        )
    )

def calculate_recall_at_k(results, k):
    if not results or k <= 0:
        return 0.0

    successful_cases = sum(
        1
        for result in results
        if is_retrieval_successful(result, k)
    )

    return successful_cases / len(results)
def calculate_mrr(results):
    if not results:
        return 0.0

    reciprocal_ranks = []

    for result in results:
        expected_chunk_ids = set(
            result["expected_chunk_ids"]
        )

        reciprocal_rank = 0.0

        for rank, chunk_id in enumerate(
            result["retrieved_chunk_ids"],
            start=1,
        ):
            if chunk_id in expected_chunk_ids:
                reciprocal_rank = 1.0 / rank
                break

        reciprocal_ranks.append(reciprocal_rank)

    return sum(reciprocal_ranks) / len(reciprocal_ranks)

def calculate_precision_at_k(results, k):
    if not results or k <= 0:
        return 0.0

    precision_scores = []

    for result in results:
        expected_chunk_ids = set(
            result["expected_chunk_ids"]
        )

        retrieved_chunk_ids = result["retrieved_chunk_ids"][:k]

        if not retrieved_chunk_ids:
            precision_scores.append(0.0)
            continue

        relevant_count = sum(
            1
            for chunk_id in retrieved_chunk_ids
            if chunk_id in expected_chunk_ids
        )

        precision = relevant_count / len(retrieved_chunk_ids)

        precision_scores.append(precision)

    return sum(precision_scores) / len(precision_scores)

import math

def calculate_ndcg_at_k(results, k):
    if not results or k <= 0:
        return 0.0

    ndcg_scores = []

    for result in results:
        expected_chunk_ids = set(
            result["expected_chunk_ids"]
        )

        retrieved_chunk_ids = result["retrieved_chunk_ids"][:k]

        dcg = 0.0

        for rank, chunk_id in enumerate(
            retrieved_chunk_ids,
            start=1,
        ):
            if chunk_id in expected_chunk_ids:
                relevance = 1.0
            else:
                relevance = 0.0

            dcg += relevance / math.log2(rank + 1)

        relevant_count = min(
            len(expected_chunk_ids),
            k,
        )

        if relevant_count == 0:
            ndcg_scores.append(0.0)
            continue

        ideal_dcg = sum(
            1.0 / math.log2(rank + 1)
            for rank in range(1, relevant_count + 1)
        )

        ndcg = dcg / ideal_dcg

        ndcg_scores.append(ndcg)

    return sum(ndcg_scores) / len(ndcg_scores)
def run_evaluation():
    dataset = load_dataset()

    results = []

    for case in dataset:
        result = evaluate_retrieval(case)
        results.append(result)

    return results


if __name__ == "__main__":
    results = run_evaluation()

    print()
    print("RAG RETRIEVAL EVALUATION")
    print("=" * 60)

    for result in results:
        print()
        print(f"ID: {result['id']}")
        print(f"Question: {result['question']}")
        print(f"Expected: {result['expected_chunk_ids']}")
        print(f"Retrieved: {result['retrieved_chunk_ids']}")
        print(
            f"Relevant Retrieved: "
            f"{result['relevant_retrieved_chunk_ids']}"
        )
        print(f"Relevant: {result['is_relevant']}")

    recall_at_1 = calculate_recall_at_k(
        results,
        k=1,
    )

    recall_at_3 = calculate_recall_at_k(
        results,
        k=3,
    )

    recall_at_5 = calculate_recall_at_k(
        results,
        k=5,
    )

    mrr = calculate_mrr(results)

    precision_at_1 = calculate_precision_at_k(
        results,
        k=1,
    )

    precision_at_3 = calculate_precision_at_k(
        results,
        k=3,
    )

    precision_at_5 = calculate_precision_at_k(
        results,
        k=5,
    )

    ndcg_at_1 = calculate_ndcg_at_k(
        results,
        k=1,
    )

    ndcg_at_3 = calculate_ndcg_at_k(
        results,
        k=3,
    )

    ndcg_at_5 = calculate_ndcg_at_k(
        results,
        k=5,
    )

    print()
    print("=" * 60)
    print("BASELINE EVALUATION SUMMARY")
    print("=" * 60)
    print("Corpus: HR + Finance + IT")
    print("Documents: 9")
    print("Benchmark: V2 - Ambiguous Retrieval")
    print(f"Evaluation Cases: {len(results)}")
    print()
    print(f"Recall@1:     {calculate_recall_at_k(results, 1):.4f}")
    print(f"Recall@3:     {calculate_recall_at_k(results, 3):.4f}")
    print(f"Recall@5:     {calculate_recall_at_k(results, 5):.4f}")
    print(f"Precision@1:  {calculate_precision_at_k(results, 1):.4f}")
    print(f"Precision@3:  {calculate_precision_at_k(results, 3):.4f}")
    print(f"Precision@5:  {calculate_precision_at_k(results, 5):.4f}")
    print(f"MRR:          {calculate_mrr(results):.4f}")
    print(f"NDCG@1:       {calculate_ndcg_at_k(results, 1):.4f}")
    print(f"NDCG@3:       {calculate_ndcg_at_k(results, 3):.4f}")
    print(f"NDCG@5:       {calculate_ndcg_at_k(results, 5):.4f}")