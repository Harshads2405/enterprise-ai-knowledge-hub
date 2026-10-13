
import json
from typing import Dict

from app.services.llm.groq_client import groq_client


class ContextRelevanceJudgeError(Exception):
    """Raised when the context relevance judge cannot produce a valid evaluation."""


class ContextRelevanceJudge:
    def evaluate(
        self,
        question: str,
        retrieved_context: str,
    ) -> Dict:
        prompt = f"""
You are an evaluation judge for an enterprise RAG system.

Evaluate how relevant the retrieved knowledge-base context is to answering
the user's question.

User question:
{question}

Retrieved knowledge-base context:
{retrieved_context}

Score context relevance using integers from 1 to 5:

1 = Irrelevant: the context does not help answer the question.
2 = Mostly irrelevant: only a small portion is related.
3 = Partially relevant: some useful information is present, but important
    information is missing or much of the context is unrelated.
4 = Mostly relevant: the context substantially helps answer the question,
    with minor gaps or some unnecessary information.
5 = Highly relevant: the context directly and substantially supports
    answering the question.

Evaluate only the relevance of the retrieved context to the question.
Do NOT evaluate a generated answer.
Do NOT use outside knowledge.
Do NOT reward context merely for sharing keywords with the question.

Return ONLY valid JSON with exactly this structure:

{{
    "context_relevance": 1,
    "reason": "Brief explanation"
}}

Do not include markdown, code fences, or additional fields.
"""

        raw_response = groq_client.chat(prompt)

        try:
            result = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            raise ContextRelevanceJudgeError(
                f"Context relevance judge returned invalid JSON: {raw_response}"
            ) from exc

        if not isinstance(result, dict):
            raise ContextRelevanceJudgeError(
                "Context relevance judge must return a JSON object."
            )

        required_fields = {"context_relevance", "reason"}

        if set(result.keys()) != required_fields:
            raise ContextRelevanceJudgeError(
                "Context relevance judge returned an unexpected response structure."
            )

        score = result["context_relevance"]

        if (
            not isinstance(score, int)
            or isinstance(score, bool)
            or not 1 <= score <= 5
        ):
            raise ContextRelevanceJudgeError(
                f"Invalid context relevance score: {score}"
            )

        if not isinstance(result["reason"], str):
            raise ContextRelevanceJudgeError(
                "Context relevance judge reason must be a string."
            )

        return result


context_relevance_judge = ContextRelevanceJudge()