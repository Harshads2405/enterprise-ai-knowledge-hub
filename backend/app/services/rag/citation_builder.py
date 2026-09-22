from typing import List

from app.models.document_chunk import DocumentChunk
from app.schemas.rag.citation import Citation
from app.services.retrieval.retrieval_result import RetrievalResult


class CitationBuilder:
    def build(
        self,
        results: List[RetrievalResult],
    ) -> List[Citation]:
        citations = []

        for result in results:
            chunk: DocumentChunk = result.chunk

            source_name = (
                chunk.document.source_name
                if chunk.document
                else "Unknown"
            )

            page = None

            if chunk.chunk_metadata:
                page = chunk.chunk_metadata.get("page")

            citations.append(
                Citation(
                    document_id=chunk.document_id,
                    chunk_id=chunk.id,
                    chunk_index=chunk.chunk_index,
                    source_name=source_name,
                    page=page,
                    retrieval_score=float(
                        result.retrieval_score
                    ),
                    reranker_score=(
                        float(result.reranker_score)
                        if result.reranker_score is not None
                        else None
                    ),
                )
            )

        return citations


citation_builder = CitationBuilder()