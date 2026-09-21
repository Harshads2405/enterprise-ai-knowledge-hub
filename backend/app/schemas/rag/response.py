from typing import List

from pydantic import BaseModel, Field

from app.schemas.rag.citation import Citation


class ClarificationOption(BaseModel):
    label: str
    topic: str


class RAGResponse(BaseModel):
    answer: str
    sources: List[Citation]

    should_clarify: bool = False
    clarification_question: str = ""
    clarification_options: List[ClarificationOption] = Field(
        default_factory=list
    )