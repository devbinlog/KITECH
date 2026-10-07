"""Async HTTP client for middleware communication."""

from typing import Any, Dict, List, Optional

import httpx

from ..app.core.config import settings
from ..app.services.aas_scheduler_info import normalize_aas_assets_response


class MiddlewareClient:
    """Async HTTP client for middleware server communication."""

    def __init__(self, base_url: Optional[str] = None, timeout: int = 30):
        """
        Initialize middleware client.

        Args:
            base_url: Middleware server base URL (default from settings)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or settings.MIDDLEWARE_URL
        self.timeout = timeout

    async def fetch_all_assets(self) -> List[Dict[str, Any]]:
        """
        Fetch all AAS assets from middleware.

        Returns:
            List of asset dictionaries with id, name, type, connection, spec
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/api/aas/view")
            response.raise_for_status()
            data = response.json()
            # 미들웨어 응답 형식이 {"data": [...]}, 직접 리스트, 또는
            # {"assetAdministrationShells": [...], "submodels": [...]}일 수 있음.
            return normalize_aas_assets_response(data)

    async def get_equipment_status(self, connection_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get real-time status for an equipment.

        Args:
            connection_config: Equipment connection configuration (ip, port, etc.)

        Returns:
            Raw status data from equipment
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/resources/status",
                params=connection_config,
            )
            response.raise_for_status()
            return response.json()

    async def send_work_info(self, payload: Dict[str, Any]) -> bool:
        """
        Send work execution payload to middleware.

        Args:
            payload: Work info payload (wo_id, routing, scenario, etc.)

        Returns:
            True if successful
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            job_id = payload.get("job_id") or payload.get("wo_id")
            response = await client.post(
                f"{self.base_url}/api/lots/{job_id}/start",
                json=payload,
            )
            response.raise_for_status()
            return True

    async def health_check(self) -> bool:
        """미들웨어 서버 정상 동작 여부 확인. /api/aas/view 엔드포인트를 호출하여 확인."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/api/aas/view")
                return response.status_code < 400
        except Exception:
            return False


# Singleton instance
middleware_client = MiddlewareClient()
