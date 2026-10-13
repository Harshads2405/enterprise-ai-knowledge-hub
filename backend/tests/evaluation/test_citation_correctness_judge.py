import pytest

from evaluation.evaluators.citation_correctness_judge import (
    CitationCorrectnessJudge,
    CitationCorrectnessJudgeError,
)


def test_valid_citation_correctness_result(monkeypatch):
    judge = CitationCorrectnessJudge()

    def mock_chat(prompt):
        return """
        {
          "citation_correctness": 5,
          "reason": "The cited source directly supports the claim."
        }
        """

    monkeypatch.setattr(
        "evaluation.evaluators.citation_correctness_judge.groq_client.chat",
        mock_chat,
    )

    result = judge.evaluate(
        question="How many annual leave days do employees get?",
        claim="Employees are entitled to 20 days of annual leave per year.",
        cited_source=(
            "Employees are entitled to 20 days of annual leave per year."
        ),
    )

    assert result["citation_correctness"] == 5
    assert isinstance(result["reason"], str)


def test_invalid_json_raises_error(monkeypatch):
    judge = CitationCorrectnessJudge()

    def mock_chat(prompt):
        return "not valid json"

    monkeypatch.setattr(
        "evaluation.evaluators.citation_correctness_judge.groq_client.chat",
        mock_chat,
    )

    with pytest.raises(CitationCorrectnessJudgeError):
        judge.evaluate(
            question="What is the leave policy?",
            claim="Employees receive annual leave.",
            cited_source="Employees receive annual leave.",
        )


def test_invalid_score_raises_error(monkeypatch):
    judge = CitationCorrectnessJudge()

    def mock_chat(prompt):
        return """
        {
          "citation_correctness": 6,
          "reason": "Invalid score."
        }
        """

    monkeypatch.setattr(
        "evaluation.evaluators.citation_correctness_judge.groq_client.chat",
        mock_chat,
    )

    with pytest.raises(CitationCorrectnessJudgeError):
        judge.evaluate(
            question="What is the leave policy?",
            claim="Employees receive annual leave.",
            cited_source="Employees receive annual leave.",
        )

