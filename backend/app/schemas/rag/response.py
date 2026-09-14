from typing import List

from pydantic import BaseModel

from app.schemas.rag.citation import Citation


class RAGResponse(BaseModel):
    answer: str
    sources: List[Citation]