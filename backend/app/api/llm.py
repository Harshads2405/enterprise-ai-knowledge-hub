from fastapi import APIRouter

from app.schemas.llm.chat import ChatRequest
from app.services.llm.groq_client import groq_client


router = APIRouter(
    prefix="/api/v1/llm",
    tags=["LLM"],
)


@router.post("/chat")
def chat(request: ChatRequest):
    response = groq_client.chat(request.message)

    return {
        "message": request.message,
        "response": response,
    }