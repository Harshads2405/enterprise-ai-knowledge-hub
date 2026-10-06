import json
from typing import Dict

from app.services.llm.groq_client import groq_client


class FaithfulnessJudgeError(Exception):
    """Raised when the faithfulness judge cannot produce a valid evaluation."""


class FaithfulnessJudge:
    def evaluate(
        self,
        question: str,
        retrieved_context: str,
        generated_answer: str,
    ) -> Dict:
        prompt = f"""
You are an evaluation judge for an enterprise RAG system.

Evaluate whether the generated answer is fully supported by the
retrieved knowledge-base context.

Question:
{question}

Retrieved knowledge-base context:
{retrieved_context}

Generated answer:
{generated_answer}

Score faithfulness using integers from 1 to 5:

1 = Completely unsupported
2 = Mostly unsupported
3 = Partially supported
4 = Mostly supported
5 = Fully supported

Evaluate only whether the claims in the generated answer are supported
by the retrieved context.

Do NOT use outside knowledge.
Do NOT judge whether the answer is well-written.
Do NOT judge whether the answer matches an external reference answer.

Return ONLY valid JSON with exactly this structure:

{{
  "faithfulness": 1,
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
            raise FaithfulnessJudgeError(
                f"Faithfulness judge returned invalid JSON: {raw_response}"
            ) from exc

        required_fields = {
            "faithfulness",
            "reason",
        }

        if set(result.keys()) != required_fields:
            raise FaithfulnessJudgeError(
                "Faithfulness judge returned an unexpected response structure."
            )

        score = result["faithfulness"]

        if (
            not isinstance(score, int)
            or isinstance(score, bool)
            or score < 1
            or score > 5
        ):
            raise FaithfulnessJudgeError(
                f"Invalid faithfulness score: {score}"
            )

        if not isinstance(result["reason"], str):
            raise FaithfulnessJudgeError(
                "Faithfulness judge reason must be a string."
            )

        return result


faithfulness_judge = FaithfulnessJudge()