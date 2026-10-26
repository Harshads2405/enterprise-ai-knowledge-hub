
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.conversation.request import (
    ConversationCreateRequest,
    ConversationMessageRequest,
)
from app.schemas.conversation.response import (
    ConversationMessageResponse,
    ConversationRAGResponse,
    ConversationResponse,
)
from app.services.conversation.conversation_service import conversation_service
from app.services.rag.rag_service import rag_service
from app.services.conversation.conversation_state_service import (
    conversation_state_service,
)
from app.services.conversation.conversation_context_service import (
    conversation_context_service,
)


router = APIRouter(
    prefix="/api/v1/conversations",
    tags=["Conversations"],
)


def _get_owned_conversation(
    db: Session,
    conversation_id: int,
    current_user: User,
):
    conversation = conversation_service.get_conversation(
        db=db,
        conversation_id=conversation_id,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    return conversation


@router.post("", response_model=ConversationResponse)
def create_conversation(
    request: ConversationCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConversationResponse:
    conversation = conversation_service.create_conversation(
        db=db,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        title=request.title,
    )

    return ConversationResponse(
        id=conversation.id,
        organization_id=conversation.organization_id,
        user_id=conversation.user_id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


@router.get("", response_model=List[ConversationResponse])
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ConversationResponse]:
    conversations = conversation_service.list_conversations(
        db=db,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
    )

    return [
        ConversationResponse(
            id=conversation.id,
            organization_id=conversation.organization_id,
            user_id=conversation.user_id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )
        for conversation in conversations
    ]


@router.get("/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConversationResponse:
    conversation = _get_owned_conversation(
        db=db,
        conversation_id=conversation_id,
        current_user=current_user,
    )

    return ConversationResponse(
        id=conversation.id,
        organization_id=conversation.organization_id,
        user_id=conversation.user_id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


@router.get(
    "/{conversation_id}/messages",
    response_model=List[ConversationMessageResponse],
)
def get_conversation_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ConversationMessageResponse]:
    _get_owned_conversation(
        db=db,
        conversation_id=conversation_id,
        current_user=current_user,
    )

    messages = conversation_service.get_messages(
        db=db,
        conversation_id=conversation_id,
    )

    return [
        ConversationMessageResponse(
            message_id=message.id,
            conversation_id=message.conversation_id,
            role=message.role,
            content=message.content,
            metadata=message.message_metadata,
        )
        for message in messages
    ]


@router.post(
    "/{conversation_id}/messages",
    response_model=ConversationRAGResponse,
)
def send_message(
    conversation_id: int,
    request: ConversationMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConversationRAGResponse:
    _get_owned_conversation(
        db=db,
        conversation_id=conversation_id,
        current_user=current_user,
    )

    messages = conversation_service.get_messages(
        db=db,
        conversation_id=conversation_id,
    )

    pending_clarification = None

    if messages:
        latest_message = messages[-1]

        if latest_message.role == "assistant":
            if conversation_state_service.is_pending_clarification(
                latest_message.message_metadata
            ):
                pending_clarification = latest_message

    conversation_service.add_message(
        db=db,
        conversation_id=conversation_id,
        role="user",
        content=request.content,
        metadata={"type": "user_message"},
    )

    if pending_clarification is not None:
        clarification_metadata = pending_clarification.message_metadata
        options = conversation_state_service.get_options(
            clarification_metadata
        )

        selected_topic = conversation_state_service.find_selected_topic(
            user_input=request.content,
            options=options,
        )

        if selected_topic is None:
            rag_response = rag_service.generate(
                question=request.content,
                organization_id=current_user.organization_id,
                limit=request.limit,
                department=request.department,
            )
        else:
            original_query = (
                conversation_state_service.get_original_query(
                    clarification_metadata
                )
            )

            if not original_query:
                rag_response = rag_service.generate(
                    question=request.content,
                    limit=request.limit,
                    organization_id=current_user.organization_id,
                    department=request.department,
                )
            else:
                rag_response = (
                    rag_service.generate_with_clarification(
                        original_question=original_query,
                        selected_topic=selected_topic,
                        organization_id=current_user.organization_id,
                        limit=request.limit,
                        department=request.department,
                    )
                )
    else:
        contextual_query = (
            conversation_context_service.build_contextual_query(
                current_query=request.content,
                messages=messages,
            )
        )

        rag_response = rag_service.generate(
            question=contextual_query,
            limit=request.limit,
            organization_id=current_user.organization_id,
            department=request.department,
        )

    assistant_metadata = {
        "type": (
            "clarification"
            if rag_response.should_clarify
            else "assistant_message"
        ),
        "pending": rag_response.should_clarify,
        "sources": [
            source.model_dump()
            for source in rag_response.sources
        ],
    }

    if rag_response.should_clarify:
        assistant_metadata.update(
            {
                "original_query": request.content,
                "options": [
                    {
                        "label": option.label,
                        "topic": option.topic,
                    }
                    for option in rag_response.clarification_options
                ],
            }
        )

    assistant_content = (
        rag_response.clarification_question
        if rag_response.should_clarify
        else rag_response.answer
    )

    assistant_message = conversation_service.add_message(
        db=db,
        conversation_id=conversation_id,
        role="assistant",
        content=assistant_content,
        metadata=assistant_metadata,
    )

    return ConversationRAGResponse(
        message_id=assistant_message.id,
        conversation_id=conversation_id,
        role="assistant",
        answer=rag_response.answer,
        sources=rag_response.sources,
        should_clarify=rag_response.should_clarify,
        clarification_question=rag_response.clarification_question,
        clarification_options=[
            {
                "label": option.label,
                "topic": option.topic,
            }
            for option in rag_response.clarification_options
        ],
        metadata=assistant_metadata,
    )
