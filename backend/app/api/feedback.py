
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.services.feedback_service import feedback_service


router = APIRouter(
    prefix="/api/v1/feedback",
    tags=["feedback"],
)


class FeedbackCreateRequest(BaseModel):
    message_id: int = Field(..., gt=0)
    rating: str = Field(..., min_length=1, max_length=20)
    comment: Optional[str] = None


@router.post("")
def create_feedback(
    request: FeedbackCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    message = (
        db.query(Message)
        .join(
            Conversation,
            Message.conversation_id == Conversation.id,
        )
        .filter(
            Message.id == request.message_id,
            Conversation.user_id == current_user.id,
            Conversation.organization_id == current_user.organization_id,
        )
        .first()
    )

    if message is None:
        raise HTTPException(
            status_code=404,
            detail="Message not found.",
        )

    feedback = feedback_service.create_feedback(
        db=db,
        message_id=message.id,
        user_id=current_user.id,
        rating=request.rating,
        comment=request.comment,
    )

    return {
        "id": feedback.id,
        "message_id": feedback.message_id,
        "user_id": feedback.user_id,
        "rating": feedback.rating,
        "comment": feedback.comment,
        "created_at": feedback.created_at.isoformat(),
    }
