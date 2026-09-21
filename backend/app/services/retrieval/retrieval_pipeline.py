from typing import List, Optional

from app.services.embeddings.embedding_service import embedding_service
from app.services.retrieval.vector_search import vector_search
from app.services.retrieval.retrieval_result import RetrievalResult
from app.services.reranking.reranker_service import reranker_service


class RetrievalPipeline:

    def retrieve(
        self,
        search_queries: List[str],
        limit: int = 5,
        candidate_limit: Optional[int] = None,
        department: Optional[str] = None,
    ) -> List[RetrievalResult]:

        # Remove duplicate search formulations while preserving order.
        unique_search_queries = []
        seen_queries = set()

        for search_query in search_queries:
            normalized_query = search_query.strip().lower()

            if not normalized_query:
                continue

            if normalized_query in seen_queries:
                continue

            seen_queries.add(normalized_query)
            unique_search_queries.append(search_query)

        if not unique_search_queries:
            return []

        if candidate_limit is None:
            candidate_limit = max(limit * 2, 10)

        unique_results = {}

        for search_query in unique_search_queries:
            query_embedding = embedding_service.embed_query(
                search_query
            )

            candidates = vector_search.hybrid_search(
                query_embedding=query_embedding,
                query=search_query,
                limit=candidate_limit,
                department=department,
            )

            if not candidates:
                continue

            query_reranked = reranker_service.rerank(
                query=search_query,
                results=candidates,
                top_k=candidate_limit,
            )

            for rank, result in enumerate(query_reranked, start=1):
                chunk_id = result.chunk.id
                current_score = result.reranker_score

                if chunk_id not in unique_results:
                    result.retrieval_queries = [search_query]
                    result.retrieval_ranks = [rank]
                    result.retrieval_count = 1
                    result.best_retrieval_rank = rank

                    result.reranker_scores = []

                    if current_score is not None:
                        result.reranker_scores.append(
                            float(current_score)
                        )

                    result.reranker_queries = [search_query]

                    result.best_reranker_score = (
                        float(current_score)
                        if current_score is not None
                        else None
                    )

                    result.best_reranker_query = (
                        search_query
                        if current_score is not None
                        else None
                    )

                    unique_results[chunk_id] = result

                else:
                    existing = unique_results[chunk_id]

                    existing.retrieval_queries.append(
                        search_query
                    )

                    existing.retrieval_ranks.append(rank)
                    existing.retrieval_count += 1

                    if (
                        existing.best_retrieval_rank is None
                        or rank < existing.best_retrieval_rank
                    ):
                        existing.best_retrieval_rank = rank

                    if current_score is not None:
                        score = float(current_score)

                        existing.reranker_scores.append(score)
                        existing.reranker_queries.append(
                            search_query
                        )

                        if (
                            existing.best_reranker_score is None
                            or score > existing.best_reranker_score
                        ):
                            existing.best_reranker_score = score
                            existing.best_reranker_query = search_query

        if not unique_results:
            return []

        results = list(unique_results.values())

        for result in results:
            result.reranker_score = result.best_reranker_score

        results.sort(
            key=lambda result: (
                result.best_reranker_score
                if result.best_reranker_score is not None
                else float("-inf")
            ),
            reverse=True,
        )

        return results[:limit]


retrieval_pipeline = RetrievalPipeline()
