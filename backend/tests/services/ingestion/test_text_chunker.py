import pytest

from app.services.ingestion.chunking.text_chunker import TextChunker


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