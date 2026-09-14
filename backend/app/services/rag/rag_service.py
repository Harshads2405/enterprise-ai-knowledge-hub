from typing import List, Optional, Tuple

from app.models.document_chunk import DocumentChunk
from app.schemas.rag.response import RAGResponse
from app.services.embeddings.embedding_service import embedding_service
from app.services.retrieval.vector_search import vector_search
from app.services.rag.citation_builder import citation_builder
from app.services.rag.prompts.rag_prompt import rag_prompt_builder
from app.services.llm.groq_client import groq_client


class RAGService:
    def retrieve(
        self,
        query: str,
        limit: int = 5,
        department: Optional[str] = None,
    ) -> List[Tuple[DocumentChunk, float]]:
        query_embedding = embedding_service.embed_query(query)

        return vector_search.search(
            query_embedding=query_embedding,
            limit=limit,
            department=department,
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
                f"[Context {rank}]\n{chunk.content}"
            )

        return "\n\n".join(context_parts)

    def generate(
        self,
        question: str,
        limit: int = 5,
        department: Optional[str] = None,
    ) -> RAGResponse:
        results = self.retrieve(
            query=question,
            limit=limit,
            department=department,
        )

        context = self.build_context(results)

        if not context:
            return RAGResponse(
                answer=(
                    "I don't have enough information in the provided "
                    "knowledge base to answer that."
                ),
                sources=[],
            )

        prompt = rag_prompt_builder.build(
            question=question,
            context=context,
        )

        answer = groq_client.chat(prompt)

        citations = citation_builder.build(results)

        return RAGResponse(
            answer=answer,
            sources=citations,
        )


rag_service = RAGService()