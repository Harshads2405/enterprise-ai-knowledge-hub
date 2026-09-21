from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.message import Message


class ConversationService:

    def create_conversation(
        self,
        db: Session,
        organization_id: int,
        user_id: int,
        title: Optional[str] = None,
    ) -> Conversation:

        conversation = Conversation(
            organization_id=organization_id,
            user_id=user_id,
            title=title or "New Conversation",
        )

        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        return conversation

    def get_conversation(
        self,
        db: Session,
        conversation_id: int,
    ) -> Optional[Conversation]:

        return (
            db.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )

    def add_message(
        self,
        db: Session,
        conversation_id: int,
        role: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> Message:

        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            message_metadata=metadata or {},
        )

        db.add(message)
        db.commit()
        db.refresh(message)

        return message

    def get_messages(
        self,
        db: Session,
        conversation_id: int,
    ) -> List[Message]:

        return (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc(), Message.id.asc())
            .all()
        )


conversation_service = ConversationService()