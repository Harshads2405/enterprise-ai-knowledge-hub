from dataclasses import dataclass
from typing import List, Optional, Tuple

from app.services.ambiguity.ambiguity_analysis_service import (
    AmbiguityAnalysis,
)
from app.services.ambiguity.responsibility_ambiguity_service import (
    responsibility_ambiguity_service,
)
from app.services.retrieval.retrieval_result import RetrievalResult


@dataclass
class ClarificationOption:
    label: str
    topic: str


@dataclass
class ClarificationResponse:
    should_clarify: bool
    question: str = ""
    options: List[ClarificationOption] = None

    def __post_init__(self):
        if self.options is None:
            self.options = []


class ClarificationService:

    def build_clarification(
        self,
        query: str,
        analysis: AmbiguityAnalysis,
        results: Optional[List[RetrievalResult]] = None,
    ) -> ClarificationResponse:

        if not analysis.is_ambiguous:
            return ClarificationResponse(
                should_clarify=False,
            )

        results = results or []

        responsibility_response = (
            self._build_responsibility_clarification(
                query=query,
                results=results,
            )
        )

        if responsibility_response is not None:
            return responsibility_response

        candidate_topics = (
            self._extract_candidate_topics(
                query=query,
                analysis=analysis,
                results=results,
            )
        )

        if not candidate_topics:
            return ClarificationResponse(
                should_clarify=True,
                question=(
                    "Could you provide a little more detail "
                    "about what you mean?"
                ),
            )

        options = [
            ClarificationOption(
                label=label,
                topic=topic,
            )
            for topic, label in candidate_topics
        ]

        return ClarificationResponse(
            should_clarify=True,
            question=self._build_question(
                candidate_topics
            ),
            options=options,
        )

    # ------------------------------------------------------------------
    # Responsibility ambiguity
    # ------------------------------------------------------------------

    def _build_responsibility_clarification(
        self,
        query: str,
        results: List[RetrievalResult],
    ) -> Optional[ClarificationResponse]:

        responsibility_result = (
            responsibility_ambiguity_service
            .analyze_with_results(
                query=query,
                results=results,
            )
        )

        if not responsibility_result.is_ambiguous:
            return None

        options = []

        if "security" in responsibility_result.matched_topics:

            evidence = self._collect_security_evidence(
                results
            )

            if self._contains_reporting_evidence(
                evidence
            ):
                options.append(
                    ClarificationOption(
                        label=(
                            "reporting a security incident"
                        ),
                        topic=(
                            "security incident reporting"
                        ),
                    )
                )

            if self._contains_investigation_evidence(
                evidence
            ):
                options.append(
                    ClarificationOption(
                        label=(
                            "investigating a security incident"
                        ),
                        topic=(
                            "security incident investigation"
                        ),
                    )
                )

        if not options:
            return ClarificationResponse(
                should_clarify=True,
                question=(
                    "Could you clarify which "
                    "responsibility you mean?"
                ),
            )

        if len(options) == 2:

            question = (
                "Could you clarify which "
                "security-related responsibility "
                "you mean: "
                f"{options[0].label} or "
                f"{options[1].label}?"
            )

        else:

            question = (
                "Could you clarify which "
                "security-related responsibility "
                f"you mean: {options[0].label}?"
            )

        return ClarificationResponse(
            should_clarify=True,
            question=question,
            options=options,
        )

    def _collect_security_evidence(
        self,
        results: List[RetrievalResult],
    ) -> str:

        evidence = []

        for result in results:

            content = result.chunk.content

            if not content:
                continue

            normalized_content = content.lower()

            if any(
                phrase in normalized_content
                for phrase in [
                    "security incident",
                    "security incidents",
                    "unauthorized access",
                    "data exposure",
                    "malware",
                    "compromised account",
                ]
            ):
                evidence.append(
                    normalized_content
                )

        return " ".join(evidence)

    def _contains_reporting_evidence(
        self,
        evidence: str,
    ) -> bool:

        return (
            "employees must report" in evidence
            or "employees should report" in evidence
            or "employees report" in evidence
            or "report suspected security incidents"
            in evidence
        )

    def _contains_investigation_evidence(
        self,
        evidence: str,
    ) -> bool:

        return (
            "it security team is responsible for "
            "investigating"
            in evidence
            or "it security investigates" in evidence
            or "security team investigates" in evidence
        )

    # ------------------------------------------------------------------
    # Generic ambiguity
    # ------------------------------------------------------------------

    def _extract_candidate_topics(
        self,
        query: str,
        analysis: AmbiguityAnalysis,
        results: List[RetrievalResult],
    ) -> List[Tuple[str, str]]:

        candidates = []

        # --------------------------------------------------------------
        # 1. Explicit candidate topics from ambiguity analysis
        # --------------------------------------------------------------

        for topic in analysis.candidate_topics:

            normalized_topic = (
                topic.lower().strip()
            )

            mapping = {
                "expense claim": (
                    "expense claim",
                    "an expense claim",
                ),
                "reimbursement": (
                    "reimbursement request",
                    "a reimbursement request",
                ),
                "remote work": (
                    "remote work",
                    "remote work",
                ),
                "business travel": (
                    "business travel",
                    "business travel",
                ),
                "leave": (
                    "leave",
                    "leave",
                ),
                "attendance": (
                    "attendance",
                    "attendance",
                ),
            }

            if normalized_topic in mapping:
                candidates.append(
                    mapping[normalized_topic]
                )

        # --------------------------------------------------------------
        # 2. Evidence-driven interpretation detection
        # --------------------------------------------------------------

        evidence_candidates = (
            self._extract_evidence_candidates(
                query=query,
                results=results,
            )
        )

        candidates.extend(
            evidence_candidates
        )

        return self._deduplicate_candidates(
            candidates
        )

    def _extract_evidence_candidates(
        self,
        query: str,
        results: List[RetrievalResult],
    ) -> List[Tuple[str, str]]:

        candidates = []

        query_lower = query.lower()

        # This interpretation is specifically about
        # what must accompany a submitted request.
        submission_question = (
            "submit" in query_lower
            and (
                "with" in query_lower
                or "include" in query_lower
                or "provide" in query_lower
            )
        )

        if not submission_question:
            return candidates

        for result in results:

            content = result.chunk.content

            if not content:
                continue

            normalized_content = (
                content.lower()
            )

            # ----------------------------------------------------------
            # Expense claim evidence
            # ----------------------------------------------------------

            if (
                "expense claim" in normalized_content
                and (
                    "receipt" in normalized_content
                    or "supporting documentation"
                    in normalized_content
                )
            ):
                candidates.append(
                    (
                        "expense claim",
                        "an expense claim",
                    )
                )

            # ----------------------------------------------------------
            # Reimbursement evidence
            # ----------------------------------------------------------

            if (
                "reimbursement request"
                in normalized_content
                and (
                    "receipt" in normalized_content
                    or "supporting document"
                    in normalized_content
                )
            ):
                candidates.append(
                    (
                        "reimbursement request",
                        "a reimbursement request",
                    )
                )

        return candidates

    # ------------------------------------------------------------------
    # Question generation
    # ------------------------------------------------------------------

    def _build_question(
        self,
        candidates: List[Tuple[str, str]],
    ) -> str:

        labels = [
            label
            for _, label in candidates
        ]

        if len(labels) == 2:

            return (
                "Could you clarify which type of request "
                "you mean: "
                f"{labels[0]} or {labels[1]}?"
            )

        if len(labels) > 2:

            formatted = ", ".join(
                labels[:-1]
            )

            formatted += (
                f", or {labels[-1]}"
            )

            return (
                "Could you clarify which topic "
                f"you mean: {formatted}?"
            )

        return (
            "Could you clarify which topic "
            "you mean?"
        )

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def _deduplicate_candidates(
        self,
        candidates: List[Tuple[str, str]],
    ) -> List[Tuple[str, str]]:

        seen = set()
        result = []

        for topic, label in candidates:

            if topic in seen:
                continue

            seen.add(topic)

            result.append(
                (
                    topic,
                    label,
                )
            )

        return result


clarification_service = ClarificationService()