from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.conversations import router as conversations_router
from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.llm import router as llm_router
from app.api.rag import router as rag_router
from app.api.feedback import router as feedback_router

app = FastAPI(
    title="Enterprise AI Knowledge & Operations Copilot",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
app.include_router(feedback_router)

