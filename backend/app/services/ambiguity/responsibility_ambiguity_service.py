import re
from dataclasses import dataclass
from typing import List

from app.services.retrieval.retrieval_result import RetrievalResult


@dataclass
class ResponsibilityAmbiguityResult:
    is_ambiguous: bool
    matched_roles: List[str]
    matched_topics: List[str]
    reason: str = ""


class ResponsibilityAmbiguityService:
    def analyze(
        self,
        query: str,
    ) -> ResponsibilityAmbiguityResult:

        if not query or not query.strip():
            return ResponsibilityAmbiguityResult(
                is_ambiguous=False,
                matched_roles=[],
                matched_topics=[],
            )

        normalized_query = " ".join(query.lower().split())

        matched_topics = self._find_topics(normalized_query)

        if not self._is_responsibility_question(normalized_query):
            return ResponsibilityAmbiguityResult(
                is_ambiguous=False,
                matched_roles=[],
                matched_topics=matched_topics,
            )

        return ResponsibilityAmbiguityResult(
            is_ambiguous=False,
            matched_roles=[],
            matched_topics=matched_topics,
        )

    def analyze_with_results(
        self,
        query: str,
        results: List[RetrievalResult],
    ) -> ResponsibilityAmbiguityResult:

        if not query or not query.strip():
            return ResponsibilityAmbiguityResult(
                is_ambiguous=False,
                matched_roles=[],
                matched_topics=[],
            )

        normalized_query = " ".join(query.lower().split())

        matched_topics = self._find_topics(normalized_query)

        if not self._is_responsibility_question(normalized_query):
            return ResponsibilityAmbiguityResult(
                is_ambiguous=False,
                matched_roles=[],
                matched_topics=matched_topics,
            )

        if not results:
            return ResponsibilityAmbiguityResult(
                is_ambiguous=False,
                matched_roles=[],
                matched_topics=matched_topics,
            )

        relevant_evidence = self._select_relevant_evidence(
            matched_topics,
            results,
        )

        evidence_text = " ".join(
            content.lower()
            for content in relevant_evidence
        )

        matched_roles = self._find_roles_in_evidence(
            evidence_text
        )

        # ---------------------------------------------------------
        # Action-aware responsibility handling
        # ---------------------------------------------------------
        #
        # A query such as:
        #
        #   "Who investigates reported security incidents?"
        #
        # explicitly asks about the "investigates" responsibility.
        # Employees may also appear in the evidence because they
        # report incidents, but that does not make the query
        # ambiguous.
        #
        # A broader query such as:
        #
        #   "Who is responsible for security-related issues?"
        #
        # does not identify a specific responsibility. If multiple
        # actors have security-related responsibilities, clarification
        # is appropriate.
        # ---------------------------------------------------------

        responsibility_action = self._find_responsibility_action(
            normalized_query
        )

        if (
            "security" in matched_topics
            and len(matched_roles) >= 2
        ):

            if responsibility_action:
                return ResponsibilityAmbiguityResult(
                    is_ambiguous=False,
                    matched_roles=matched_roles,
                    matched_topics=matched_topics,
                )

            return ResponsibilityAmbiguityResult(
                is_ambiguous=True,
                matched_roles=matched_roles,
                matched_topics=matched_topics,
                reason=(
                    "The retrieved knowledge contains security-related "
                    "responsibilities assigned to multiple actors, and "
                    "the query does not identify a specific responsibility."
                ),
            )

        return ResponsibilityAmbiguityResult(
            is_ambiguous=False,
            matched_roles=matched_roles,
            matched_topics=matched_topics,
        )

    def _is_responsibility_question(
        self,
        query: str,
    ) -> bool:

        patterns = [
            r"\bwho is responsible\b",
            r"\bwho handles\b",
            r"\bwho manages\b",
            r"\bwho investigates\b",
            r"\bwho reviews\b",
            r"\bwho approves\b",
            r"\bwho should\b",
        ]

        return any(
            re.search(pattern, query)
            for pattern in patterns
        )

    def _find_responsibility_action(
        self,
        query: str,
    ) -> str:

        actions = [
            "investigates",
            "investigate",
            "reports",
            "report",
            "reviews",
            "review",
            "approves",
            "approve",
            "handles",
            "handle",
            "manages",
            "manage",
            "requests",
            "request",
            "provisions",
            "provision",
            "protects",
            "protect",
        ]

        for action in actions:
            if re.search(
                rf"\b{re.escape(action)}\b",
                query,
            ):
                return action

        return ""

    def _find_roles_in_evidence(
        self,
        evidence: str,
    ) -> List[str]:

        roles = []

        if re.search(
            r"\bemployees?\b",
            evidence,
        ):
            roles.append("employees")

        if re.search(
            r"\b(it security|security team)\b",
            evidence,
        ):
            roles.append("IT security team")

        if re.search(
            r"\bmanagers?\b",
            evidence,
        ):
            roles.append("managers")

        if re.search(
            r"\bfinance team\b",
            evidence,
        ):
            roles.append("finance team")

        if re.search(
            r"\bhr team\b",
            evidence,
        ):
            roles.append("HR team")

        return roles

    def _select_relevant_evidence(
        self,
        matched_topics: List[str],
        results: List[RetrievalResult],
    ) -> List[str]:

        selected = []

        for result in results:
            content = result.chunk.content

            if not content:
                continue

            normalized_content = content.lower()

            if "security" in matched_topics:
                if (
                    "security" in normalized_content
                    or "incident" in normalized_content
                    or "unauthorized access" in normalized_content
                    or "data exposure" in normalized_content
                    or "malware" in normalized_content
                    or "compromised account" in normalized_content
                ):
                    selected.append(content)

            elif "access" in matched_topics:
                if (
                    "access" in normalized_content
                    or "authorized" in normalized_content
                ):
                    selected.append(content)

            elif "expenses" in matched_topics:
                if (
                    "expense" in normalized_content
                    or "receipt" in normalized_content
                ):
                    selected.append(content)

            elif "reimbursement" in matched_topics:
                if (
                    "reimbursement" in normalized_content
                    or "reimbursed" in normalized_content
                ):
                    selected.append(content)

            elif "remote work" in matched_topics:
                if (
                    "remote" in normalized_content
                    or "manager approval" in normalized_content
                ):
                    selected.append(content)

            elif "travel" in matched_topics:
                if "travel" in normalized_content:
                    selected.append(content)

            elif "leave" in matched_topics:
                if "leave" in normalized_content:
                    selected.append(content)

        return selected

    def _find_topics(
        self,
        query: str,
    ) -> List[str]:

        topics = []

        if re.search(
            r"\bsecurity\b",
            query,
        ):
            topics.append("security")

        if re.search(
            r"\baccess\b",
            query,
        ):
            topics.append("access")

        if re.search(
            r"\bexpense\b|\bexpenses\b",
            query,
        ):
            topics.append("expenses")

        if re.search(
            r"\breimbursement\b",
            query,
        ):
            topics.append("reimbursement")

        if re.search(
            r"\bremote work\b|\bwork remotely\b",
            query,
        ):
            topics.append("remote work")

        if re.search(
            r"\btravel\b",
            query,
        ):
            topics.append("travel")

        if re.search(
            r"\bleave\b",
            query,
        ):
            topics.append("leave")

        return topics


responsibility_ambiguity_service = (
    ResponsibilityAmbiguityService()
)