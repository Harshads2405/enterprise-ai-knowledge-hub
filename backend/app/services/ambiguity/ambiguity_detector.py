import re
from dataclasses import dataclass
from typing import List


@dataclass
class AmbiguityResult:
    is_ambiguous: bool
    reason: str = ""
    candidate_topics: List[str] = None

    def __post_init__(self):
        if self.candidate_topics is None:
            self.candidate_topics = []


class AmbiguityDetector:

    def detect(self, query: str) -> AmbiguityResult:
        if not query or not query.strip():
            return AmbiguityResult(
                is_ambiguous=False,
            )

        normalized_query = " ".join(query.lower().split())

        candidate_topics = self._find_candidate_topics(
            normalized_query
        )

        if self._has_unresolved_reference(normalized_query):
            if len(candidate_topics) > 1:
                return AmbiguityResult(
                    is_ambiguous=True,
                    reason=(
                        "The query contains an unresolved reference "
                        "that may refer to multiple knowledge-base topics."
                    ),
                    candidate_topics=candidate_topics,
                )

        return AmbiguityResult(
            is_ambiguous=False,
            candidate_topics=candidate_topics,
        )

    def has_explicit_topic(self, query: str) -> bool:
        """
        Determine whether the query explicitly identifies
        at least one known knowledge-base topic.

        This method is intentionally separate from detect().
        A query can have an explicit topic and still be ambiguous.

        Example:
            "Who is responsible for security-related issues?"

        The topic "security" is explicit, but the specific
        responsibility is still unresolved.
        """

        if not query or not query.strip():
            return False

        normalized_query = " ".join(query.lower().split())

        candidate_topics = self._find_candidate_topics(
            normalized_query
        )

        return len(candidate_topics) > 0

    def _has_unresolved_reference(self, query: str) -> bool:
        ambiguous_references = [
            r"\btheir request\b",
            r"\bthe request\b",
            r"\bthis request\b",
            r"\bthat request\b",
            r"\bthe form\b",
            r"\bthis form\b",
            r"\bthat form\b",
            r"\bthe policy\b",
            r"\bthis policy\b",
            r"\bthat policy\b",
        ]

        return any(
            re.search(pattern, query)
            for pattern in ambiguous_references
        )

    def _find_candidate_topics(
        self,
        query: str,
    ) -> List[str]:

        topic_patterns = {
            "expense claim": [
                r"\bexpense\b",
                r"\bexpenses\b",
                r"\bexpense claim\b",
                r"\bexpense claims\b",
            ],
            "reimbursement": [
                r"\breimbursement\b",
                r"\breimburse\b",
            ],
            "remote work": [
                r"\bremote work\b",
                r"\bwork remotely\b",
            ],
            "business travel": [
                r"\btravel\b",
                r"\bbusiness travel\b",
            ],
            "leave": [
                r"\bleave\b",
                r"\bannual leave\b",
            ],
            "attendance": [
                r"\battendance\b",
                r"\battend work\b",
            ],
            "security": [
                r"\bsecurity\b",
                r"\bsecurity incident\b",
            ],
            "access control": [
                r"\baccess\b",
                r"\baccess control\b",
                r"\bunauthorized access\b",
            ],
        }

        matches = []

        for topic, patterns in topic_patterns.items():
            if any(
                re.search(pattern, query)
                for pattern in patterns
            ):
                matches.append(topic)

        return matches


ambiguity_detector = AmbiguityDetector()