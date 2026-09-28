from typing import Optional

from sqlalchemy.orm import Session

from app.models.message_feedback import MessageFeedback


class FeedbackService:

    def create_feedback(
        self,
        db: Session,
        message_id: int,
        user_id: int,
        rating: str,
        comment: Optional[str] = None,
    ) -> MessageFeedback:
        feedback = MessageFeedback(
            message_id=message_id,
            user_id=user_id,
            rating=rating,
            comment=comment,
        )

        db.add(feedback)
        db.commit()
        db.refresh(feedback)

        return feedback


feedback_service = FeedbackService()
