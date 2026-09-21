from fastapi import FastAPI

from app.api.conversations import router as conversations_router
from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.llm import router as llm_router
from app.api.rag import router as rag_router


app = FastAPI(
    title="Enterprise AI Knowledge & Operations Copilot",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Enterprise AI Copilot backend is running",
    }


app.include_router(health_router)
app.include_router(llm_router)
app.include_router(documents_router)
app.include_router(rag_router)
app.include_router(conversations_router)