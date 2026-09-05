from functools import lru_cache
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application runtime configuration settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # General App Settings
    PROJECT_NAME: str = "Voice AI Patient Registration System"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # Database Settings
    DATABASE_URL: str = "sqlite+aiosqlite:///./patients.db"

    # Security & Authentication
    WEBHOOK_SECRET: str = "vapi_secret_token_dev_2026"
    API_KEY: str = "dev_api_key_voice_agent"

    # Vapi Telephony Settings
    VAPI_API_KEY: str | None = None
    VAPI_PHONE_NUMBER: str | None = None
    VAPI_ASSISTANT_ID: str | None = None

    # OpenAI-Compatible LLM Provider Settings (Groq, OpenRouter, DeepSeek, Together, Ollama, etc.)
    LLM_BASE_URL: str = "https://api.groq.com/openai/v1"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    LLM_TEMPERATURE: float = 0.1

    @property
    def is_production(self) -> bool:
        """Check if current environment is production."""
        return self.ENVIRONMENT == "production"

    @property
    def is_sqlite(self) -> bool:
        """Check if currently configured database engine is SQLite."""
        return "sqlite" in self.DATABASE_URL.lower()

    @property
    def async_database_url(self) -> str:
        """Normalize database URL for SQLAlchemy async engine.
        
        Automatically converts standard postgresql:// or postgres:// to postgresql+asyncpg://
        and strips query params like sslmode that asyncpg handles via connect_args.
        """
        url = self.DATABASE_URL.strip()
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

        # Strip sslmode or other query parameters that cause asyncpg errors
        if "sslmode=" in url:
            import re
            url = re.sub(r"[?&]sslmode=[^&]+", "", url)
            if "?" not in url and "&" in url:
                url = url.replace("&", "?", 1)
        return url


@lru_cache()
def get_settings() -> Settings:
    """Returns singleton cached instance of Application Settings."""
    return Settings()
