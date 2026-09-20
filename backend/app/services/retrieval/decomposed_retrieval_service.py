from typing import List, Optional

from app.services.query_decomposition.query_decomposer_service import (
    query_decomposer_service,
)
from app.services.retrieval.retrieval_pipeline import retrieval_pipeline
from app.services.retrieval.retrieval_result import RetrievalResult


class DecomposedRetrievalService:

    def retrieve(
        self,
        query: str,
        limit: int = 5,
        department: Optional[str] = None,
    ) -> List[RetrievalResult]:

        decomposed_queries = query_decomposer_service.decompose(
            query=query,
            max_queries=3,
        )

        if not decomposed_queries:
            return []

        # Single information need:
        # use the normal retrieval pipeline with one query.
        if len(decomposed_queries) == 1:
            return retrieval_pipeline.retrieve(
                search_queries=decomposed_queries,
                limit=limit,
                department=department,
            )

        unique_results = {}

        # Multiple information needs:
        # retrieve each subquery independently.
        for subquery in decomposed_queries:

            results = retrieval_pipeline.retrieve(
                search_queries=[subquery],
                limit=limit,
                department=department,
            )

            for result in results:

                chunk_id = result.chunk.id

                if chunk_id not in unique_results:
                    unique_results[chunk_id] = result
                    continue

                existing = unique_results[chunk_id]

                # Preserve retrieval evidence.
                existing.retrieval_queries.extend(
                    result.retrieval_queries
                )

                existing.retrieval_ranks.extend(
                    result.retrieval_ranks
                )

                existing.retrieval_count += (
                    result.retrieval_count
                )

                if (
                    result.best_retrieval_rank is not None
                    and (
                        existing.best_retrieval_rank is None
                        or result.best_retrieval_rank
                        < existing.best_retrieval_rank
                    )
                ):
                    existing.best_retrieval_rank = (
                        result.best_retrieval_rank
                    )

                # Preserve reranker evidence.
                existing.reranker_scores.extend(
                    result.reranker_scores
                )

                existing.reranker_queries.extend(
                    result.reranker_queries
                )

                if (
                    result.best_reranker_score is not None
                    and (
                        existing.best_reranker_score is None
                        or result.best_reranker_score
                        > existing.best_reranker_score
                    )
                ):
                    existing.best_reranker_score = (
                        result.best_reranker_score
                    )

                    existing.best_reranker_query = (
                        result.best_reranker_query
                    )

        if not unique_results:
            return []

        merged_results = list(unique_results.values())

        for result in merged_results:
            result.reranker_score = result.best_reranker_score

        merged_results.sort(
            key=lambda result: (
                result.best_reranker_score
                if result.best_reranker_score is not None
                else float("-inf")
            ),
            reverse=True,
        )

        return merged_results[:limit]


decomposed_retrieval_service = DecomposedRetrievalService()
