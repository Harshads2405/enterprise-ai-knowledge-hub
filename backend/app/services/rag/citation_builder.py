from typing import List, Tuple

from app.models.document_chunk import DocumentChunk
from app.schemas.rag.citation import Citation


class CitationBuilder:
    def build(
        self,
        results: List[Tuple[DocumentChunk, float]],
    ) -> List[Citation]:
        citations = []

        for chunk, distance in results:
            source_name = (
                chunk.document.source_name
                if chunk.document
                else "Unknown"
            )

            citations.append(
                Citation(
                    document_id=chunk.document_id,
                    chunk_id=chunk.id,
                    chunk_index=chunk.chunk_index,
                    source_name=source_name,
                    distance=float(distance),
                )
            )

        return citations


citation_builder = CitationBuilder()