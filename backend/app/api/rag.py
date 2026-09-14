from fastapi import APIRouter

from app.schemas.rag.query import RAGQueryRequest
from app.schemas.rag.response import RAGResponse
from app.services.rag.rag_service import rag_service


router = APIRouter(
    prefix="/api/v1/rag",
    tags=["RAG"],
)


@router.post(
    "/query",
    response_model=RAGResponse,
)
def query_rag(request: RAGQueryRequest) -> RAGResponse:
    return rag_service.generate(
        question=request.question,
        limit=request.limit,
    )