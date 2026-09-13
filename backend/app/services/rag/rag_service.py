from typing import List, Tuple

from app.models.document_chunk import DocumentChunk
from app.services.embeddings.embedding_service import embedding_service
from app.services.retrieval.vector_search import vector_search
from app.services.rag.prompts.rag_prompt import rag_prompt_builder
from app.services.llm.groq_client import groq_client


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

    def generate(
        self,
        question: str,
        limit: int = 5,
    ) -> str:
        results = self.retrieve(
            query=question,
            limit=limit,
        )

        context = self.build_context(results)

        if not context:
            return (
                "I don't have enough information in the "
                "provided knowledge base to answer that."
            )

        prompt = rag_prompt_builder.build(
            question=question,
            context=context,
        )

        return groq_client.chat(prompt)


rag_service = RAGService()