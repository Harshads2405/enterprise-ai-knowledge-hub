from typing import List, Optional

from app.services.retrieval.retrieval_pipeline import (
    retrieval_pipeline,
)
from app.services.retrieval.retrieval_result import RetrievalResult


class RetrievalAmbiguityService:

    def retrieve_candidates(
        self,
        query: str,
        department: Optional[str] = None,
        candidate_limit: int = 10,
    ) -> List[RetrievalResult]:

        if not query or not query.strip():
            return []

        return retrieval_pipeline.retrieve(
            search_queries=[query],
            limit=candidate_limit,
            department=department,
        )


retrieval_ambiguity_service = RetrievalAmbiguityService()