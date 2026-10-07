"""Tests for scheduling/http_client.py — HTTP + circuit breaker."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _make_scheduling_request(machines=None, work_orders=None):
    return {
        "request": {
            "scheduling_request": {
                "scheduling_horizon": {
                    "start": "2024-06-01T09:00:00+00:00",
                    "end": "2024-06-02T09:00:00+00:00",
                }
            }
        },
        "work_orders": work_orders or [],
        "machines": machines or [],
        "machine_type_params": {"machine_types": {}},
        "constraints": {},
        "amrs": [],
        "scheduler_config": {"lot_size": 1, "amr_transfer_time_sec": 60},
    }


def _mock_cb(allow=True):
    cb = MagicMock()
    cb.allow.return_value = allow
    cb.record_success = MagicMock()
    cb.record_failure = MagicMock()
    return cb


class TestCallSchedulerService:
    @pytest.mark.asyncio
    async def test_returns_result_on_success(self):
        from src.app.services.scheduling.http_client import SchedulerHttpClient

        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "success", "scheduled_tasks": []}
        mock_response.raise_for_status = MagicMock()

        mock_http = AsyncMock()
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_http.post = AsyncMock(return_value=mock_response)

        cb = _mock_cb(allow=True)

        client = SchedulerHttpClient()
        with patch("src.app.services.scheduling.http_client._get_scheduler_cb", return_value=cb):
            with patch("src.app.services.scheduling.http_client.httpx.AsyncClient", return_value=mock_http):
                result = await client.call_scheduler_service(
                    _make_scheduling_request(), solver_type="OR_TOOLS"
                )

        assert result["status"] == "success"
        cb.record_success.assert_called_once()

    @pytest.mark.asyncio
    async def test_circuit_open_returns_error(self):
        from src.app.services.scheduling.http_client import SchedulerHttpClient

        cb = _mock_cb(allow=False)
        client = SchedulerHttpClient()
        with patch("src.app.services.scheduling.http_client._get_scheduler_cb", return_value=cb):
            result = await client.call_scheduler_service(_make_scheduling_request())

        assert result["status"] == "error"
        assert "circuit" in result["error"].lower() or "중단" in result["error"]
        cb.record_failure.assert_not_called()

    @pytest.mark.asyncio
    async def test_timeout_returns_error_and_records_failure(self):
        import httpx
        from src.app.services.scheduling.http_client import SchedulerHttpClient

        mock_http = AsyncMock()
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_http.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

        cb = _mock_cb(allow=True)
        client = SchedulerHttpClient()
        with patch("src.app.services.scheduling.http_client._get_scheduler_cb", return_value=cb):
            with patch("src.app.services.scheduling.http_client.httpx.AsyncClient", return_value=mock_http):
                result = await client.call_scheduler_service(_make_scheduling_request())

        assert result["status"] == "error"
        cb.record_failure.assert_called_once()

    @pytest.mark.asyncio
    async def test_http_status_error_returns_error(self):
        import httpx
        from src.app.services.scheduling.http_client import SchedulerHttpClient

        mock_response_obj = MagicMock()
        mock_response_obj.status_code = 500

        mock_http = AsyncMock()
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_http.post = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "error", request=MagicMock(), response=mock_response_obj
            )
        )

        cb = _mock_cb(allow=True)
        client = SchedulerHttpClient()
        with patch("src.app.services.scheduling.http_client._get_scheduler_cb", return_value=cb):
            with patch("src.app.services.scheduling.http_client.httpx.AsyncClient", return_value=mock_http):
                result = await client.call_scheduler_service(_make_scheduling_request())

        assert result["status"] == "error"
        cb.record_failure.assert_called_once()

    @pytest.mark.asyncio
    async def test_uses_solver_time_limits_per_type(self):
        """OR_TOOLS should use 60s, ALNS 300s, unless overridden."""
        from src.app.services.scheduling.http_client import (
            SchedulerHttpClient,
            SOLVER_TIME_LIMITS,
        )

        assert SOLVER_TIME_LIMITS["OR_TOOLS"] == 60
        assert SOLVER_TIME_LIMITS["ALNS"] == 300
        assert SOLVER_TIME_LIMITS["SA"] == 30

    @pytest.mark.asyncio
    async def test_caller_override_time_limit(self):
        """time_limit_sec=5 should override defaults and appear in POST body."""
        from src.app.services.scheduling.http_client import SchedulerHttpClient

        captured = []

        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "success", "scheduled_tasks": []}
        mock_response.raise_for_status = MagicMock()

        async def fake_post(url, json=None, **kwargs):
            captured.append(json)
            return mock_response

        mock_http = AsyncMock()
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_http.post = fake_post

        cb = _mock_cb(allow=True)
        client = SchedulerHttpClient()
        with patch("src.app.services.scheduling.http_client._get_scheduler_cb", return_value=cb):
            with patch("src.app.services.scheduling.http_client.httpx.AsyncClient", return_value=mock_http):
                await client.call_scheduler_service(
                    _make_scheduling_request(), solver_type="OR_TOOLS", time_limit_sec=5
                )

        assert captured[0]["options"]["time_limit_sec"] == 5
