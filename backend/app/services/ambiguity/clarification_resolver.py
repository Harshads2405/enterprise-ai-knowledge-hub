from dataclasses import dataclass


@dataclass
class ClarificationResolution:
    resolved_query: str
    selected_topic: str


class ClarificationResolver:

    def resolve(
        self,
        original_query: str,
        selected_topic: str,
    ) -> ClarificationResolution:

        if not original_query or not original_query.strip():
            raise ValueError(
                "Original query cannot be empty."
            )

        if not selected_topic or not selected_topic.strip():
            raise ValueError(
                "Selected topic cannot be empty."
            )

        normalized_query = (
            " ".join(
                original_query.split()
            )
            .strip()
        )

        normalized_topic = (
            " ".join(
                selected_topic.split()
            )
            .strip()
        )

        resolved_query = self._resolve_query(
            query=normalized_query,
            topic=normalized_topic,
        )

        return ClarificationResolution(
            resolved_query=resolved_query,
            selected_topic=normalized_topic,
        )

    def _resolve_query(
        self,
        query: str,
        topic: str,
    ) -> str:

        normalized_query = query.rstrip(
            " .?!"
        )

        topic_lower = topic.lower()

        # ----------------------------------------------------------
        # Request clarification
        # ----------------------------------------------------------

        if topic_lower == "reimbursement request":

            replacements = [
                (
                    "their request",
                    "their reimbursement request",
                ),
                (
                    "the request",
                    "the reimbursement request",
                ),
                (
                    "this request",
                    "this reimbursement request",
                ),
                (
                    "that request",
                    "that reimbursement request",
                ),
            ]

            for old, new in replacements:

                if old in normalized_query.lower():

                    start = (
                        normalized_query.lower()
                        .find(old)
                    )

                    end = start + len(old)

                    normalized_query = (
                        normalized_query[:start]
                        + new
                        + normalized_query[end:]
                    )

                    return (
                        normalized_query + "?"
                    )

            return (
                f"{normalized_query} "
                f"regarding {topic}?"
            )

        if topic_lower == "expense claim":

            replacements = [
                (
                    "their request",
                    "their expense claim",
                ),
                (
                    "the request",
                    "the expense claim",
                ),
                (
                    "this request",
                    "this expense claim",
                ),
                (
                    "that request",
                    "that expense claim",
                ),
            ]

            for old, new in replacements:

                if old in normalized_query.lower():

                    start = (
                        normalized_query.lower()
                        .find(old)
                    )

                    end = start + len(old)

                    normalized_query = (
                        normalized_query[:start]
                        + new
                        + normalized_query[end:]
                    )

                    return (
                        normalized_query + "?"
                    )

            return (
                f"{normalized_query} "
                f"regarding {topic}?"
            )

        # ----------------------------------------------------------
        # Security responsibility clarification
        # ----------------------------------------------------------

        if topic_lower == (
            "security incident reporting"
        ):

            if "responsible for" in normalized_query.lower():

                return (
                    "Who is responsible for "
                    "reporting a security incident?"
                )

            return (
                f"{normalized_query} "
                f"regarding {topic}?"
            )

        if topic_lower == (
            "security incident investigation"
        ):

            if "responsible for" in normalized_query.lower():

                return (
                    "Who is responsible for "
                    "investigating a security incident?"
                )

            return (
                f"{normalized_query} "
                f"regarding {topic}?"
            )

        # ----------------------------------------------------------
        # Generic fallback
        # ----------------------------------------------------------

        return (
            f"{normalized_query} "
            f"regarding {topic}?"
        )


clarification_resolver = ClarificationResolver()