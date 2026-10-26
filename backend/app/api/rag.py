
from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.models.user import User
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
def query_rag(
    request: RAGQueryRequest,
    current_user: User = Depends(get_current_user),
) -> RAGResponse:
    return rag_service.generate(
        question=request.question,
        organization_id=current_user.organization_id,
        limit=request.limit,
        department=request.department,
    )
