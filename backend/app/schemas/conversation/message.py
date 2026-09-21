from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ConversationMessageRequest(BaseModel):
    conversation_id: int
    content: str = Field(min_length=1)
    organization_id: int
    user_id: int


class ConversationMessageResponse(BaseModel):
    message_id: int
    conversation_id: int
    role: str
    content: str
    metadata: Dict[str, Any] = Field(
        default_factory=dict
    )


class ClarificationState(BaseModel):
    pending: bool = False
    original_query: Optional[str] = None
    options: List[Dict[str, str]] = Field(
        default_factory=list
    )