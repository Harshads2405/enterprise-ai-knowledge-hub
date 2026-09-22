from typing import List

from app.services.ingestion.document_unit import DocumentUnit


class TextChunker:
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")

        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative")

        if chunk_overlap >= chunk_size:
            raise ValueError(
                "chunk_overlap must be smaller than chunk_size"
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self, text: str) -> List[str]:
        text = text.strip()

        if not text:
            return []

        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = min(
                start + self.chunk_size,
                text_length,
            )

            chunk = text[start:end].strip()

            if chunk:
                chunks.append(chunk)

            if end >= text_length:
                break

            start = end - self.chunk_overlap

        return chunks

    def split_units(
        self,
        units: List[DocumentUnit],
    ) -> List[DocumentUnit]:
        chunks = []

        for unit in units:
            unit_chunks = self.split(unit.content)

            for chunk in unit_chunks:
                chunks.append(
                    DocumentUnit(
                        content=chunk,
                        metadata=unit.metadata.copy(),
                    )
                )

        return chunks


text_chunker = TextChunker()