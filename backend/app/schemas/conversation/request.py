from typing import Optional

from pydantic import BaseModel, Field


class ConversationCreateRequest(BaseModel):
    organization_id: int = Field(
        ...,
        gt=0,
        description="Organization that owns the conversation.",
    )

    user_id: int = Field(
        ...,
        gt=0,
        description="User who owns the conversation.",
    )

    title: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Optional conversation title.",
    )


class ConversationMessageRequest(BaseModel):
    content: str = Field(
        ...,
        min_length=1,
        description="User message.",
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