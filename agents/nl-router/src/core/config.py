"""NL-Router configuration using Pydantic Settings."""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    """NL-Router application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    ENV: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8001

    # Application
    APP_NAME: str = "NL-Router"
    APP_VERSION: str = "0.1.0"

    # Service URLs
    CELL_MES_URL: str = "http://localhost:8000"
    NL_ROUTER_URL: str = "http://localhost:8001"
    CELL_SCHEDULER_URL: str = "http://localhost:8002"
    MIDDLEWARE_URL: str = "http://10.10.10.113:8100"
    TORUS_GATEWAY_URL: str = "http://10.10.10.113:5001"
    REDIS_URL: str = "redis://localhost:6379"

    # MES API (backward compatible property)
    @property
    def MES_API_BASE_URL(self) -> str:
        """Backward compatible property for MES API URL."""
        return self.CELL_MES_URL

    # Authentication
    INTERNAL_SERVICE_KEY: str = "internal-service-key-change-in-production"

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Accept both string and list for CORS_ORIGINS."""
        if isinstance(v, list):
            return ",".join(v)
        return v

    def get_cors_origins_list(self) -> List[str]:
        """Return CORS_ORIGINS as a list."""
        if not self.CORS_ORIGINS:
            return ["*"]
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # LLM Settings
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.1

    # HTTP Client
    HTTP_TIMEOUT: float = 30.0

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENV.lower() == "production"


def _get_env_file() -> str:
    """Determine which .env file to use."""
    if env_file := os.getenv("ENV_FILE"):
        return env_file
    env = os.getenv("ENV", "development").lower()
    if env == "production":
        return ".env.prod"
    return ".env"


settings = Settings(_env_file=_get_env_file())
