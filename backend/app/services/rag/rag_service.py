from typing import List, Optional

from app.schemas.rag.response import RAGResponse
from app.services.retrieval.retrieval_result import RetrievalResult
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
from app.services.retrieval.retrieval_pipeline import retrieval_pipeline
from app.services.retrieval.decomposed_retrieval_service import (
    decomposed_retrieval_service,
)
from app.services.query_decomposition.decomposition_decision_service import (
    decomposition_decision_service,
)



class RAGService:

    def retrieve(
            self,
            query: str,
            limit: int = 5,
            department: Optional[str] = None,
    ) -> List[RetrievalResult]:

        if decomposition_decision_service.should_decompose(query):
            return self.retrieve_with_decomposition(
                query=query,
                limit=limit,
                department=department,
            )

        rewritten_query = query_rewriter_service.rewrite(query)
        search_query = rewritten_query or query

        generated_queries = multi_query_service.generate(
            query=search_query,
            num_queries=3,
        )

        search_queries = [query]

        if search_query.strip().lower() != query.strip().lower():
            search_queries.append(search_query)

        for generated_query in generated_queries:
            if generated_query.strip().lower() != search_query.strip().lower():
                search_queries.append(generated_query)

        return retrieval_pipeline.retrieve(
            search_queries=search_queries,
            limit=limit,
            department=department,
        )

    def retrieve_with_decomposition(
            self,
            query: str,
            limit: int = 5,
            department: Optional[str] = None,
    ) -> List[RetrievalResult]:

        return decomposed_retrieval_service.retrieve(
            query=query,
            limit=limit,
            department=department,
        )


    def build_context(
            self,
            results: List[RetrievalResult],
    ) -> str:
        if not results:
            return ""

        context_parts = []

        for rank, result in enumerate(results, start=1):
            content = result.compressed_content or result.chunk.content

            context_parts.append(
                f"[Context {rank}]\n{content}"
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