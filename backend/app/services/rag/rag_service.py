from typing import List, Tuple

from app.models.document_chunk import DocumentChunk
from app.services.embeddings.embedding_service import embedding_service
from app.services.retrieval.vector_search import vector_search


class RAGService:
    def retrieve(
        self,
        query: str,
        limit: int = 5,
    ) -> List[Tuple[DocumentChunk, float]]:
        query_embedding = embedding_service.embed_query(query)

        return vector_search.search(
            query_embedding=query_embedding,
            limit=limit,
        )

    def build_context(
        self,
        results: List[Tuple[DocumentChunk, float]],
    ) -> str:
        if not results:
            return ""

        context_parts = []

        for rank, (chunk, distance) in enumerate(results, start=1):
            context_parts.append(
                f"[Context {rank}]\n"
                f"{chunk.content}"
            )

        return "\n\n".join(context_parts)


rag_service = RAGService()