from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from langchain_core.tools import tool

from app.services.retrieval.retrieval_pipeline import (
    retrieval_pipeline,
)


@tool
def search_knowledge_base(
    query: str,
    limit: int = 3,
    department: Optional[str] = None,
    document_type: Optional[str] = None,
    version: Optional[str] = None,
    access_level: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Search the enterprise knowledge base for relevant internal documents.

    Use this tool when answering a question requires information from
    the enterprise knowledge base.
    """

    if not query or not query.strip():
        raise ValueError(
            "Knowledge-base search query cannot be empty."
        )

    if limit < 1:
        raise ValueError(
            "Knowledge-base search limit must be at least 1."
        )

    results = retrieval_pipeline.retrieve(
        search_queries=[query],
        limit=limit,
        department=department,
        document_type=document_type,
        version=version,
        access_level=access_level,
    )

    documents = []

    for result in results:
        chunk = result.chunk

        metadata = {
            "document_id": chunk.document_id,
            "chunk_id": chunk.id,
            "chunk_index": chunk.chunk_index,
            "retrieval_score": result.retrieval_score,
            "reranker_score": result.reranker_score,
            **chunk.chunk_metadata,
        }

        if chunk.document:
            metadata["source_name"] = chunk.document.source_name
            metadata["document_title"] = chunk.document.title

        documents.append(
            {
                "content": (
                    result.compressed_content
                    or chunk.content
                ),
                "metadata": metadata,
            }
        )

    return documents


@dataclass(frozen=True)
class AgentToolMetadata:
    requires_confirmation: bool = False


SEARCH_KNOWLEDGE_BASE_METADATA = AgentToolMetadata(
    requires_confirmation=False,
)


AGENT_TOOLS = [
    search_knowledge_base,
]

AGENT_TOOL_METADATA = {
    search_knowledge_base.name: SEARCH_KNOWLEDGE_BASE_METADATA,
}
