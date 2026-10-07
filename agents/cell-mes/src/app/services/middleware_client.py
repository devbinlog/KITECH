"""Client helpers for Cell-MES to call the execution middleware."""

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx


class MiddlewareCallError(Exception):
    """Raised when the middleware HTTP call itself fails."""

    def __init__(self, message: str, status_code: Optional[int] = None, body: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.body = body


class MiddlewareBusinessError(Exception):
    """Raised when middleware returns HTTP 2xx with JSON status != success."""

    def __init__(
        self,
        message: str,
        error: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error = error
        self.payload = payload or {}


class MiddlewareClient:
    """Small async client that enforces middleware response semantics."""

    def __init__(self, base_url: str, caller: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.caller = caller
        self.timeout = timeout

    async def get_lot(self, lot_no: str) -> Dict[str, Any]:
        return await self._request("GET", f"/api/lots/{lot_no}")

    async def command_unit(
        self,
        lot_no: str,
        unit_no: str,
        action: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return await self._request(
            "POST",
            f"/api/lots/{lot_no}/units/{unit_no}/{action}",
            params=params,
        )

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        headers = {"X-Caller": self.caller}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method,
                    f"{self.base_url}{path}",
                    params=self._clean_params(params),
                    headers=headers,
                )
        except httpx.HTTPError as exc:
            raise MiddlewareCallError(f"미들웨어 통신 실패: {exc}") from exc

        return self._parse_response(response)

    @staticmethod
    def _clean_params(params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not params:
            return {}
        return {key: value for key, value in params.items() if value is not None}

    @staticmethod
    def _parse_response(response: httpx.Response) -> Dict[str, Any]:
        if response.status_code < 200 or response.status_code >= 300:
            raise MiddlewareCallError(
                "미들웨어 HTTP 요청 실패",
                status_code=response.status_code,
                body=response.text,
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise MiddlewareCallError(
                "미들웨어가 유효한 JSON을 반환하지 않았습니다",
                status_code=response.status_code,
                body=response.text,
            ) from exc

        if payload.get("status") != "success":
            raise MiddlewareBusinessError(
                payload.get("message") or "미들웨어가 요청을 거부했습니다",
                error=payload.get("error"),
                payload=payload,
            )

        return payload
