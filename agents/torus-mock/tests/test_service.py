"""Tests for service.py — the thin FastAPI container wrapper.

Covers the 4 required test patterns from api-design-principles.md:
  1. /health → 200 OK
  2. /capabilities → correct structure
  3. domain endpoint without auth → 401 (when auth enabled)
  4. domain endpoint with valid auth → 200

Uses anyio (available in root venv) for async test execution.
Auth is controlled via MOCK_SKIP_AUTH env var and INTERNAL_SERVICE_KEY.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

# Ensure workspace root is on path so shared.common is importable
_root = Path(__file__).parent.parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

DATA_DIR = Path(__file__).parent.parent / "data"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _reset_store():
    from src.app.services.machine_store import reset_store, get_store
    reset_store()
    store = get_store()
    store.load_from_json(DATA_DIR / "default_machines.json")


def _get_app_skip_auth():
    """Return app with MOCK_SKIP_AUTH=1 (no auth)."""
    os.environ["MOCK_SKIP_AUTH"] = "1"
    os.environ.pop("INTERNAL_SERVICE_KEY", None)
    # Force reimport to pick up env change
    if "src.service" in sys.modules:
        del sys.modules["src.service"]
    from src.service import app
    return app


def _get_app_with_auth(key: str = "test-secret-key"):
    """Return app with MOCK_SKIP_AUTH=0 and INTERNAL_SERVICE_KEY set."""
    os.environ["MOCK_SKIP_AUTH"] = "0"
    os.environ["INTERNAL_SERVICE_KEY"] = key
    if "src.service" in sys.modules:
        del sys.modules["src.service"]
    from src.service import app
    return app


# ---------------------------------------------------------------------------
# 1. /health — no auth required
# ---------------------------------------------------------------------------


class TestHealth:
    @pytest.mark.anyio
    async def test_health_ok(self):
        """GET /health returns 200 with service info."""
        _reset_store()
        app = _get_app_skip_auth()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "torus-mock"
        assert "version" in data

    @pytest.mark.anyio
    async def test_health_no_auth_needed(self):
        """/health is accessible without X-Internal-Key even when auth is on."""
        _reset_store()
        app = _get_app_with_auth()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/health")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# 2. /capabilities — MCP-style introspection, no auth
# ---------------------------------------------------------------------------


class TestCapabilities:
    @pytest.mark.anyio
    async def test_capabilities_structure(self):
        """GET /capabilities returns correct MCP-style structure."""
        _reset_store()
        app = _get_app_skip_auth()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/capabilities")
        assert resp.status_code == 200
        data = resp.json()
        assert data["service"] == "torus-mock"
        assert "version" in data
        assert "tools" in data
        tool_names = {t["name"] for t in data["tools"]}
        assert "get_data" in tool_names
        assert "list_machines" in tool_names
        assert "get_plc_signal" in tool_names

    @pytest.mark.anyio
    async def test_capabilities_no_auth_needed(self):
        """/capabilities is accessible without X-Internal-Key."""
        _reset_store()
        app = _get_app_with_auth()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/capabilities")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# 3. Domain endpoints without auth → 401 (auth enforced mode)
# ---------------------------------------------------------------------------


class TestAuthEnforced:
    @pytest.mark.anyio
    async def test_machines_no_key_returns_401(self):
        """GET /api/v1/machines without X-Internal-Key → 401."""
        _reset_store()
        app = _get_app_with_auth()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/machines")
        assert resp.status_code == 401

    @pytest.mark.anyio
    async def test_data_no_key_returns_401(self):
        """GET /api/v1/data without X-Internal-Key → 401."""
        _reset_store()
        app = _get_app_with_auth()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/data",
                params={
                    "address": "data://machine/channel/axis/machinePosition",
                    "filter": "machine=1&channel=1&axis=1",
                },
            )
        assert resp.status_code == 401

    @pytest.mark.anyio
    async def test_plc_no_key_returns_401(self):
        """GET /api/v1/plc without X-Internal-Key → 401."""
        _reset_store()
        app = _get_app_with_auth()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/plc",
                params={"machine": 1, "type": 1, "startAddress": 0, "count": 1},
            )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 4. Domain endpoints with valid auth → 200
# ---------------------------------------------------------------------------


class TestAuthValid:
    @pytest.mark.anyio
    async def test_machines_with_key_returns_200(self):
        """GET /api/v1/machines with correct X-Internal-Key → 200."""
        _reset_store()
        app = _get_app_with_auth("test-secret-key")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/machines",
                headers={"X-Internal-Key": "test-secret-key"},
            )
        assert resp.status_code == 200
        assert len(resp.json()["machines"]) == 2

    @pytest.mark.anyio
    async def test_data_with_key_returns_200(self):
        """GET /api/v1/data with correct X-Internal-Key → 200."""
        _reset_store()
        app = _get_app_with_auth("test-secret-key")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/data",
                params={
                    "address": "data://machine/channel/axis/machinePosition",
                    "filter": "machine=1&channel=1&axis=1",
                },
                headers={"X-Internal-Key": "test-secret-key"},
            )
        assert resp.status_code == 200
        assert resp.json()["success"] is True


# ---------------------------------------------------------------------------
# 5. MOCK_SKIP_AUTH mode (default for cell-mes test integration)
# ---------------------------------------------------------------------------


class TestSkipAuthMode:
    @pytest.mark.anyio
    async def test_machines_no_key_ok_in_skip_mode(self):
        """With MOCK_SKIP_AUTH=1, domain endpoints work without X-Internal-Key."""
        _reset_store()
        app = _get_app_skip_auth()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/machines")
        assert resp.status_code == 200
        assert len(resp.json()["machines"]) == 2

    @pytest.mark.anyio
    async def test_data_no_key_ok_in_skip_mode(self):
        """GET /api/v1/data works without auth in skip mode."""
        _reset_store()
        app = _get_app_skip_auth()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/data",
                params={
                    "address": "data://machine/channel/axis/axisName",
                    "filter": "machine=1&channel=1&axis=1",
                },
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["value"] == "X"

    @pytest.mark.anyio
    async def test_simulation_status_in_skip_mode(self):
        """GET /api/v1/simulation/status works without auth."""
        _reset_store()
        app = _get_app_skip_auth()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/simulation/status")
        assert resp.status_code == 200
        assert resp.json()["running"] is False
