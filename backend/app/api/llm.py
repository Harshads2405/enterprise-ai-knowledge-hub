
from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.llm.chat import ChatRequest
from app.services.llm.groq_client import groq_client


router = APIRouter(
    prefix="/api/v1/llm",
    tags=["LLM"],
)


@router.post("/chat")
def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    response = groq_client.chat(request.message)

    return {
        "message": request.message,
        "response": response,
    }
