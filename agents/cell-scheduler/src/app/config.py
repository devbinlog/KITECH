"""Cell-Scheduler configuration using Pydantic Settings."""

import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    """Cell-Scheduler application settings loaded from environment variables."""

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
    PORT: int = 8002

    # Application
    APP_NAME: str = "Cell-Scheduler"
    APP_VERSION: str = "0.2.0"

    # Service URLs
    CELL_MES_URL: str = "http://localhost:8000"
    NL_ROUTER_URL: str = "http://localhost:8001"
    CELL_SCHEDULER_URL: str = "http://localhost:8002"
    MIDDLEWARE_URL: str = "http://10.10.10.113:8100"
    TORUS_GATEWAY_URL: str = "http://10.10.10.113:5001"
    REDIS_URL: str = "redis://localhost:6379"

    # Authentication
    INTERNAL_SERVICE_KEY: str = "internal-service-key-change-in-production"

    # CORS - 환경변수에서 쉼표로 구분된 문자열 지원
    CORS_ORIGINS: str = (
        "http://localhost:3000,http://localhost:3001,http://localhost:8000,http://localhost:8001"
    )

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

    # AAS Configuration
    AAS_PATH: str = ""  # aas.json 경로. 설정 시 machines/amrs를 AAS에서 로드. 미설정 시 요청 바디 사용

    # Solver Configuration
    DEFAULT_SOLVER: str = "OR_TOOLS"
    DEFAULT_TIME_LIMIT_SEC: int = 60
    DEFAULT_HORIZON_HOURS: int = 24

    # Solver-specific settings
    GA_POPULATION_SIZE: int = 100
    GA_GENERATIONS: int = 200
    SA_INITIAL_TEMP: float = 10000.0
    SA_COOLING_RATE: float = 0.995
    TABU_LIST_SIZE: int = 50

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
