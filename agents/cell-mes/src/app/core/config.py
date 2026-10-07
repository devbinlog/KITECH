"""Application configuration using Pydantic Settings."""

import os
import warnings
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator, field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields from .env
    )

    # Environment
    ENV: str = "development"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Application
    APP_NAME: str = "Cell-MES"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/mes.db"

    # JWT Authentication
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    @model_validator(mode="after")
    def validate_secret_key(self):
        """Warn if using default SECRET_KEY or INTERNAL_SERVICE_KEY (insecure for production)."""
        if self.SECRET_KEY == "your-secret-key-change-in-production":
            if not self.DEBUG:
                warnings.warn(
                    "Using default SECRET_KEY is insecure! "
                    "Set SECRET_KEY environment variable for production.",
                    UserWarning,
                    stacklevel=2,
                )
        if self.INTERNAL_SERVICE_KEY == "internal-service-key-change-in-production":
            if not self.DEBUG:
                warnings.warn(
                    "Using default INTERNAL_SERVICE_KEY is insecure! "
                    "Set INTERNAL_SERVICE_KEY environment variable for production.",
                    UserWarning,
                    stacklevel=2,
                )
        return self

    # Service URLs (from environment)
    CELL_MES_URL: str = "http://localhost:8000"
    NL_ROUTER_URL: str = "http://localhost:8001"
    CELL_SCHEDULER_URL: str = "http://localhost:8002"
    MIDDLEWARE_URL: str = "http://10.10.10.113:8100"
    TORUS_GATEWAY_URL: str = "http://10.10.10.113:5001"
    REDIS_URL: str = "redis://localhost:6379"
    DTP_BASE_URL: str = "https://dthread.nexmoa.com"
    DTP_API_KEY: str = ""
    DTP_AUTH_HEADER: str = "Authorization"
    DTP_TIMEOUT: int = 30
    P4R_FAILURE_RULES_PATH: str = "./config/p4r_failure_rules.json"

    # Middleware Server (legacy - use MIDDLEWARE_URL)
    @property
    def MIDDLEWARE_BASE_URL(self) -> str:
        """Backward compatible property."""
        return self.MIDDLEWARE_URL

    MIDDLEWARE_TIMEOUT: int = 30

    # Polling Configuration
    EQUIPMENT_POLL_INTERVAL_SEC: int = 3

    # File Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 50

    # CORS - 환경변수에서 쉼표로 구분된 문자열 지원
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"

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

    # Scheduler Integration (use CELL_SCHEDULER_URL)
    @property
    def SCHEDULER_BASE_URL(self) -> str:
        """Backward compatible property."""
        return self.CELL_SCHEDULER_URL

    SCHEDULER_TIMEOUT: int = 300
    SCHEDULER_DEFAULT_SOLVER: str = "OR_TOOLS"
    SCHEDULER_DEFAULT_HORIZON_HOURS: int = 24
    SCHEDULER_DEFAULT_TIME_LIMIT_SEC: int = 60

    # Scenario Files
    SCENARIOS_DIR: str = "./scenarios"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Internal Service Communication
    INTERNAL_SERVICE_KEY: str = "internal-service-key-change-in-production"

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
