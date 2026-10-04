from math import log2
from typing import List, Set
from app.services.evaluation.retrieval_metrics import (
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)

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


def test_recall_at_k():
    retrieved = [1, 2, 3, 4, 5]
    relevant = {2, 4}

    assert recall_at_k(retrieved, relevant, 1) == 0.0
    assert recall_at_k(retrieved, relevant, 3) == 0.5
    assert recall_at_k(retrieved, relevant, 5) == 1.0


def test_precision_at_k():
    retrieved = [1, 2, 3, 4, 5]
    relevant = {2, 4}

    assert precision_at_k(retrieved, relevant, 1) == 0.0
    assert precision_at_k(retrieved, relevant, 3) == 1 / 3
    assert precision_at_k(retrieved, relevant, 5) == 2 / 5


def test_reciprocal_rank():
    retrieved = [5, 3, 2, 1]
    relevant = {2}

    assert reciprocal_rank(retrieved, relevant) == 1 / 3


def test_reciprocal_rank_when_no_relevant_result():
    retrieved = [5, 3, 1]
    relevant = {2}

    assert reciprocal_rank(retrieved, relevant) == 0.0


def test_ndcg_at_k():
    retrieved = [1, 2, 3, 4]
    relevant = {2, 4}

    score = ndcg_at_k(retrieved, relevant, 4)

    assert 0.0 < score < 1.0


def test_ndcg_perfect_ranking():
    retrieved = [2, 4, 1, 3]
    relevant = {2, 4}

    assert ndcg_at_k(retrieved, relevant, 4) == 1.0