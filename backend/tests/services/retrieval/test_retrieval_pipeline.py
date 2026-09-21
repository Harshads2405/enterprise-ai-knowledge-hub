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
        return [
            make_result(1, 1.0),
            make_result(2, 0.9),
            make_result(3, 0.8),
            make_result(4, 0.7),
            make_result(5, 0.6),
            make_result(6, 0.5),
            make_result(7, 0.4),
            make_result(8, 0.3),
            make_result(9, 0.2),
            make_result(10, 0.1),
        ]

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
        limit=5,
    )

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
        return [
            make_result(1, 1.0),
            make_result(2, 0.9),
            make_result(3, 0.8),
            make_result(4, 0.7),
            make_result(5, 0.6),
        ]

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
        candidate_limit=5,
        limit=3,
    )

    assert captured["limit"] == 5
    assert captured["rerank_top_k"] == 5
    assert len(results) == 3