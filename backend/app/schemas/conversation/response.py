from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, Field

from app.schemas.rag.citation import Citation


class ConversationResponse(BaseModel):
    id: int
    organization_id: int
    user_id: int
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationMessageResponse(BaseModel):
    message_id: int
    conversation_id: int
    role: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationMessagesResponse(BaseModel):
    conversation_id: int
    messages: List[ConversationMessageResponse] = Field(
        default_factory=list
    )


class ConversationRAGResponse(BaseModel):
    message_id: int
    conversation_id: int
    role: str = "assistant"
    answer: str
    sources: List[Citation] = Field(default_factory=list)

    should_clarify: bool = False
    clarification_question: str = ""
    clarification_options: List[Dict[str, str]] = Field(
        default_factory=list
    )

    metadata: Dict[str, Any] = Field(default_factory=dict)