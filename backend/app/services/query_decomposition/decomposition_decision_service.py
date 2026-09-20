import re


class DecompositionDecisionService:

    def should_decompose(self, query: str) -> bool:
        if not query or not query.strip():
            return False

        normalized_query = " ".join(query.lower().split())

        # Explicit multi-topic patterns.
        #
        # Examples:
        # "remote work, travel, and expenses"
        # "remote work and travel"
        # "leave, attendance, and remote work"
        #
        # We only use this as a cheap pre-check.
        conjunction_pattern = r"\b(and|as well as|along with)\b"

        has_conjunction = bool(
            re.search(conjunction_pattern, normalized_query)
        )

        has_multiple_items = "," in normalized_query

        return has_conjunction and (
            has_multiple_items
            or self._contains_multiple_topics(normalized_query)
        )

    def _contains_multiple_topics(self, query: str) -> bool:
        topic_groups = [
            (
                "remote work",
                "travel",
                "expense",
                "expenses",
                "leave",
                "attendance",
            ),
            (
                "security",
                "access",
                "incident",
                "incidents",
            ),
        ]

        matched_topic_groups = 0

        for group in topic_groups:
            matches = sum(
                1
                for topic in group
                if topic in query
            )

            if matches >= 2:
                matched_topic_groups += 1

        return matched_topic_groups > 0


decomposition_decision_service = DecompositionDecisionService()
