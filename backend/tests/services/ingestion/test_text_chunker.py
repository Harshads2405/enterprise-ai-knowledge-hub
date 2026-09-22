import pytest

from app.services.ingestion.chunking.text_chunker import TextChunker

from app.services.ingestion.document_unit import DocumentUnit
def test_empty_text_returns_no_chunks():
    chunker = TextChunker()

    assert chunker.split("") == []


def test_whitespace_only_returns_no_chunks():
    chunker = TextChunker()

    assert chunker.split("   \n\t  ") == []


def test_short_text_returns_single_chunk():
    chunker = TextChunker(
        chunk_size=100,
        chunk_overlap=20,
    )

    result = chunker.split("This is a short document.")

    assert result == ["This is a short document."]


def test_long_text_is_split_into_multiple_chunks():
    chunker = TextChunker(
        chunk_size=10,
        chunk_overlap=2,
    )

    text = "abcdefghijklmnopqrstuvwxyz"

    result = chunker.split(text)

    assert len(result) > 1


def test_chunk_size_is_respected():
    chunker = TextChunker(
        chunk_size=10,
        chunk_overlap=2,
    )

    text = "abcdefghijklmnopqrstuvwxyz"

    result = chunker.split(text)

    for chunk in result:
        assert len(chunk) <= 10


def test_chunk_overlap_is_preserved():
    chunker = TextChunker(
        chunk_size=10,
        chunk_overlap=2,
    )

    text = "abcdefghijklmnopqrstuvwxyz"

    result = chunker.split(text)

    assert result[0][-2:] == result[1][:2]


def test_invalid_chunk_size():
    with pytest.raises(
        ValueError,
        match="chunk_size must be greater than 0",
    ):
        TextChunker(chunk_size=0)


def test_negative_overlap():
    with pytest.raises(
        ValueError,
        match="chunk_overlap cannot be negative",
    ):
        TextChunker(
            chunk_size=100,
            chunk_overlap=-1,
        )


def test_overlap_must_be_smaller_than_chunk_size():
    with pytest.raises(
        ValueError,
        match="chunk_overlap must be smaller than chunk_size",
    ):
        TextChunker(
            chunk_size=100,
            chunk_overlap=100,
        )


def test_split_units_empty_list_returns_no_chunks():
    chunker = TextChunker()

    result = chunker.split_units([])

    assert result == []


def test_split_units_preserves_metadata():
    chunker = TextChunker(
        chunk_size=10,
        chunk_overlap=2,
    )

    units = [
        DocumentUnit(
            content="abcdefghijklmnopqrstuvwxyz",
            metadata={
                "page": 3,
                "document_type": "policy",
            },
        )
    ]

    result = chunker.split_units(units)

    assert len(result) > 1

    for chunk in result:
        assert chunk.metadata == {
            "page": 3,
            "document_type": "policy",
        }


def test_split_units_preserves_page_metadata():
    chunker = TextChunker(
        chunk_size=10,
        chunk_overlap=2,
    )

    units = [
        DocumentUnit(
            content="page three content that is long enough to split",
            metadata={"page": 3},
        ),
        DocumentUnit(
            content="page four content that is long enough to split",
            metadata={"page": 4},
        ),
    ]

    result = chunker.split_units(units)

    page_values = [chunk.metadata["page"] for chunk in result]

    assert 3 in page_values
    assert 4 in page_values


def test_split_units_does_not_share_metadata_dictionary():
    chunker = TextChunker(
        chunk_size=10,
        chunk_overlap=2,
    )

    original_metadata = {"page": 3}

    units = [
        DocumentUnit(
            content="abcdefghijklmnopqrstuvwxyz",
            metadata=original_metadata,
        )
    ]

    result = chunker.split_units(units)

    assert len(result) > 1

    assert result[0].metadata is not result[1].metadata