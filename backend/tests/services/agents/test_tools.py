import sys
from unittest.mock import MagicMock, patch

import pytest


retrieval_pipeline_module = MagicMock()
retrieval_pipeline_module.retrieval_pipeline = MagicMock()

sys.modules[
    "app.services.retrieval.retrieval_pipeline"
] = retrieval_pipeline_module

from app.services.agents.tools import (
    AGENT_TOOL_METADATA,
    search_knowledge_base,
)

def test_search_knowledge_base_is_langchain_tool():
    assert search_knowledge_base.name == "search_knowledge_base"
    assert search_knowledge_base.description
    assert search_knowledge_base.args_schema is not None


def test_search_knowledge_base_rejects_empty_query():
    with pytest.raises(
        ValueError,
        match="Knowledge-base search query cannot be empty.",
    ):
        search_knowledge_base.invoke(
            {
                "query": "",
            }
        )


def test_search_knowledge_base_rejects_invalid_limit():
    with pytest.raises(
        ValueError,
        match="Knowledge-base search limit must be at least 1.",
    ):
        search_knowledge_base.invoke(
            {
                "query": "employee leave policy",
                "limit": 0,
            }
        )


@patch(
    "app.services.agents.tools.retrieval_pipeline.retrieve"
)
def test_search_knowledge_base_delegates_to_retrieval_pipeline(
    mock_retrieve,
):
    mock_retrieve.return_value = []

    result = search_knowledge_base.invoke(
        {
            "query": "employee leave policy",
            "limit": 3,
            "department": "HR",
            "document_type": "policy",
            "version": "v1",
            "access_level": "internal",
        }
    )

    assert result == []

    mock_retrieve.assert_called_once_with(
        search_queries=["employee leave policy"],
        limit=3,
        department="HR",
        document_type="policy",
        version="v1",
        access_level="internal",
    )


def test_search_knowledge_base_is_read_only():
    metadata = AGENT_TOOL_METADATA[
        search_knowledge_base.name
    ]

    assert metadata.requires_confirmation is False
