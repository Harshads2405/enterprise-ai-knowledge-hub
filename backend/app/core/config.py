from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

# Project root:
# enterprise-ai-copilot/
BASE_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "Enterprise AI Knowledge & Operations Copilot"
    app_version: str = "0.1.0"
    app_env: str = "development"
    debug: bool = True

    database_url: str
    redis_url: str
    groq_api_key: str

    jwt_secret_key: str

    llm_mode: str = "mock"

    rag_similarity_threshold: float = 0.30
    rag_multi_query_v2_enabled: bool = False

    rag_candidate_limit: int = 5
    rag_top_k: int = 3
    evaluation_organization_id: Optional[int] = None

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret_key(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError(
                "JWT_SECRET_KEY must contain at least 32 characters."
            )
        return value

settings = Settings()


def get_evaluation_organization_id() -> int:
    """Return the explicitly configured evaluation organization ID."""
    from app.core.organization import validate_organization_id

    try:
        return validate_organization_id(settings.evaluation_organization_id)
    except ValueError as exc:
        raise RuntimeError(
            "EVALUATION_ORGANIZATION_ID must be set to a positive integer "
            "before running an evaluation."
        ) from exc
