from types import SimpleNamespace

from app.services.rag.citation_builder import CitationBuilder


def make_result(
    page=None,
    retrieval_score=0.85,
    reranker_score=0.92,
):
    chunk = SimpleNamespace(
        id=101,
        document_id=42,
        chunk_index=3,
        chunk_metadata=(
            {"page": page}
            if page is not None
            else {}
        ),
        document=SimpleNamespace(
            source_name="employee_policy.pdf",
        ),
    )

    return SimpleNamespace(
        chunk=chunk,
        retrieval_score=retrieval_score,
        reranker_score=reranker_score,
    )


def test_build_includes_page_metadata():
    builder = CitationBuilder()

    result = builder.build(
        [make_result(page=7)]
    )

    assert len(result) == 1

    citation = result[0]

    assert citation.document_id == 42
    assert citation.chunk_id == 101
    assert citation.chunk_index == 3
    assert citation.source_name == "employee_policy.pdf"
    assert citation.page == 7
    assert citation.retrieval_score == 0.85
    assert citation.reranker_score == 0.92


def test_build_uses_none_when_page_metadata_is_missing():
    builder = CitationBuilder()

    result = builder.build(
        [make_result()]
    )

    assert len(result) == 1
    assert result[0].page is None
