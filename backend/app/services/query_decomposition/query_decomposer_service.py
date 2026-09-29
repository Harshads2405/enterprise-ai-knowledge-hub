import json
import re
from typing import List

from app.core.config import settings
from app.services.llm.groq_client import groq_client


class QueryDecomposerService:

    def decompose(
        self,
        query: str,
        max_queries: int = 3,
    ) -> List[str]:

        if not query or not query.strip():
            return []

        if max_queries <= 0:
            raise ValueError("max_queries must be greater than 0")

        max_queries = min(max_queries, 3)

        # ---------------------------------------------------------
        # 1. Use the real LLM only when explicitly enabled.
        # ---------------------------------------------------------
        if settings.llm_mode.lower() == "groq":

            llm_queries = self._decompose_with_llm(
                query=query,
                max_queries=max_queries,
            )

            if llm_queries:
                return llm_queries

        # ---------------------------------------------------------
        # 2. Deterministic fallback.
        #
        # Only decomposes queries where multiple topics are
        # explicitly present.
        # ---------------------------------------------------------
        deterministic_queries = self._deterministic_decompose(
            query=query,
            max_queries=max_queries,
        )

        if deterministic_queries:
            return deterministic_queries

        # ---------------------------------------------------------
        # 3. Preserve the original query.
        # ---------------------------------------------------------
        return [query.strip()]

    # =============================================================
    # LLM decomposition
    # =============================================================

    def _decompose_with_llm(
        self,
        query: str,
        max_queries: int,
    ) -> List[str]:

        prompt = f"""
Analyze the following user query for an enterprise knowledge base.

User query:
{query}

Your task is to identify distinct information needs contained explicitly
in the user's query.

Rules:
- Do not answer the question.
- Preserve the user's intent exactly.
- Preserve every explicit topic, entity, subject, or requirement.
- If the query explicitly mentions multiple topics, each topic must be
  represented by a separate search query.
- Do not drop, merge, or replace an explicit topic.
- Do not invent entities, departments, policies, causes, consequences,
  or business domains.
- Only create separate information needs when the original query explicitly
  contains multiple topics, entities, requirements, or actions.
- Do not split one simple information need into artificial sub-queries.
- Do not infer hidden topics.
- Preserve important terminology.
- Keep each information need concise and suitable for knowledge-base search.
- If the query contains only one information need, return one query.
- Return at most {max_queries} queries.
- Return only valid JSON.

Example:

Query:
"What approval requirements apply to remote work, travel, and expenses?"

Expected:
{{
  "queries": [
    "remote work approval requirements",
    "business travel approval requirements",
    "business expense approval requirements"
  ]
}}

Query:
"How should employees submit business expense claims?"

Expected:
{{
  "queries": [
    "business expense claim submission process"
  ]
}}

Query:
"What should employees submit with their request?"

Expected:
{{
  "queries": [
    "employee request submission requirements"
  ]
}}

Do not infer "expense" or "reimbursement" from the last example.

Expected JSON:
{{
  "queries": [
    "query 1"
  ]
}}
"""

        try:
            response = groq_client.chat(prompt).strip()
            data = json.loads(response)
        except Exception:
            return []

        queries = data.get("queries", [])

        if not isinstance(queries, list):
            return []

        return self._clean_queries(
            queries=queries,
            max_queries=max_queries,
        )

    # =============================================================
    # Deterministic decomposition
    # =============================================================

    def _deterministic_decompose(
        self,
        query: str,
        max_queries: int,
    ) -> List[str]:

        normalized = " ".join(query.lower().split())

        topic_patterns = [
            ("remote work", r"\bremote work\b"),
            ("travel", r"\btravel\b"),
            ("expenses", r"\bexpenses?\b"),
            ("leave", r"\bleave\b"),
            ("attendance", r"\battendance\b"),
            ("security", r"\bsecurity\b"),
            ("access", r"\baccess\b"),
            ("incidents", r"\bincidents?\b"),
        ]

        matched_topics = []

        for topic, pattern in topic_patterns:
            if re.search(pattern, normalized):
                matched_topics.append(topic)

        # Do not decompose a single-topic query.
        if len(matched_topics) < 2:
            return []

        # Require explicit multi-topic structure.
        has_conjunction = bool(
            re.search(
                r"\b(and|as well as|along with)\b",
                normalized,
            )
        )

        has_comma = "," in normalized

        if not (has_conjunction or has_comma):
            return []

        query_type = self._detect_query_type(normalized)

        decomposed = []

        for topic in matched_topics:

            if query_type == "approval":

                if topic == "travel":
                    search_query = "business travel approval requirements"

                elif topic == "expenses":
                    search_query = "business expense approval requirements"

                else:
                    search_query = f"{topic} approval requirements"

            elif query_type == "requirements":

                search_query = f"{topic} requirements"

            elif query_type == "responsibility":

                search_query = f"{topic} responsibilities"

            else:

                search_query = (
                    f"{topic} {self._search_suffix(normalized)}"
                )

            decomposed.append(search_query)

        return self._clean_queries(
            queries=decomposed,
            max_queries=max_queries,
        )

    # =============================================================
    # Query intent helpers
    # =============================================================

    def _detect_query_type(self, query: str) -> str:

        if "approval" in query or "approve" in query:
            return "approval"

        if "requirements" in query or "required" in query:
            return "requirements"

        if (
            "responsible" in query
            or "responsibility" in query
            or "who handles" in query
        ):
            return "responsibility"

        return "general"

    def _search_suffix(self, query: str) -> str:

        if "submit" in query:
            return "submission requirements"

        if "process" in query:
            return "process"

        if "policy" in query:
            return "policy"

        if "days" in query:
            return "policy"

        return "requirements"

    # =============================================================
    # Cleanup / validation
    # =============================================================

    def _clean_queries(
        self,
        queries: List[str],
        max_queries: int,
    ) -> List[str]:

        unique_queries = []
        seen = set()

        for item in queries:

            if not isinstance(item, str):
                continue

            cleaned = " ".join(item.strip().split())

            if not cleaned:
                continue

            normalized = cleaned.lower()

            if normalized in seen:
                continue

            seen.add(normalized)
            unique_queries.append(cleaned)

            if len(unique_queries) >= max_queries:
                break

        return unique_queries


query_decomposer_service = QueryDecomposerService()