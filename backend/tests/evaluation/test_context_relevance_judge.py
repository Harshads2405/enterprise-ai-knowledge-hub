
import json
from unittest.mock import patch

import pytest

from evaluation.evaluators.context_relevance_judge import (
    ContextRelevanceJudge,
    ContextRelevanceJudgeError,
)


def test_evaluate_accepts_valid_response():
    response = {
        "context_relevance": 5,
        "reason": "The context directly addresses the question.",
    }

    with patch(
        "evaluation.evaluators.context_relevance_judge.groq_client.chat",
        return_value=json.dumps(response),
    ):
        result = ContextRelevanceJudge().evaluate(
            question="Who approves annual leave?",
            retrieved_context="Managers must approve annual leave requests.",
        )

    assert result["context_relevance"] == 5
    assert result["reason"] == response["reason"]


def test_evaluate_rejects_invalid_json():
    with patch(
        "evaluation.evaluators.context_relevance_judge.groq_client.chat",
        return_value="not valid json",
    ):
        with pytest.raises(ContextRelevanceJudgeError):
            ContextRelevanceJudge().evaluate(
                question="Who approves annual leave?",
                retrieved_context="Managers must approve annual leave requests.",
            )


@pytest.mark.parametrize(
    "score",
    [0, 6, True, "5", 3.5],
)
def test_evaluate_rejects_invalid_scores(score):
    response = {
        "context_relevance": score,
        "reason": "Test reason.",
    }

    with patch(
        "evaluation.evaluators.context_relevance_judge.groq_client.chat",
        return_value=json.dumps(response),
    ):
        with pytest.raises(ContextRelevanceJudgeError):
            ContextRelevanceJudge().evaluate(
                question="Who approves annual leave?",
                retrieved_context="Managers must approve annual leave requests.",
            )


def test_evaluate_rejects_unexpected_fields():
    response = {
        "context_relevance": 5,
        "reason": "Relevant context.",
        "extra": "Unexpected",
    }

    with patch(
        "evaluation.evaluators.context_relevance_judge.groq_client.chat",
        return_value=json.dumps(response),
    ):
        with pytest.raises(ContextRelevanceJudgeError):
            ContextRelevanceJudge().evaluate(
                question="Who approves annual leave?",
                retrieved_context="Managers must approve annual leave requests.",
            )
