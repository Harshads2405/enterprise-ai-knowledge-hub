from fastapi import FastAPI

from app.api.health import router as health_router


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