
from types import SimpleNamespace
from unittest.mock import MagicMock
from typing import Optional, Tuple

import pytest

from app.services.llm.groq_client import (
    GroqClient,
    LLMClientError,
)


def make_groq_response(
    content="Test response",
    prompt_tokens=12,
    completion_tokens=8,
):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content)
            )
        ],
        usage=SimpleNamespace(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        ),
    )


def make_client(monkeypatch):
    monkeypatch.setattr(
        "app.services.llm.groq_client.settings.llm_mode",
        "groq",
    )

    client = GroqClient()
    client.client = MagicMock()
    return client


def test_groq_client_records_token_usage(monkeypatch):
    client = make_client(monkeypatch)
    client.client.chat.completions.create.return_value = (
        make_groq_response()
    )

    result = client.chat("Test prompt")

    assert result == "Test response"
    metrics = client.last_request_metrics
    assert metrics is not None
    assert metrics.model == client.DEFAULT_MODEL
    assert metrics.prompt_tokens == 12
    assert metrics.completion_tokens == 8
    assert metrics.total_tokens == 20
    assert metrics.latency_ms >= 0
    assert metrics.success is True


def test_groq_client_records_failed_request(monkeypatch):
    client = make_client(monkeypatch)
    client.client.chat.completions.create.side_effect = (
        RuntimeError("simulated provider failure")
    )

    with pytest.raises(LLMClientError):
        client.chat("Test prompt")

    metrics = client.last_request_metrics
    assert metrics is not None
    assert metrics.success is False
    assert metrics.error_type == "RuntimeError"
    assert metrics.latency_ms >= 0


def test_groq_client_rejects_empty_message(monkeypatch):
    client = make_client(monkeypatch)

    with pytest.raises(
        LLMClientError,
        match="cannot be empty",
    ):
        client.chat("")

    client.client.chat.completions.create.assert_not_called()


def test_groq_client_rejects_empty_provider_response(monkeypatch):
    client = make_client(monkeypatch)
    client.client.chat.completions.create.return_value = (
        make_groq_response(content="")
    )

    with pytest.raises(
        LLMClientError,
        match="empty response",
    ):
        client.chat("Test prompt")

    # The provider call succeeded, but the content was unusable.
    metrics = client.last_request_metrics
    assert metrics is not None
    assert metrics.success is True


def test_groq_client_mock_mode_records_metrics(monkeypatch):
    monkeypatch.setattr(
        "app.services.llm.groq_client.settings.llm_mode",
        "mock",
    )

    client = GroqClient()
    client.client = MagicMock()

    result = client.chat("Test prompt")

    assert "[MOCK LLM RESPONSE]" in result

    metrics = client.last_request_metrics
    assert metrics is not None
    assert metrics.model == "mock"
    assert metrics.latency_ms >= 0
    assert metrics.success is True

    client.client.chat.completions.create.assert_not_called()
