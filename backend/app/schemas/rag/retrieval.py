from typing import Optional

from pydantic import BaseModel


class RetrievalResult(BaseModel):
    chunk_id: int
    retrieval_score: float
    reranker_score: Optional[float] = None