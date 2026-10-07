"""Central application configuration, loaded from environment variables / .env."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py -> repository root is three levels above "core"
REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AgentFlow AI"
    environment: Literal["development", "testing", "production"] = "development"
    api_v1_prefix: str = "/api/v1"

    log_level: str = "INFO"
    log_json: bool = False

    # Comma-separated string (simple to set in .env); use `cors_origin_list` in code.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Default to sqlite locally if PostgreSQL is not configured, or use provided DATABASE_URL
    database_url: SecretStr = SecretStr("sqlite:///./agentflow.db")

    # LLM Settings
    llm_provider: Literal["mock", "gemini", "openai"] = "mock"
    gemini_api_key: SecretStr = SecretStr("")
    gemini_model: str = "gemini-2.5-flash"
    openai_api_key: SecretStr = SecretStr("")
    openai_api_base: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    # Execution limits
    max_workflow_iterations: int = 50
    default_task_timeout_seconds: int = 60
    max_task_retries: int = 3

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
