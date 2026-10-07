"""
Shared configuration module for agents-workspace.

Provides centralized configuration management with:
- Environment variable loading
- Pydantic-based validation
- Service URL management
- Common settings across all agents
"""

from .base import BaseAppSettings, get_env_file
from .services import ServiceURLs, get_service_urls

__all__ = [
    "BaseAppSettings",
    "get_env_file",
    "ServiceURLs",
    "get_service_urls",
]
