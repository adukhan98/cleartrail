"""Application configuration via environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_name: str = "Compliance Packet Agent"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    secret_key: str = Field(..., description="Secret key for JWT signing")

    # Database
    database_url: PostgresDsn = Field(
        ..., description="PostgreSQL connection string"
    )
    database_pool_size: int = 5
    database_max_overflow: int = 10

    # Redis
    redis_url: RedisDsn = Field(..., description="Redis connection string")

    # Auth
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # GitHub Integration
    github_app_id: str | None = None
    github_app_private_key: str | None = None
    github_client_id: str | None = None
    github_client_secret: str | None = None
    github_webhook_secret: str | None = None

    # Jira Integration
    jira_client_id: str | None = None
    jira_client_secret: str | None = None

    # Google Drive Integration
    google_client_id: str | None = None
    google_client_secret: str | None = None

    # OpenAI
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o"

    # Encryption
    encryption_key: str = Field(
        ..., description="Fernet key for encrypting OAuth tokens"
    )

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
