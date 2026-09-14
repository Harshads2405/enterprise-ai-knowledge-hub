from pydantic import BaseModel, Field


class RAGQueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        description="Question to ask the enterprise knowledge base.",
    )

    limit: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of knowledge chunks to retrieve.",
    )