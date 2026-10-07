"""Digital Thread Platform API client used by MES integration endpoints."""

from typing import Any

import httpx

from ..core.config import settings


class DtpConfigurationError(RuntimeError):
    """Raised when DTP integration is requested without credentials."""


class DtpClientError(RuntimeError):
    """Raised when DTP responds with an error or an unexpected payload."""


class DtpClient:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        auth_header: str | None = None,
        timeout: int | None = None,
    ) -> None:
        self.base_url = (base_url or settings.DTP_BASE_URL).rstrip("/")
        self.api_key = api_key if api_key is not None else settings.DTP_API_KEY
        self.auth_header = auth_header or settings.DTP_AUTH_HEADER
        self.timeout = timeout or settings.DTP_TIMEOUT

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise DtpConfigurationError("DTP API key is not configured")
        return {self.auth_header: self.api_key}

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=float(self.timeout)) as client:
            try:
                response = await client.get(url, params=params, headers=self._headers())
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise DtpClientError(f"DTP request failed: {exc.response.status_code}") from exc
            except httpx.RequestError as exc:
                raise DtpClientError("DTP request failed") from exc

        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            return response.json()
        return response.content

    async def list_projects(self, keyword: str | None = None) -> list[dict[str, Any]]:
        payload = await self._get("/openapi/v2/project", {"keyword": keyword} if keyword else None)
        if isinstance(payload, dict):
            if isinstance(payload.get("content"), list):
                return payload["content"]
            if isinstance(payload.get("data"), list):
                return payload["data"]
            if isinstance(payload.get("items"), list):
                return payload["items"]
        if isinstance(payload, list):
            return payload
        raise DtpClientError("Unexpected DTP project list payload")

    async def get_project_tree(self, asset_global_id: str, asset_id: str) -> dict[str, Any]:
        payload = await self._get(
            "/openapi/v2/project/tree",
            {"gid": asset_global_id, "aid": asset_id},
        )
        if not isinstance(payload, dict):
            raise DtpClientError("Unexpected DTP project tree payload")
        return payload

    async def find_nc_files(self, asset_global_id: str) -> list[dict[str, Any]]:
        payload = await self._get(
            "/openapi/v2/asset/find/ref",
            {"gid": asset_global_id, "category": "NC"},
        )
        if isinstance(payload, dict):
            if isinstance(payload.get("content"), list):
                return payload["content"]
            if isinstance(payload.get("data"), list):
                return payload["data"]
            if isinstance(payload.get("items"), list):
                return payload["items"]
        if isinstance(payload, list):
            return payload
        raise DtpClientError("Unexpected DTP NC file payload")

    async def download_userdata_file(self, path: str) -> bytes:
        payload = await self._get(
            "/openapi/v2/files/download/userdata",
            {"path": path},
        )
        if isinstance(payload, bytes):
            return payload
        raise DtpClientError("Unexpected DTP file download payload")
