from typing import List, Optional

from app.schemas.rag.response import (
    RAGResponse,
    ClarificationOption as RAGClarificationOption,
)

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

from app.services.rag.citation_builder import (
    citation_builder,
)

from app.services.rag.prompts.rag_prompt import (
    rag_prompt_builder,
)

from app.services.llm.groq_client import (
    groq_client,
)

from app.services.retrieval.retrieval_pipeline import (
    retrieval_pipeline,
)

from app.services.retrieval.decomposed_retrieval_service import (
    decomposed_retrieval_service,
)

from app.services.query_decomposition.decomposition_decision_service import (
    decomposition_decision_service,
)

from app.services.ambiguity.ambiguity_detector import (
    ambiguity_detector,
)

from app.services.ambiguity.ambiguity_analysis_service import (
    ambiguity_analysis_service,
)

from app.services.ambiguity.clarification_service import (
    clarification_service,
)
from app.services.ambiguity.clarification_resolver import (
    clarification_resolver,
)
from app.services.rag.citation_validator import citation_validator
from app.core.config import settings


class RAGService:

    def retrieve(
        self,
        query: str,
        limit: Optional[int] = None,
        department: Optional[str] = None,
    ) -> List[RetrievalResult]:

        final_top_k = limit if limit is not None else settings.rag_top_k
        candidate_limit = settings.rag_candidate_limit

        if decomposition_decision_service.should_decompose(query):
            return self.retrieve_with_decomposition(
                query=query,
                limit=final_top_k,
                candidate_limit=candidate_limit,
                department=department,
            )

        rewritten_query = query_rewriter_service.rewrite(
            query
        )

        search_query = (
            rewritten_query
            or query
        )

        generated_queries = multi_query_service.generate(
            query=search_query,
            num_queries=3,
        )

        search_queries = [query]

        if (
            search_query.strip().lower()
            != query.strip().lower()
        ):
            search_queries.append(
                search_query
            )

        for generated_query in generated_queries:

            if (
                generated_query.strip().lower()
                != search_query.strip().lower()
            ):
                search_queries.append(
                    generated_query
                )

        return retrieval_pipeline.retrieve(
            search_queries=search_queries,
            limit=final_top_k,
            candidate_limit=candidate_limit,
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

        for rank, result in enumerate(
                results,
                start=1,
        ):
            chunk = result.chunk

            source_name = (
                chunk.document.source_name
                if chunk.document
                else "Unknown"
            )

            content = (
                    result.compressed_content
                    or chunk.content
            )

            context_parts.append(
                f"""[Source {rank}]
    Document: {source_name}
    Document ID: {chunk.document_id}
    Chunk ID: {chunk.id}
    Chunk Index: {chunk.chunk_index}

    Content:
    {content}"""
            )

        return "\n\n".join(context_parts)


    def _build_clarification_response(
        self,
        clarification,
    ) -> RAGResponse:

        options = [
            RAGClarificationOption(
                label=option.label,
                topic=option.topic,
            )
            for option in clarification.options
        ]

        return RAGResponse(
            answer="",
            sources=[],
            should_clarify=True,
            clarification_question=(
                clarification.question
            ),
            clarification_options=options,
        )

    def generate(
        self,
        question: str,
        limit: Optional[int] = None,
        department: Optional[str] = None,
    ) -> RAGResponse:

        results = self.retrieve(
            query=question,
            limit=limit,
            department=department,
        )

        explicit_topic = (
            ambiguity_detector.has_explicit_topic(
                question
            )
        )

        ambiguity_analysis = (
            ambiguity_analysis_service.analyze(
                results=results,
                explicit_topic=explicit_topic,
                query=question,
            )
        )

        if ambiguity_analysis.is_ambiguous:

            clarification = (
                clarification_service.build_clarification(
                    query=question,
                    analysis=ambiguity_analysis,
                    results=results,
                )
            )

            if clarification.should_clarify:

                return self._build_clarification_response(
                    clarification
                )

        compressed_results = (
            context_compressor.compress(
                query=question,
                results=results,
            )
        )

        context = self.build_context(
            compressed_results
        )

        if not context:

            return RAGResponse(
                answer=(
                    "I don't have enough information "
                    "in the provided knowledge base "
                    "to answer that."
                ),
                sources=[],
            )

        prompt = rag_prompt_builder.build(
            question=question,
            context=context,
        )

        answer = groq_client.chat(prompt)

        citation_validation = citation_validator.validate(
            answer=answer,
            results=results,
        )

        if not citation_validation.is_valid:
            answer = (
                "I couldn't safely verify the source citations for this answer. "
                "Please try the question again."
            )

        citations = citation_builder.build(results)

        return RAGResponse(
            answer=answer,
            sources=citations,
        )

    def generate_with_clarification(
            self,
            original_question: str,
            selected_topic: str,
            limit: int = 5,
            department: Optional[str] = None,
    ) -> RAGResponse:

        resolution = clarification_resolver.resolve(
            original_query=original_question,
            selected_topic=selected_topic,
        )

        return self.generate(
            question=resolution.resolved_query,
            limit=limit,
            department=department,
        )


rag_service = RAGService()