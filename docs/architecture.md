# Architecture

Frontend (Next.js/React/TypeScript)
        |
        v
FastAPI backend
        |
        +--> RAG / retrieval / reranking
        |
        +--> Agent / tool layer
        |
        +--> LLM
        |
        +--> PostgreSQL + pgvector
        |
        +--> Redis / background workers
        |
        +--> Evaluation / tracing / audit

Detailed implementation will be added incrementally.
