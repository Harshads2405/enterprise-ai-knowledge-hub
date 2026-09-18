from typing import List, Optional

from app.models.document_chunk import DocumentChunk
from app.schemas.rag.response import RAGResponse
from app.services.embeddings.embedding_service import embedding_service
from app.services.retrieval.vector_search import vector_search
from app.services.retrieval.retrieval_result import RetrievalResult
from app.services.reranking.reranker_service import reranker_service
from app.services.query_rewriting.query_rewriter_service import (
    query_rewriter_service,
)
from app.services.context_compression.context_compressor import (
    context_compressor,
)
from app.services.multi_query.multi_query_service import (
    multi_query_service,
)
from app.services.rag.citation_builder import citation_builder
from app.services.rag.prompts.rag_prompt import rag_prompt_builder
from app.services.llm.groq_client import groq_client


class RAGService:
    def retrieve(
            self,
            query: str,
            limit: int = 5,
            department: Optional[str] = None,
    ) -> List[RetrievalResult]:
        rewritten_query = query_rewriter_service.rewrite(query)

        search_query = rewritten_query or query

        generated_queries = multi_query_service.generate(
            query=search_query,
            num_queries=3,
        )

        search_queries = [search_query]

        for generated_query in generated_queries:
            if generated_query.strip().lower() != search_query.strip().lower():
                search_queries.append(generated_query)

        candidate_limit = max(limit * 2, 10)

        unique_results = {}

        for search_query_item in search_queries:
            query_embedding = embedding_service.embed_query(
                search_query_item
            )

            candidates = vector_search.hybrid_search(
                query_embedding=query_embedding,
                query=search_query_item,
                limit=candidate_limit,
                department=department,
            )

            for result in candidates:
                unique_results[result.chunk.id] = result

        if not unique_results and search_query != query:
            query_embedding = embedding_service.embed_query(query)

            candidates = vector_search.hybrid_search(
                query_embedding=query_embedding,
                query=query,
                limit=candidate_limit,
                department=department,
            )

            for result in candidates:
                unique_results[result.chunk.id] = result

        candidates = list(unique_results.values())

        return reranker_service.rerank(
            query=query,
            results=candidates,
            top_k=limit,
        )

    def build_context(
        self,
        results: List[RetrievalResult],
    ) -> str:
        if not results:
            return ""

        context_parts = []

        for rank, result in enumerate(results, start=1):
            context_parts.append(
                f"[Context {rank}]\n{result.chunk.content}"
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

        compressed_results = context_compressor.compress(
            query=question,
            results=results,
        )

        context = self.build_context(compressed_results)

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