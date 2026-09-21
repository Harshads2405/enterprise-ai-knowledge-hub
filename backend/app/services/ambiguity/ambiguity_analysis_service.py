from dataclasses import dataclass
from typing import List, Optional

from app.services.retrieval.retrieval_result import RetrievalResult
from app.services.ambiguity.ambiguity_detector import (
    ambiguity_detector,
)
from app.services.ambiguity.responsibility_ambiguity_service import (
    responsibility_ambiguity_service,
)


@dataclass
class AmbiguityAnalysis:
    is_ambiguous: bool
    reason: str
    strong_candidate_count: int
    distinct_document_count: int
    top_score: Optional[float]
    second_score: Optional[float]
    score_gap: Optional[float]
    candidate_topics: List[str]


class AmbiguityAnalysisService:

    def analyze(
        self,
        results: List[RetrievalResult],
        explicit_topic: bool = False,
        query: Optional[str] = None,
    ) -> AmbiguityAnalysis:

        # ---------------------------------------------------------
        # Determine candidate topics from the actual query.
        #
        # This is only a descriptive signal.
        # It does NOT determine ambiguity by itself.
        # ---------------------------------------------------------

        candidate_topics = []

        if query:
            detector_result = ambiguity_detector.detect(
                query
            )

            candidate_topics = (
                detector_result.candidate_topics
            )

        # ---------------------------------------------------------
        # No retrieval results
        # ---------------------------------------------------------

        if not results:
            return AmbiguityAnalysis(
                is_ambiguous=False,
                reason="No retrieval candidates were found.",
                strong_candidate_count=0,
                distinct_document_count=0,
                top_score=None,
                second_score=None,
                score_gap=None,
                candidate_topics=candidate_topics,
            )

        # ---------------------------------------------------------
        # Collect reranker scores
        # ---------------------------------------------------------

        scores = [
            result.best_reranker_score
            for result in results
            if result.best_reranker_score is not None
        ]

        scores.sort(reverse=True)

        top_score = (
            scores[0]
            if scores
            else None
        )

        second_score = (
            scores[1]
            if len(scores) > 1
            else None
        )

        score_gap = (
            top_score - second_score
            if (
                top_score is not None
                and second_score is not None
            )
            else None
        )

        # ---------------------------------------------------------
        # No reranker scores
        # ---------------------------------------------------------

        if top_score is None:
            return AmbiguityAnalysis(
                is_ambiguous=False,
                reason=(
                    "Retrieval candidates do not contain "
                    "reranker scores."
                ),
                strong_candidate_count=0,
                distinct_document_count=0,
                top_score=None,
                second_score=None,
                score_gap=None,
                candidate_topics=candidate_topics,
            )

        # ---------------------------------------------------------
        # Strong retrieval candidates
        #
        # Candidates within 2.0 points of the best reranker
        # score are considered strong evidence.
        # ---------------------------------------------------------

        strong_candidates = [
            result
            for result in results
            if (
                result.best_reranker_score is not None
                and result.best_reranker_score
                >= (top_score - 2.0)
            )
        ]

        document_ids = {
            result.chunk.document_id
            for result in strong_candidates
        }

        strong_candidate_count = len(
            strong_candidates
        )

        distinct_document_count = len(
            document_ids
        )

        # ---------------------------------------------------------
        # Retrieval-based ambiguity
        # ---------------------------------------------------------

        retrieval_ambiguous = (
            not explicit_topic
            and strong_candidate_count >= 2
            and distinct_document_count >= 2
            and score_gap is not None
            and score_gap < 2.0
        )

        # ---------------------------------------------------------
        # Responsibility-based ambiguity
        # ---------------------------------------------------------

        responsibility_ambiguous = False
        responsibility_result = None

        if query:

            responsibility_result = (
                responsibility_ambiguity_service
                .analyze_with_results(
                    query=query,
                    results=results,
                )
            )

            responsibility_ambiguous = (
                responsibility_result.is_ambiguous
            )

        # ---------------------------------------------------------
        # Final ambiguity decision
        #
        # Responsibility ambiguity has priority because it can
        # identify ambiguity even when the query contains an
        # explicit topic such as "security".
        # ---------------------------------------------------------

        if responsibility_ambiguous:

            is_ambiguous = True

            reason = (
                responsibility_result.reason
            )

        elif retrieval_ambiguous:

            is_ambiguous = True

            reason = (
                "Multiple knowledge-base documents have "
                "similarly strong relevance scores, and the "
                "query does not explicitly identify which "
                "topic the user means."
            )

        elif explicit_topic:

            is_ambiguous = False

            reason = (
                "The query explicitly identifies its topic, "
                "so multiple relevant documents are treated "
                "as supporting evidence rather than unresolved "
                "ambiguity."
            )

        else:

            is_ambiguous = False

            reason = (
                "Retrieval evidence is sufficiently concentrated "
                "on one interpretation."
            )

        # ---------------------------------------------------------
        # Final analysis
        # ---------------------------------------------------------

        return AmbiguityAnalysis(
            is_ambiguous=is_ambiguous,
            reason=reason,
            strong_candidate_count=strong_candidate_count,
            distinct_document_count=distinct_document_count,
            top_score=top_score,
            second_score=second_score,
            score_gap=score_gap,
            candidate_topics=candidate_topics,
        )


ambiguity_analysis_service = (
    AmbiguityAnalysisService()
)