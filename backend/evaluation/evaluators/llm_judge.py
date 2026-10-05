import json
from typing import Dict

from app.services.llm.groq_client import groq_client


class LLMJudgeError(Exception):
    """Raised when the LLM judge cannot produce a valid evaluation."""


class LLMJudge:
    def evaluate_answer(
        self,
        question: str,
        expected_answer: str,
        generated_answer: str,
    ) -> Dict:
        prompt = f"""
You are an evaluation judge for an enterprise RAG system.

Evaluate the generated answer against the reference answer.

Question:
{question}

Reference answer:
{expected_answer}

Generated answer:
{generated_answer}

Score the generated answer using integers from 1 to 5:

1 = Completely incorrect
2 = Mostly incorrect
3 = Partially correct
4 = Mostly correct
5 = Fully correct

Evaluate:

- answer_correctness: Does the generated answer contain the information
  required by the reference answer?
- answer_relevance: Does the generated answer directly answer the question?

Return ONLY valid JSON with exactly this structure:

{{
  "answer_correctness": 1,
  "answer_relevance": 1,
  "reason": "Brief explanation"
}}

Do not include markdown.
Do not include code fences.
Do not add any other fields.
"""

        raw_response = groq_client.chat(prompt)

        try:
            result = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            raise LLMJudgeError(
                f"LLM judge returned invalid JSON: {raw_response}"
            ) from exc

        required_fields = {
            "answer_correctness",
            "answer_relevance",
            "reason",
        }

        if set(result.keys()) != required_fields:
            raise LLMJudgeError(
                "LLM judge returned an unexpected response structure."
            )

        for field in (
            "answer_correctness",
            "answer_relevance",
        ):
            score = result[field]

            if (
                not isinstance(score, int)
                or isinstance(score, bool)
                or score < 1
                or score > 5
            ):
                raise LLMJudgeError(
                    f"Invalid {field} score: {score}"
                )

        if not isinstance(result["reason"], str):
            raise LLMJudgeError(
                "LLM judge reason must be a string."
            )

        return result


llm_judge = LLMJudge()