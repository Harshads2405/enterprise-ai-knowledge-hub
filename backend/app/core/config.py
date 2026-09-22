from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

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

    llm_mode: str = "mock"

    rag_similarity_threshold: float = 0.30
    rag_multi_query_v2_enabled: bool = False

    rag_candidate_limit: int = 5
    rag_top_k: int = 3

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

settings = Settings()
