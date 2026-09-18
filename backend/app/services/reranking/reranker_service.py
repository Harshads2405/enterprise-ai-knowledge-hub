from typing import List

from sentence_transformers import CrossEncoder

from app.services.retrieval.retrieval_result import RetrievalResult


class RerankerService:
    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    ):
        self.model = CrossEncoder(model_name)

    def rerank(
        self,
        query: str,
        results: List[RetrievalResult],
        top_k: int = 5,
    ) -> List[RetrievalResult]:
        if not results:
            return []

        pairs = [
            (query, result.chunk.content)
            for result in results
        ]

        scores = self.model.predict(pairs)

        for result, score in zip(results, scores):
            result.reranker_score = float(score)

        results.sort(
            key=lambda result: result.reranker_score,
            reverse=True,
        )

        return results[:top_k]


reranker_service = RerankerService()