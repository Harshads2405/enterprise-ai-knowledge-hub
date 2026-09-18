from dataclasses import dataclass
from typing import Optional

from app.models.document_chunk import DocumentChunk


@dataclass
class RetrievalResult:
    chunk: DocumentChunk
    retrieval_score: float
    reranker_score: Optional[float] = None
    compressed_content: Optional[str] = None