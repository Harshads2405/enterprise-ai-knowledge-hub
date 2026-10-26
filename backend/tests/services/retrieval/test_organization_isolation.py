import pytest

from app.services.retrieval.retrieval_pipeline import RetrievalPipeline
from app.services.retrieval.vector_search import vector_search


@pytest.mark.parametrize("organization_id", [None, 0, -1, True, False, "1"])
def test_vector_keyword_and_hybrid_search_reject_invalid_organization_ids(
    organization_id,
):
    with pytest.raises(ValueError, match="valid organization_id"):
        vector_search.search([], organization_id=organization_id)

    with pytest.raises(ValueError, match="valid organization_id"):
        vector_search.keyword_search("policy", organization_id=organization_id)

    with pytest.raises(ValueError, match="valid organization_id"):
        vector_search.hybrid_search(
            [],
            "policy",
            organization_id=organization_id,
        )


@pytest.mark.parametrize("organization_id", [None, 0, -1, True, False, "1"])
def test_retrieval_pipeline_rejects_invalid_organization_ids(organization_id):
    with pytest.raises(ValueError, match="valid organization_id"):
        RetrievalPipeline().retrieve(
            search_queries=["policy"],
            organization_id=organization_id,
        )


def test_retrieval_pipeline_passes_organization_id_to_hybrid_search(monkeypatch):
    captured = {}

    monkeypatch.setattr(
        "app.services.retrieval.retrieval_pipeline.embedding_service.embed_query",
        lambda query: [0.1],
    )

    def fake_hybrid_search(**kwargs):
        captured["organization_id"] = kwargs["organization_id"]
        return []

    monkeypatch.setattr(
        "app.services.retrieval.retrieval_pipeline.vector_search.hybrid_search",
        fake_hybrid_search,
    )

    assert RetrievalPipeline().retrieve(
        search_queries=["policy"],
        organization_id=17,
    ) == []
    assert captured["organization_id"] == 17
