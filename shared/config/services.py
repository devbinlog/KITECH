"""
Service URL configuration and helpers.

Provides easy access to service URLs from environment variables.
"""

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional


@dataclass
class ServiceURLs:
    """
    Container for all service URLs.

    Use get_service_urls() to get an instance with values from environment.
    """

    cell_mes: str = "http://localhost:8000"
    nl_router: str = "http://localhost:8001"
    cell_scheduler: str = "http://localhost:8002"
    middleware: str = "http://localhost:8003"
    redis: str = "redis://localhost:6379"

    def get_mes_api_url(self, path: str = "") -> str:
        """Get full URL for MES API endpoint."""
        base = self.cell_mes.rstrip("/")
        path = path.lstrip("/")
        return f"{base}/{path}" if path else base

    def get_scheduler_api_url(self, path: str = "") -> str:
        """Get full URL for Scheduler API endpoint."""
        base = self.cell_scheduler.rstrip("/")
        path = path.lstrip("/")
        return f"{base}/{path}" if path else base

    def get_router_api_url(self, path: str = "") -> str:
        """Get full URL for NL Router API endpoint."""
        base = self.nl_router.rstrip("/")
        path = path.lstrip("/")
        return f"{base}/{path}" if path else base


@lru_cache()
def get_service_urls() -> ServiceURLs:
    """
    Get service URLs from environment variables.

    Cached for performance. Clear cache if environment changes:
        get_service_urls.cache_clear()

    Returns:
        ServiceURLs instance with values from environment
    """
    return ServiceURLs(
        cell_mes=os.getenv("CELL_MES_URL", "http://localhost:8000"),
        nl_router=os.getenv("NL_ROUTER_URL", "http://localhost:8001"),
        cell_scheduler=os.getenv("CELL_SCHEDULER_URL", "http://localhost:8002"),
        middleware=os.getenv("MIDDLEWARE_URL", "http://10.10.10.113:8100"),
        torus_gateway=os.getenv("TORUS_GATEWAY_URL", "http://10.10.10.113:5001"),
        redis=os.getenv("REDIS_URL", "redis://localhost:6379"),
    )


def get_internal_service_key() -> str:
    """Get the internal service communication key."""
    return os.getenv("INTERNAL_SERVICE_KEY", "internal-service-key-change-in-production")


class ServiceClientMixin:
    """
    Mixin for services that need to call other services.

    Provides:
    - Service URL access
    - Internal service key for authentication
    - Common HTTP headers

    Example:
        class MyClient(ServiceClientMixin):
            def __init__(self):
                self.mes_url = self.get_service_url("cell_mes")
                self.headers = self.get_internal_headers()
    """

    _service_urls: Optional[ServiceURLs] = None

    def get_service_urls(self) -> ServiceURLs:
        """Get service URLs (cached)."""
        if self._service_urls is None:
            self._service_urls = get_service_urls()
        return self._service_urls

    def get_service_url(self, service_name: str) -> str:
        """
        Get URL for a specific service.

        Args:
            service_name: One of 'cell_mes', 'nl_router', 'cell_scheduler',
                         'middleware', 'redis'

        Returns:
            Service URL string
        """
        urls = self.get_service_urls()
        return getattr(urls, service_name, "")

    def get_internal_headers(self) -> dict:
        """Get headers for internal service communication."""
        return {
            "X-Internal-Service-Key": get_internal_service_key(),
            "Content-Type": "application/json",
        }
