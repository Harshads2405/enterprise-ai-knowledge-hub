from typing import Optional

from pydantic import BaseModel, Field


class RAGQueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        description="Question to ask the enterprise knowledge base.",
    )

    limit: Optional[int] = Field(
        default=None,
        ge=1,
        le=20,
        description="Optional maximum number of knowledge chunks to retrieve.",
    )

    department: Optional[str] = Field(
        default=None,
        min_length=1,
        description="Optional department filter for knowledge retrieval.",
    )