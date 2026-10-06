import pytest

from evaluation.evaluators.faithfulness_judge import (
    FaithfulnessJudge,
    FaithfulnessJudgeError,
)


def test_valid_faithfulness_result(monkeypatch):
    judge = FaithfulnessJudge()

    def mock_chat(prompt):
        return """
        {
          "faithfulness": 5,
          "reason": "The generated answer is fully supported by the retrieved context."
        }
        """

    monkeypatch.setattr(
        "evaluation.evaluators.faithfulness_judge.groq_client.chat",
        mock_chat,
    )

    result = judge.evaluate(
        question="How many annual leave days do employees get?",
        retrieved_context=(
            "Employees are entitled to 20 days of annual leave per year."
        ),
        generated_answer=(
            "Employees are entitled to 20 days of annual leave per year."
        ),
    )

    assert result["faithfulness"] == 5
    assert isinstance(result["reason"], str)


def test_invalid_json_raises_error(monkeypatch):
    judge = FaithfulnessJudge()

    def mock_chat(prompt):
        return "not valid json"

    monkeypatch.setattr(
        "evaluation.evaluators.faithfulness_judge.groq_client.chat",
        mock_chat,
    )

    with pytest.raises(FaithfulnessJudgeError):
        judge.evaluate(
            question="What is the leave policy?",
            retrieved_context="Employees receive annual leave.",
            generated_answer="Employees receive annual leave.",
        )


def test_invalid_score_raises_error(monkeypatch):
    judge = FaithfulnessJudge()

    def mock_chat(prompt):
        return """
        {
          "faithfulness": 6,
          "reason": "Invalid score."
        }
        """

    monkeypatch.setattr(
        "evaluation.evaluators.faithfulness_judge.groq_client.chat",
        mock_chat,
    )

    with pytest.raises(FaithfulnessJudgeError):
        judge.evaluate(
            question="What is the leave policy?",
            retrieved_context="Employees receive annual leave.",
            generated_answer="Employees receive annual leave.",
        )