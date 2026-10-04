from math import log2
from typing import List, Set


def recall_at_k(
    retrieved: List[int],
    relevant: Set[int],
    k: int,
) -> float:
    if not relevant:
        return 0.0

    retrieved_at_k = retrieved[:k]
    hits = len(set(retrieved_at_k) & relevant)

    return hits / len(relevant)


def precision_at_k(
    retrieved: List[int],
    relevant: Set[int],
    k: int,
) -> float:
    if k <= 0:
        return 0.0

    retrieved_at_k = retrieved[:k]

    if not retrieved_at_k:
        return 0.0

    hits = len(set(retrieved_at_k) & relevant)

    return hits / len(retrieved_at_k)


def reciprocal_rank(
    retrieved: List[int],
    relevant: Set[int],
) -> float:
    for rank, item in enumerate(retrieved, start=1):
        if item in relevant:
            return 1.0 / rank

    return 0.0


def ndcg_at_k(
    retrieved: List[int],
    relevant: Set[int],
    k: int,
) -> float:
    retrieved_at_k = retrieved[:k]

    if not retrieved_at_k or not relevant:
        return 0.0

    dcg = 0.0

    for rank, item in enumerate(retrieved_at_k, start=1):
        relevance = 1 if item in relevant else 0

        if relevance:
            dcg += relevance / log2(rank + 1)

    ideal_relevant_count = min(len(relevant), k)

    idcg = sum(
        1 / log2(rank + 1)
        for rank in range(1, ideal_relevant_count + 1)
    )

    if idcg == 0:
        return 0.0

    return dcg / idcg