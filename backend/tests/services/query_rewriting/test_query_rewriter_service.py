
from unittest.mock import Mock

import pytest

from app.services.query_rewriting.query_rewriter_service import (
    QueryRewriterService,
)
from app.services.llm.groq_client import LLMClientError


@pytest.fixture
def rewriter(monkeypatch):
    monkeypatch.setattr(
        "app.services.query_rewriting.query_rewriter_service.settings.llm_mode",
        "groq",
    )
    return QueryRewriterService()


def test_rewrite_returns_groq_result(rewriter, monkeypatch):
    monkeypatch.setattr(
        "app.services.query_rewriting.query_rewriter_service.groq_client.chat",
        Mock(return_value="annual leave policy"),
    )

    assert rewriter.rewrite("What is the annual leave policy?") == (
        "annual leave policy"
    )


def test_rewrite_falls_back_on_llm_error(rewriter, monkeypatch):
    monkeypatch.setattr(
        "app.services.query_rewriting.query_rewriter_service.groq_client.chat",
        Mock(side_effect=LLMClientError("Groq returned an empty response.")),
    )

    query = "What is the annual leave policy?"

    assert rewriter.rewrite(query) == query


def test_rewrite_falls_back_on_blank_result(rewriter, monkeypatch):
    monkeypatch.setattr(
        "app.services.query_rewriting.query_rewriter_service.groq_client.chat",
        Mock(return_value="   "),
    )

    query = "What is the annual leave policy?"

    assert rewriter.rewrite(query) == query


def test_rewrite_preserves_query_in_mock_mode(rewriter, monkeypatch):
    monkeypatch.setattr(
        "app.services.query_rewriting.query_rewriter_service.settings.llm_mode",
        "mock",
    )

    query = "  What is the annual leave policy?  "

    assert rewriter.rewrite(query) == query.strip()
