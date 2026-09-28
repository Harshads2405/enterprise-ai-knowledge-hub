from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.feedback_service import feedback_service


router = APIRouter(
    prefix="/api/v1/feedback",
    tags=["feedback"],
)


class FeedbackCreateRequest(BaseModel):
    message_id: int
    user_id: int
    rating: str = Field(..., min_length=1, max_length=20)
    comment: Optional[str] = None


@router.post("")
def create_feedback(
    request: FeedbackCreateRequest,
    db: Session = Depends(get_db),
):
    feedback = feedback_service.create_feedback(
        db=db,
        message_id=request.message_id,
        user_id=request.user_id,
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
