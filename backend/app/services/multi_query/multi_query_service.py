import json
from typing import List

from app.schemas.rag.multi_query import MultiQueryResponse
from app.services.llm.groq_client import groq_client


class MultiQueryService:
    def generate(
        self,
        query: str,
        num_queries: int = 3,
    ) -> List[str]:
        if not query.strip():
            return []

        if num_queries <= 0:
            raise ValueError("num_queries must be greater than 0")

        num_queries = min(num_queries, 3)

        prompt = f"""
Generate exactly {num_queries} alternative search queries
for an enterprise knowledge base.

Original user query:
{query}

Requirements:
- Keep exactly the same intent.
- Use different wording for every query.
- Do not copy the original query.
- Do not answer the question.
- Do not invent information.
- Keep queries short.
- Return ONLY valid JSON.
- Use exactly this format:

{{
  "queries": [
    "query one",
    "query two",
    "query three"
  ]
}}
"""

        response = groq_client.chat(prompt).strip()

        try:
            data = json.loads(response)
            parsed = MultiQueryResponse.model_validate(data)
        except Exception:
            return [query]

        queries = [
            item.strip()
            for item in parsed.queries
            if item.strip()
        ]

        unique_queries = []
        seen = set()

        for item in queries:
            normalized = item.lower()

            if normalized == query.strip().lower():
                continue

            if normalized not in seen:
                seen.add(normalized)
                unique_queries.append(item)

        if not unique_queries:
            return [query]

        return unique_queries[:num_queries]


multi_query_service = MultiQueryService()