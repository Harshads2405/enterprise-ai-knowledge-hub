from unittest.mock import patch

import pytest

from evaluation.evaluators.llm_judge import LLMJudge, LLMJudgeError


def test_llm_judge_returns_valid_scores():
    judge = LLMJudge()

    mock_response = """
    {
        "answer_correctness": 5,
        "answer_relevance": 4,
        "reason": "The answer correctly addresses the question."
    }
    """

    with patch(
        "evaluation.evaluators.llm_judge.groq_client.chat",
        return_value=mock_response,
    ):
        result = judge.evaluate_answer(
            question="What is the remote work policy?",
            expected_answer="Employees need manager approval before working remotely.",
            generated_answer="Employees must obtain manager approval before working remotely.",
        )

    assert result["answer_correctness"] == 5
    assert result["answer_relevance"] == 4
    assert isinstance(result["reason"], str)


def test_llm_judge_rejects_invalid_json():
    judge = LLMJudge()

    with patch(
        "evaluation.evaluators.llm_judge.groq_client.chat",
        return_value="not valid json",
    ):
        with pytest.raises(LLMJudgeError):
            judge.evaluate_answer(
                question="Test question",
                expected_answer="Expected answer",
                generated_answer="Generated answer",
            )


def test_llm_judge_rejects_invalid_score():
    judge = LLMJudge()

    mock_response = """
    {
        "answer_correctness": 6,
        "answer_relevance": 4,
        "reason": "Invalid score."
    }
    """

    with patch(
        "evaluation.evaluators.llm_judge.groq_client.chat",
        return_value=mock_response,
    ):
        with pytest.raises(LLMJudgeError):
            judge.evaluate_answer(
                question="Test question",
                expected_answer="Expected answer",
                generated_answer="Generated answer",
            )
