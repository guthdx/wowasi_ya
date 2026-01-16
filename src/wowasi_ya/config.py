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
        populate_by_name=True,
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
    api_key: SecretStr | None = Field(
        default=None,
        alias="WOWASI_API_KEY",
        description="API key for portal/external access",
    )

    # Output
    output_dir: Path = Path("./output")
    obsidian_vault_path: Path | None = None
    git_output_path: Path | None = None
    gdrive_remote_path: str = "gdrive:Wowasi"
    enable_gdrive_sync: bool = True

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
    max_generation_tokens: int = 32000  # Full capacity for long documents
    enable_web_search: bool = True
    max_concurrent_research_agents: int = Field(default=1, ge=1, le=10)  # Rate limit protection

    # LLM Provider Configuration
    generation_provider: Literal["claude", "llamacpp"] = "claude"  # Default to Claude API
    research_provider: Literal["claude"] = "claude"  # Fixed for now (web search)

    # Llama CPP Settings (via Cloudflare Tunnel)
    llamacpp_base_url: str = "https://llama.iyeska.net"
    llamacpp_model: str = "Llama-3.3-70B-Instruct-Q4_K_M"
    llamacpp_timeout: int = 300  # 5 minutes for large documents
    llamacpp_fallback_to_claude: bool = True  # Fallback when Mac offline (if llamacpp primary)
    claude_fallback_to_llamacpp: bool = True  # Fallback to Mac when Claude has issues

    # Outline Wiki Integration
    outline_api_url: str = "https://docs.iyeska.net"
    outline_api_key: SecretStr | None = Field(default=None, description="Outline API key")
    outline_auto_publish: bool = False  # Auto-publish on generation

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
