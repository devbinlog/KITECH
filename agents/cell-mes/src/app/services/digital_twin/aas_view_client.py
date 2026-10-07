"""Client for middleware AAS view data used by digital twin adapters."""

from __future__ import annotations

from typing import Any

import httpx

from ...core.config import settings
from ..aas_scheduler_info import normalize_aas_assets_response


class AasViewClientError(Exception):
    """Raised when the middleware AAS view cannot be read."""


class AasViewClient:
    """Read middleware `/api/aas/view` using the same surface MES already uses."""

    def __init__(self, base_url: str | None = None, timeout: float | None = None):
        self.base_url = (base_url or settings.MIDDLEWARE_URL).rstrip("/")
        self.timeout = timeout or float(settings.MIDDLEWARE_TIMEOUT)

    async def fetch_assets(self) -> list[dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/aas/view")
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            detail = str(exc) or exc.__class__.__name__
            raise AasViewClientError(f"미들웨어 AAS view 조회 실패: {detail}") from exc
        except ValueError as exc:
            raise AasViewClientError("미들웨어 AAS view 응답이 JSON이 아닙니다") from exc

        if isinstance(payload, dict) and payload.get("status") not in (None, "success"):
            raise AasViewClientError(payload.get("message") or "미들웨어 AAS view 조회가 거부되었습니다")
        return normalize_aas_assets_response(payload)
