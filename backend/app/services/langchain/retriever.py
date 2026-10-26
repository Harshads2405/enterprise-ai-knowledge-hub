from typing import List, Optional

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import Field, StrictInt

from app.core.organization import validate_organization_id
from app.services.retrieval.retrieval_pipeline import (
    retrieval_pipeline,
)


class EnterpriseRetriever(BaseRetriever):
    """LangChain adapter for the existing enterprise retrieval pipeline."""

    limit: int = 3
    organization_id: StrictInt = Field(gt=0)
    candidate_limit: Optional[int] = None
    department: Optional[str] = None
    document_type: Optional[str] = None
    version: Optional[str] = None
    access_level: Optional[str] = None

    def __init__(self, **data):
        validate_organization_id(data.get("organization_id"))
        super().__init__(**data)

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager=None,
    ) -> List[Document]:

        results = retrieval_pipeline.retrieve(
            search_queries=[query],
            organization_id=self.organization_id,
            limit=self.limit,
            candidate_limit=self.candidate_limit,
            department=self.department,
            document_type=self.document_type,
            version=self.version,
            access_level=self.access_level,
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
                metadata["source_name"] = (
                    chunk.document.source_name
                )
                metadata["document_title"] = (
                    chunk.document.title
                )

            documents.append(
                Document(
                    page_content=(
                        result.compressed_content
                        or chunk.content
                    ),
                    metadata=metadata,
                )
            )

        return documents
