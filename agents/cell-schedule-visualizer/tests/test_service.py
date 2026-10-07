"""Tests for cell-schedule-visualizer FastAPI service.

Covers:
  - GET /health — 200, no auth required
  - GET /capabilities — 200, no auth required, expected tool listed
  - POST /api/v1/render — 200 + PNG bytes with valid key
  - POST /api/v1/render — 401 without auth key
  - POST /api/v1/render — SVG format
  - POST /api/v1/render — empty task list (graceful)
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure the workspace root (shared/) is importable during tests.
_workspace_root = Path(__file__).parent.parent.parent.parent
if str(_workspace_root) not in sys.path:
    sys.path.insert(0, str(_workspace_root))

import os

os.environ.setdefault("INTERNAL_SERVICE_KEY", "test-secret-key")

from fastapi.testclient import TestClient

from src.service import app  # noqa: E402 — import after env is set

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_INTERNAL_KEY = "test-secret-key"
_AUTH_HEADERS = {"X-Internal-Key": _INTERNAL_KEY}


@pytest.fixture(scope="module")
def client():
    """Reusable TestClient for the module."""
    return TestClient(app)


@pytest.fixture
def minimal_render_payload():
    """Minimal valid RenderRequest payload with two tasks."""
    return {
        "gantt_data": {
            "tasks": [
                {
                    "name": "WO-001 / OP10",
                    "start": "2025-01-17T08:00:00",
                    "end": "2025-01-17T09:00:00",
                    "resource": "MCH-001",
                    "priority": 1,
                    "color": "#4ECDC4",
                    "quantity": 50,
                    "duration_minutes": 60.0,
                },
                {
                    "name": "WO-002 / OP10",
                    "start": "2025-01-17T08:00:00",
                    "end": "2025-01-17T09:30:00",
                    "resource": "MCH-002",
                    "priority": 2,
                    "color": "#FF6B6B",
                    "quantity": 75,
                    "duration_minutes": 90.0,
                },
            ],
            "resources": ["MCH-001", "MCH-002"],
            "start": "2025-01-17T07:45:00",
            "end": "2025-01-17T10:00:00",
        },
        "title": "Test Schedule",
    }


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------


class TestHealth:
    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_no_auth_required(self, client):
        """Health endpoint must NOT require authentication."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_body(self, client):
        data = client.get("/health").json()
        assert data["status"] == "ok"
        assert data["service"] == "cell-schedule-visualizer"


# ---------------------------------------------------------------------------
# /capabilities
# ---------------------------------------------------------------------------


class TestCapabilities:
    def test_capabilities_returns_200(self, client):
        response = client.get("/capabilities")
        assert response.status_code == 200

    def test_capabilities_no_auth_required(self, client):
        response = client.get("/capabilities")
        assert response.status_code == 200

    def test_capabilities_lists_render_tool(self, client):
        data = client.get("/capabilities").json()
        tool_names = [t["name"] for t in data.get("tools", [])]
        assert "render_schedule" in tool_names

    def test_capabilities_schema(self, client):
        data = client.get("/capabilities").json()
        assert "service" in data
        assert "version" in data
        assert "tools" in data


# ---------------------------------------------------------------------------
# POST /api/v1/render — authentication
# ---------------------------------------------------------------------------


class TestRenderAuth:
    def test_render_without_key_returns_401(self, client, minimal_render_payload):
        """No auth header → 401."""
        response = client.post("/api/v1/render", json=minimal_render_payload)
        assert response.status_code == 401

    def test_render_wrong_key_returns_401(self, client, minimal_render_payload):
        """Wrong auth key → 401."""
        response = client.post(
            "/api/v1/render",
            json=minimal_render_payload,
            headers={"X-Internal-Key": "wrong-key"},
        )
        assert response.status_code == 401

    def test_render_with_valid_key_returns_200(self, client, minimal_render_payload):
        """Valid key → 200."""
        response = client.post(
            "/api/v1/render",
            json=minimal_render_payload,
            headers=_AUTH_HEADERS,
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# POST /api/v1/render — PNG output
# ---------------------------------------------------------------------------


class TestRenderPNG:
    def test_render_returns_png_content_type(self, client, minimal_render_payload):
        response = client.post(
            "/api/v1/render", json=minimal_render_payload, headers=_AUTH_HEADERS
        )
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("image/png")

    def test_render_returns_nonempty_bytes(self, client, minimal_render_payload):
        response = client.post(
            "/api/v1/render", json=minimal_render_payload, headers=_AUTH_HEADERS
        )
        assert len(response.content) > 0

    def test_render_png_magic_bytes(self, client, minimal_render_payload):
        """PNG files must start with the 8-byte PNG signature."""
        response = client.post(
            "/api/v1/render", json=minimal_render_payload, headers=_AUTH_HEADERS
        )
        # PNG magic: \x89PNG\r\n\x1a\n
        assert response.content[:4] == b"\x89PNG"


# ---------------------------------------------------------------------------
# POST /api/v1/render — SVG output
# ---------------------------------------------------------------------------


class TestRenderSVG:
    def test_render_svg_content_type(self, client, minimal_render_payload):
        payload = dict(minimal_render_payload, format="svg")
        response = client.post("/api/v1/render", json=payload, headers=_AUTH_HEADERS)
        assert response.status_code == 200
        assert "image/svg+xml" in response.headers["content-type"]

    def test_render_svg_contains_xml(self, client, minimal_render_payload):
        payload = dict(minimal_render_payload, format="svg")
        response = client.post("/api/v1/render", json=payload, headers=_AUTH_HEADERS)
        text = response.content.decode("utf-8", errors="replace")
        assert "<svg" in text


# ---------------------------------------------------------------------------
# POST /api/v1/render — edge cases
# ---------------------------------------------------------------------------


class TestRenderEdgeCases:
    def test_render_empty_task_list(self, client):
        """Empty task list should still produce a PNG (blank chart)."""
        payload = {
            "gantt_data": {
                "tasks": [],
                "resources": [],
                "start": "",
                "end": "",
            }
        }
        response = client.post("/api/v1/render", json=payload, headers=_AUTH_HEADERS)
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("image/png")

    def test_render_single_task(self, client):
        payload = {
            "gantt_data": {
                "tasks": [
                    {
                        "name": "WO-SINGLE",
                        "start": "2025-06-01T06:00:00",
                        "end": "2025-06-01T08:00:00",
                        "resource": "MCH-A",
                        "priority": 1,
                        "color": "#A8E6CF",
                        "quantity": 10,
                        "duration_minutes": 120.0,
                    }
                ],
                "resources": ["MCH-A"],
                "start": "2025-06-01T05:00:00",
                "end": "2025-06-01T09:00:00",
            },
            "title": "Single Task",
        }
        response = client.post("/api/v1/render", json=payload, headers=_AUTH_HEADERS)
        assert response.status_code == 200
        assert response.content[:4] == b"\x89PNG"

    def test_render_invalid_format_returns_422(self, client, minimal_render_payload):
        """Pydantic validation should reject unsupported format values."""
        payload = dict(minimal_render_payload, format="gif")
        response = client.post("/api/v1/render", json=payload, headers=_AUTH_HEADERS)
        assert response.status_code == 422
