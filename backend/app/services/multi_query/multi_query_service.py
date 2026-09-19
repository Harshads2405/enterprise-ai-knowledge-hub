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
        Generate up to {num_queries} genuinely different search queries for an
        enterprise knowledge base.

        Original user query:
        {query}

        Purpose:
        Improve retrieval coverage by expressing the user's information need using
        different relevant search formulations.

        Rules:
        - Preserve the user's intent exactly.
        - Do not answer the question.
        - Do not invent facts, entities, departments, policies, causes, consequences,
          or specific business domains.
        - Preserve important terminology from the original query.
        - Preserve the meaning of must, must not, should, may, and required.
        - Do not merely replace words with synonyms.
        - Prefer different retrieval formulations based on the same information need.
        - One formulation may be phrased as a requirement.
        - One formulation may focus on required documentation or information to provide,
          when supported by the original query.
        - One formulation may focus on the relevant submission process or requirement,
          when supported by the original query.
        - Keep every query concise.
        - Do not introduce concepts that are not supported by the original query.
        - Return only valid JSON.

        For example, if the user asks:
        "What should employees submit with their request?"

        Good search formulations would resemble:
        - "employee request submission requirements"
        - "employee request required documentation"
        - "documents employees must provide with request"

        Bad formulations would:
        - introduce a specific request type not mentioned by the user
        - answer the question
        - invent a policy or department
        - merely replace "submit" with "include" or "provide"

        Expected JSON:
        {{
          "queries": [
            "query 1",
            "query 2",
            "query 3"
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
            if item and item.strip()
        ]

        unique_queries = []
        seen = set()

        original_normalized = query.strip().lower()

        for item in queries:
            normalized = item.lower()

            if normalized == original_normalized:
                continue

            if normalized in seen:
                continue

            if not self._is_valid_variant(query, item):
                continue

            seen.add(normalized)
            unique_queries.append(item)

        if not unique_queries:
            return [query]

        return unique_queries[:num_queries]

    def _is_valid_variant(
            self,
            original_query: str,
            generated_query: str,
    ) -> bool:
        original = original_query.lower()
        generated = generated_query.lower()

        # Prevent "what should..." questions from becoming
        # "how to..." / process questions.
        if (
                original.startswith("what")
                and any(
            term in generated
            for term in [
                "steps for",
                "how to",
                "process for",
                "procedure for",
                "process of",
            ]
        )
        ):
            return False

        return True



multi_query_service = MultiQueryService()