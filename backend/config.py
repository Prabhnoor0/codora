"""
Application configuration using Pydantic Settings.
All values loaded from environment variables / .env file.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Literal


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ───────────────────────────────────────────────────
    APP_ENV: Literal["development", "production", "testing"] = "development"
    SECRET_KEY: str = "change-me-to-a-random-64-char-string"
    JWT_SECRET: str = "change-me-jwt-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"

    # ── GitHub OAuth ─────────────────────────────────────────
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_CALLBACK_URL: str = "http://localhost:8000/api/auth/github/callback"
    GITHUB_PAT: str = ""

    # ── LLM ──────────────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    XAI_API_KEY: str = ""
    LLM_PROVIDER: Literal["openai", "anthropic", "google", "groq"] = "groq"
    LLM_MODEL: str = "llama-3.1-8b-instant"

    # ── PostgreSQL ────────────────────────────────────────────
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "mentor"
    POSTGRES_PASSWORD: str = "mentor_password"
    POSTGRES_DB: str = "ai_mentor"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # ── Neo4j ────────────────────────────────────────────────
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "mentor_password"

    # ── Qdrant ───────────────────────────────────────────────
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: str = ""

    # ── Redis ─────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Celery ───────────────────────────────────────────────
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ── ML ───────────────────────────────────────────────────
    EMBEDDING_MODEL: Literal["lightweight", "codebert", "graphcodebert"] = "lightweight"
    EMBEDDING_DIM: int = 384  # lightweight; 768 for codebert
    MODELS_CACHE_DIR: str = "./models_cache"

    # ── Derived helpers ──────────────────────────────────────
    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def github_headers(self) -> dict:
        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.GITHUB_PAT:
            headers["Authorization"] = f"token {self.GITHUB_PAT}"
        return headers


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
