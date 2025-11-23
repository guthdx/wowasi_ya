"""Application configuration using pydantic-settings."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    environment: Literal["development", "staging", "production"] = "development"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Anthropic API
    anthropic_api_key: SecretStr = Field(..., description="Anthropic API key")

    # Security
    secret_key: SecretStr = Field(
        default="change-this-to-a-random-secret-key",
        description="Secret key for JWT tokens",
    )
    admin_username: str = "admin"
    admin_password: SecretStr = Field(default="changeme")

    # Output
    output_dir: Path = Path("./output")
    obsidian_vault_path: Path | None = None
    git_output_path: Path | None = None

    # Database
    database_url: str = "sqlite+aiosqlite:///./wowasi_ya.db"

    # Privacy
    strict_privacy_mode: bool = True
    privacy_confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="PII/PHI detection confidence threshold",
    )

    # Claude API
    claude_model: str = "claude-sonnet-4-20250514"
    max_generation_tokens: int = 4096
    enable_web_search: bool = True

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
