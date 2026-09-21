from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.schemas.conversation.request import (
    ConversationCreateRequest,
    ConversationMessageRequest,
)

from app.schemas.conversation.response import (
    ConversationMessageResponse,
    ConversationRAGResponse,
    ConversationResponse,
)

from app.services.conversation.conversation_service import (
    conversation_service,
)

from app.services.rag.rag_service import (
    rag_service,
)
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


@router.post(
    "",
    response_model=ConversationResponse,
)
def create_conversation(
    request: ConversationCreateRequest,
    db: Session = Depends(get_db),
) -> ConversationResponse:

    conversation = conversation_service.create_conversation(
        db=db,
        organization_id=request.organization_id,
        user_id=request.user_id,
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

@router.post(
    "/{conversation_id}/messages",
    response_model=ConversationRAGResponse,
)
def send_message(
    conversation_id: int,
    request: ConversationMessageRequest,
    db: Session = Depends(get_db),
) -> ConversationRAGResponse:

    conversation = conversation_service.get_conversation(
        db=db,
        conversation_id=conversation_id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    # ---------------------------------------------------------
    # 1. Check whether the conversation has a pending
    #    clarification from the previous assistant message.
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # 2. Save the user's message.
    # ---------------------------------------------------------

    conversation_service.add_message(
        db=db,
        conversation_id=conversation_id,
        role="user",
        content=request.content,
        metadata={
            "type": "user_message",
        },
    )

    # ---------------------------------------------------------
    # 3. Run RAG.
    #
    #    If clarification is pending:
    #      resolve the user's selection against the stored
    #      clarification options.
    #
    #    Otherwise:
    #      process the message normally.
    # ---------------------------------------------------------

    if pending_clarification is not None:

        clarification_metadata = (
            pending_clarification.message_metadata
        )

        options = (
            conversation_state_service.get_options(
                clarification_metadata
            )
        )

        selected_topic = (
            conversation_state_service.find_selected_topic(
                user_input=request.content,
                options=options,
            )
        )

        if selected_topic is None:

            rag_response = rag_service.generate(
                question=request.content,
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
                    department=request.department,
                )

            else:
                rag_response = (
                    rag_service.generate_with_clarification(
                        original_question=original_query,
                        selected_topic=selected_topic,
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

            department=request.department,

        )

    # ---------------------------------------------------------
    # 4. Build assistant metadata.
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # 5. Persist assistant response.
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # 6. Return the complete conversation RAG response.
    # ---------------------------------------------------------

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