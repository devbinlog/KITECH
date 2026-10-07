"""
Base configuration classes for all agents.

Provides:
- Common settings structure
- Environment file loading logic
- Validation helpers
"""

import os
from pathlib import Path
from typing import List
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_env_file() -> str:
    """
    Determine which .env file to use based on ENV environment variable.

    Priority:
    1. ENV_FILE environment variable (explicit path)
    2. ENV=production → .env.prod
    3. ENV=development → .env.dev
    4. Default → .env (if exists) or .env.dev

    Returns:
        Path to the environment file to use
    """
    # Check for explicit ENV_FILE
    if env_file := os.getenv("ENV_FILE"):
        return env_file

    # Determine based on ENV
    env = os.getenv("ENV", "development").lower()

    # Find project root (contains pyproject.toml)
    current = Path(__file__).resolve()
    project_root = current
    for parent in current.parents:
        if (parent / "pyproject.toml").exists():
            project_root = parent
            break

    if env == "production":
        env_path = project_root / ".env.prod"
    else:
        env_path = project_root / ".env.dev"

    # Fallback to .env if specific file doesn't exist
    if not env_path.exists():
        default_env = project_root / ".env"
        if default_env.exists():
            return str(default_env)

    return str(env_path)


class BaseAppSettings(BaseSettings):
    """
    Base settings class with common configuration for all agents.

    Subclass this and add agent-specific settings.

    Example:
        class CellMESSettings(BaseAppSettings):
            DATABASE_URL: str = "sqlite+aiosqlite:///./data/mes.db"
            SCHEDULER_TIMEOUT: int = 120
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore unknown env vars
    )

    # Environment
    ENV: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Service URLs
    CELL_MES_URL: str = "http://localhost:8000"
    NL_ROUTER_URL: str = "http://localhost:8001"
    CELL_SCHEDULER_URL: str = "http://localhost:8002"
    MIDDLEWARE_URL: str = "http://10.10.10.113:8100"
    TORUS_GATEWAY_URL: str = "http://10.10.10.113:5001"
    REDIS_URL: str = "redis://localhost:6379"

    # Authentication
    SECRET_KEY: str = "your-secret-key-change-in-production"
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
            return []
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENV.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENV.lower() in ("development", "dev")


@lru_cache()
def get_base_settings() -> BaseAppSettings:
    """
    Get cached base settings instance.

    Uses the appropriate .env file based on ENV environment variable.
    """
    env_file = get_env_file()
    return BaseAppSettings(_env_file=env_file)
