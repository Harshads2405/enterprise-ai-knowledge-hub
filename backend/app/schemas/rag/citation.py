from typing import Optional

from pydantic import BaseModel


class Citation(BaseModel):
    document_id: int
    chunk_id: int
    chunk_index: int
    source_name: str
    page: Optional[int] = None
    retrieval_score: float
    reranker_score: Optional[float] = None