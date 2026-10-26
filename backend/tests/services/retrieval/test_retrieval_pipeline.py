
from types import SimpleNamespace

from app.services.retrieval.retrieval_pipeline import RetrievalPipeline


def make_result(chunk_id: int, score: float):
    return SimpleNamespace(
        chunk=SimpleNamespace(id=chunk_id),
        reranker_score=score,
        best_reranker_score=score,
        retrieval_queries=[],
        retrieval_ranks=[],
        retrieval_count=1,
        best_retrieval_rank=1,
        reranker_scores=[score],
        reranker_queries=[],
        best_reranker_query=None,
    )


def test_candidate_limit_defaults_from_final_limit(monkeypatch):
    pipeline = RetrievalPipeline()
    captured = {}

    def fake_embed_query(query):
        return [0.1]

    def fake_hybrid_search(**kwargs):
        captured["limit"] = kwargs["limit"]
        captured["organization_id"] = kwargs["organization_id"]
        return [make_result(i, 1.0 - i * 0.1) for i in range(1, 11)]

    def fake_rerank(query, results, top_k):
        captured["rerank_top_k"] = top_k
        return results[:top_k]

    monkeypatch.setattr(
        "app.services.retrieval.retrieval_pipeline.embedding_service.embed_query",
        fake_embed_query,
    )
    monkeypatch.setattr(
        "app.services.retrieval.retrieval_pipeline.vector_search.hybrid_search",
        fake_hybrid_search,
    )
    monkeypatch.setattr(
        "app.services.retrieval.retrieval_pipeline.reranker_service.rerank",
        fake_rerank,
    )

    results = pipeline.retrieve(
        search_queries=["test query"],
        organization_id=1,
        limit=5,
    )

    assert captured["organization_id"] == 1
    assert captured["limit"] == 10
    assert captured["rerank_top_k"] == 10
    assert len(results) == 5


def test_explicit_candidate_limit_is_independent_of_final_limit(monkeypatch):
    pipeline = RetrievalPipeline()
    captured = {}

    def fake_embed_query(query):
        return [0.1]

    def fake_hybrid_search(**kwargs):
        captured["limit"] = kwargs["limit"]
        captured["organization_id"] = kwargs["organization_id"]
        return [make_result(i, 1.0 - i * 0.1) for i in range(1, 6)]

    def fake_rerank(query, results, top_k):
        captured["rerank_top_k"] = top_k
        return results[:top_k]

    monkeypatch.setattr(
        "app.services.retrieval.retrieval_pipeline.embedding_service.embed_query",
        fake_embed_query,
    )
    monkeypatch.setattr(
        "app.services.retrieval.retrieval_pipeline.vector_search.hybrid_search",
        fake_hybrid_search,
    )
    monkeypatch.setattr(
        "app.services.retrieval.retrieval_pipeline.reranker_service.rerank",
        fake_rerank,
    )

    results = pipeline.retrieve(
        search_queries=["test query"],
        organization_id=1,
        candidate_limit=5,
        limit=3,
    )

    assert captured["organization_id"] == 1
    assert captured["limit"] == 5
    assert captured["rerank_top_k"] == 5
    assert len(results) == 3
