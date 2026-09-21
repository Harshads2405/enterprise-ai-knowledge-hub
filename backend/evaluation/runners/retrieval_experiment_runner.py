import json
import math
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

from app.services.embeddings.embedding_service import embedding_service
from app.services.retrieval.vector_search import vector_search
from app.services.reranking.reranker_service import reranker_service


BASE_DIR = Path(__file__).resolve().parents[2]
DATASET_PATH = BASE_DIR / "evaluation" / "datasets" / "rag_evaluation.json"

TOP_K = 5
CANDIDATE_LIMIT = 10


def load_dataset():
    with open(DATASET_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def retrieve_vector(
    query: str,
    department: Optional[str],
    limit: int = TOP_K,
):
    query_embedding = embedding_service.embed_query(query)

    return vector_search.search(
        query_embedding=query_embedding,
        limit=limit,
        department=department,
    )


def retrieve_keyword(
    query: str,
    department: Optional[str],
    limit: int = TOP_K,
):
    return vector_search.keyword_search(
        query=query,
        limit=limit,
        department=department,
    )


def retrieve_hybrid(
    query: str,
    department: Optional[str],
    limit: int = TOP_K,
):
    query_embedding = embedding_service.embed_query(query)

    return vector_search.hybrid_search(
        query_embedding=query_embedding,
        query=query,
        limit=limit,
        department=department,
        vector_limit=CANDIDATE_LIMIT,
        keyword_limit=CANDIDATE_LIMIT,
    )


def rerank_results(
    query: str,
    results,
    limit: int = TOP_K,
):
    if not results:
        return []

    return reranker_service.rerank(
        query=query,
        results=results,
        top_k=limit,
    )

def generate_deterministic_multi_queries(query: str) -> List[str]:
    """
    Deterministic query expansion for retrieval evaluation.

    This intentionally does not call an LLM so that evaluation results
    remain reproducible across runs.
    """

    normalized = query.strip()

    if not normalized:
        return []

    queries = [normalized]

    # Requirement / submission formulation.
    if normalized.lower().startswith("what should"):
        queries.append(
            normalized.replace(
                "What should",
                "Required items employees must provide for",
                1,
            )
        )

    # Responsibility formulation.
    if normalized.lower().startswith("who is responsible for"):
        queries.append(
            normalized.replace(
                "Who is responsible for",
                "Responsibility for",
                1,
            )
        )

    # General requirement formulation.
    if "what is required" in normalized.lower():
        queries.append(
            normalized.replace(
                "What is required",
                "Required information",
                1,
            )
        )

    # Remove duplicates while preserving order.
    unique_queries = []
    seen = set()

    for item in queries:
        normalized_item = item.strip().lower()

        if not normalized_item:
            continue

        if normalized_item in seen:
            continue

        seen.add(normalized_item)
        unique_queries.append(item.strip())

    return unique_queries[:3]

def retrieve_hybrid_rerank_multi_query(
    query: str,
    department: Optional[str],
    limit: int = TOP_K,
):
    search_queries = generate_deterministic_multi_queries(query)

    if not search_queries:
        return []

    unique_results = {}

    for search_query in search_queries:
        candidates = retrieve_hybrid(
            query=search_query,
            department=department,
            limit=CANDIDATE_LIMIT,
        )

        reranked = rerank_results(
            query=search_query,
            results=candidates,
            limit=CANDIDATE_LIMIT,
        )

        for result in reranked:
            chunk_id = result.chunk.id

            if chunk_id not in unique_results:
                unique_results[chunk_id] = result
                continue

            existing = unique_results[chunk_id]

            if result.reranker_score is not None:
                if (
                    existing.reranker_score is None
                    or result.reranker_score
                    > existing.reranker_score
                ):
                    existing.reranker_score = (
                        result.reranker_score
                    )

    merged_results = list(unique_results.values())

    merged_results.sort(
        key=lambda result: (
            result.reranker_score
            if result.reranker_score is not None
            else float("-inf")
        ),
        reverse=True,
    )

    return merged_results[:limit]

def retrieve_experiment(
    experiment: str,
    query: str,
    department: Optional[str],
    limit: int = TOP_K,
):
    if experiment == "vector":
        return retrieve_vector(
            query=query,
            department=department,
            limit=limit,
        )

    if experiment == "keyword":
        return retrieve_keyword(
            query=query,
            department=department,
            limit=limit,
        )

    if experiment == "hybrid":
        return retrieve_hybrid(
            query=query,
            department=department,
            limit=limit,
        )

    if experiment == "hybrid_rerank":
        candidates = retrieve_hybrid(
            query=query,
            department=department,
            limit=CANDIDATE_LIMIT,
        )

        return rerank_results(
            query=query,
            results=candidates,
            limit=limit,
        )

    if experiment == "hybrid_rerank_multi_query":
        return retrieve_hybrid_rerank_multi_query(
            query=query,
            department=department,
            limit=limit,
        )

    raise ValueError(
        f"Unknown experiment: {experiment}"
    )


def is_relevant(
    retrieved_chunk_ids: List[int],
    expected_chunk_ids: List[int],
    relevance_type: str,
) -> bool:
    retrieved = set(retrieved_chunk_ids)
    expected = set(expected_chunk_ids)

    if relevance_type == "all":
        return expected.issubset(retrieved)

    return bool(expected.intersection(retrieved))


def calculate_recall_at_k(results, k):
    if not results:
        return 0.0

    successful = 0

    for result in results:
        if is_relevant(
            result["retrieved_chunk_ids"][:k],
            result["expected_chunk_ids"],
            result["relevance_type"],
        ):
            successful += 1

    return successful / len(results)


def calculate_precision_at_k(results, k):
    if not results:
        return 0.0

    scores = []

    for result in results:
        retrieved = result["retrieved_chunk_ids"][:k]
        expected = set(result["expected_chunk_ids"])

        if not retrieved:
            scores.append(0.0)
            continue

        relevant_count = sum(
            1
            for chunk_id in retrieved
            if chunk_id in expected
        )

        scores.append(
            relevant_count / len(retrieved)
        )

    return sum(scores) / len(scores)


def calculate_mrr(results):
    if not results:
        return 0.0

    reciprocal_ranks = []

    for result in results:
        expected = set(result["expected_chunk_ids"])

        reciprocal_rank = 0.0

        for rank, chunk_id in enumerate(
            result["retrieved_chunk_ids"],
            start=1,
        ):
            if chunk_id in expected:
                reciprocal_rank = 1.0 / rank
                break

        reciprocal_ranks.append(
            reciprocal_rank
        )

    return sum(reciprocal_ranks) / len(
        reciprocal_ranks
    )


def calculate_ndcg_at_k(results, k):
    if not results:
        return 0.0

    scores = []

    for result in results:
        expected = set(result["expected_chunk_ids"])
        retrieved = result["retrieved_chunk_ids"][:k]

        dcg = 0.0

        for rank, chunk_id in enumerate(
            retrieved,
            start=1,
        ):
            if chunk_id in expected:
                dcg += 1.0 / math.log2(rank + 1)

        relevant_count = min(
            len(expected),
            k,
        )

        if relevant_count == 0:
            scores.append(0.0)
            continue

        ideal_dcg = sum(
            1.0 / math.log2(rank + 1)
            for rank in range(
                1,
                relevant_count + 1,
            )
        )

        scores.append(
            dcg / ideal_dcg
        )

    return sum(scores) / len(scores)


def evaluate_experiment(
    experiment: str,
    dataset,
):
    results = []

    total_latency = 0.0

    for case in dataset:
        start = time.perf_counter()

        retrieved = retrieve_experiment(
            experiment=experiment,
            query=case["question"],
            department=case.get("department"),
            limit=TOP_K,
        )

        elapsed = time.perf_counter() - start
        total_latency += elapsed

        retrieved_chunk_ids = [
            result.chunk.id
            for result in retrieved
        ]

        relevant_retrieved = [
            chunk_id
            for chunk_id in retrieved_chunk_ids
            if chunk_id in case["relevant_chunk_ids"]
        ]

        results.append(
            {
                "id": case["id"],
                "question": case["question"],
                "expected_chunk_ids": case[
                    "relevant_chunk_ids"
                ],
                "retrieved_chunk_ids": retrieved_chunk_ids,
                "relevant_retrieved_chunk_ids": (
                    relevant_retrieved
                ),
                "relevance_type": case.get(
                    "relevance_type",
                    "all",
                ),
            }
        )

    return {
        "experiment": experiment,
        "results": results,
        "average_latency_ms": (
            total_latency / len(dataset) * 1000
            if dataset
            else 0.0
        ),
    }


def print_summary(evaluation):
    results = evaluation["results"]

    print()
    print("=" * 70)
    print(
        f"EXPERIMENT: {evaluation['experiment']}"
    )
    print("=" * 70)

    print(
        f"Recall@1:     "
        f"{calculate_recall_at_k(results, 1):.4f}"
    )

    print(
        f"Recall@3:     "
        f"{calculate_recall_at_k(results, 3):.4f}"
    )

    print(
        f"Recall@5:     "
        f"{calculate_recall_at_k(results, 5):.4f}"
    )

    print(
        f"Precision@1:  "
        f"{calculate_precision_at_k(results, 1):.4f}"
    )

    print(
        f"Precision@3:  "
        f"{calculate_precision_at_k(results, 3):.4f}"
    )

    print(
        f"Precision@5:  "
        f"{calculate_precision_at_k(results, 5):.4f}"
    )

    print(
        f"MRR:          "
        f"{calculate_mrr(results):.4f}"
    )

    print(
        f"NDCG@1:       "
        f"{calculate_ndcg_at_k(results, 1):.4f}"
    )

    print(
        f"NDCG@3:       "
        f"{calculate_ndcg_at_k(results, 3):.4f}"
    )

    print(
        f"NDCG@5:       "
        f"{calculate_ndcg_at_k(results, 5):.4f}"
    )

    print(
        f"Avg Latency:  "
        f"{evaluation['average_latency_ms']:.2f} ms"
    )


def main():
    dataset = load_dataset()

    experiments = [
        "vector",
        "keyword",
        "hybrid",
        "hybrid_rerank",
        "hybrid_rerank_multi_query",
    ]

    print(
        f"Evaluation cases: {len(dataset)}"
    )

    for experiment in experiments:
        evaluation = evaluate_experiment(
            experiment=experiment,
            dataset=dataset,
        )

        print_summary(evaluation)


if __name__ == "__main__":
    main()