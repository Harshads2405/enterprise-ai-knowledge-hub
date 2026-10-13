import json
from typing import Dict

from app.services.llm.groq_client import groq_client


class CitationCorrectnessJudgeError(Exception):
    """Raised when the citation correctness judge cannot produce a valid evaluation."""


class CitationCorrectnessJudge:
    def evaluate(
        self,
        question: str,
        claim: str,
        cited_source: str,
    ) -> Dict:
        prompt = f"""
You are an evaluation judge for an enterprise RAG system.

Evaluate whether the cited source actually supports the specific claim
made in the generated answer.

Question:
{question}

Claim:
{claim}

Cited source:
{cited_source}

Score citation correctness using integers from 1 to 5:

1 = The source does not support the claim at all.
2 = The source provides very weak or indirect support.
3 = The source partially supports the claim.
4 = The source mostly supports the claim.
5 = The source directly and clearly supports the claim.

Evaluate ONLY whether the cited source supports the claim.

Do NOT use outside knowledge.
Do NOT use other retrieved sources.
Do NOT judge the overall answer.
Do NOT judge writing quality.

Return ONLY valid JSON with exactly this structure:

{{
  "citation_correctness": 1,
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
            raise CitationCorrectnessJudgeError(
                f"Citation correctness judge returned invalid JSON: {raw_response}"
            ) from exc

        required_fields = {
            "citation_correctness",
            "reason",
        }

        if set(result.keys()) != required_fields:
            raise CitationCorrectnessJudgeError(
                "Citation correctness judge returned an unexpected response structure."
            )

        score = result["citation_correctness"]

        if (
            not isinstance(score, int)
            or isinstance(score, bool)
            or score < 1
            or score > 5
        ):
            raise CitationCorrectnessJudgeError(
                f"Invalid citation_correctness score: {score}"
            )

        if not isinstance(result["reason"], str):
            raise CitationCorrectnessJudgeError(
                "Citation correctness judge reason must be a string."
            )

        return result


citation_correctness_judge = CitationCorrectnessJudge()