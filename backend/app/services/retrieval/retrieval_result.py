from dataclasses import dataclass, field
from typing import List, Optional

from app.models.document_chunk import DocumentChunk


@dataclass
class RetrievalResult:
    chunk: DocumentChunk
    retrieval_score: float
    reranker_score: Optional[float] = None
    compressed_content: Optional[str] = None

    # Retrieval evidence
    retrieval_queries: List[str] = field(default_factory=list)
    retrieval_ranks: List[int] = field(default_factory=list)
    retrieval_count: int = 1
    best_retrieval_rank: Optional[int] = None

    # Per-query reranking evidence
    reranker_scores: List[float] = field(default_factory=list)
    reranker_queries: List[str] = field(default_factory=list)
    best_reranker_score: Optional[float] = None
    best_reranker_query: Optional[str] = None