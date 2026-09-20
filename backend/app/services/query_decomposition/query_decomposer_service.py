
import json
from typing import List

from app.services.llm.groq_client import groq_client


class QueryDecomposerService:

    def decompose(
        self,
        query: str,
        max_queries: int = 3,
    ) -> List[str]:

        if not query.strip():
            return []

        if max_queries <= 0:
            raise ValueError("max_queries must be greater than 0")

        max_queries = min(max_queries, 3)

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

Examples:

Query:
"What approval requirements apply to remote work, travel, and expenses?"

Good:
{{
  "queries": [
    "remote work approval requirements",
    "business travel approval requirements",
    "business expense approval requirements"
  ]
}}

Important:
The original query explicitly contains three topics:
1. remote work
2. travel
3. expenses

All three topics must be represented.

Query:
"How should employees submit business expense claims?"

Good:
{{
  "queries": [
    "business expense claim submission process"
  ]
}}

Query:
"What should employees submit with their request?"

Good:
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

        response = groq_client.chat(prompt).strip()

        try:
            data = json.loads(response)
        except Exception:
            return [query]

        queries = data.get("queries", [])

        if not isinstance(queries, list):
            return [query]

        unique_queries = []
        seen = set()

        for item in queries:
            if not isinstance(item, str):
                continue

            cleaned = item.strip()

            if not cleaned:
                continue

            normalized = cleaned.lower()

            if normalized in seen:
                continue

            seen.add(normalized)
            unique_queries.append(cleaned)

        if not unique_queries:
            return [query]

        return unique_queries[:max_queries]


query_decomposer_service = QueryDecomposerService()
