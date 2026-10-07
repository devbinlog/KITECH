"""Tests for gcode-parser FastAPI service (service.py).

Uses starlette.testclient.TestClient (sync) to avoid pytest-asyncio dependency.

Coverage:
  - /health         → 200, no auth required
  - /capabilities   → 200, correct shape (service/version/tools keys)
  - POST /api/v1/parse without X-Internal-Key → 401
  - POST /api/v1/parse with wrong key → 401
  - POST /api/v1/parse with correct key, valid G-code → 200 + ParseResponse
  - POST /api/v1/parse with empty gcode → 422 (Pydantic min_length validation)
  - POST /api/v1/parse with missing gcode field → 422
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Resolve paths
_gcode_parser_dir = Path(__file__).parent.parent  # agents/gcode-parser/
_workspace_root = _gcode_parser_dir.parent.parent  # workspace root

# Insert gcode-parser dir FIRST so its `src` package takes precedence over
# orchestrator/src (which the root pyproject.toml adds via pythonpath).
if str(_gcode_parser_dir) not in sys.path:
    sys.path.insert(0, str(_gcode_parser_dir))

# Workspace root must also be present so `shared.common` is importable.
if str(_workspace_root) not in sys.path:
    sys.path.insert(1, str(_workspace_root))

# Set the key BEFORE importing the app so require_internal can read it.
_TEST_KEY = "test-internal-key-abc123"
os.environ["INTERNAL_SERVICE_KEY"] = _TEST_KEY

from starlette.testclient import TestClient  # noqa: E402

from src.service import app  # noqa: E402

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SIMPLE_GCODE = """
G90
G00 X10 Y20
G01 Z-5 F100
M05
"""


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers() -> dict:
    return {"X-Internal-Key": _TEST_KEY}


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


def test_health_no_auth(client):
    """GET /health returns 200 with no authentication."""
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"] == "gcode-parser"


# ---------------------------------------------------------------------------
# Capabilities
# ---------------------------------------------------------------------------


def test_capabilities_shape(client):
    """GET /capabilities returns service/version/tools keys."""
    resp = client.get("/capabilities")
    assert resp.status_code == 200
    body = resp.json()
    assert "service" in body
    assert "version" in body
    assert "tools" in body
    assert isinstance(body["tools"], list)
    assert len(body["tools"]) >= 1
    tool = body["tools"][0]
    assert "name" in tool
    assert "description" in tool
    assert "endpoint" in tool


# ---------------------------------------------------------------------------
# Auth guard
# ---------------------------------------------------------------------------


def test_parse_no_auth_returns_401(client):
    """POST /api/v1/parse without X-Internal-Key returns 401."""
    resp = client.post("/api/v1/parse", json={"gcode": SIMPLE_GCODE})
    assert resp.status_code == 401


def test_parse_wrong_key_returns_401(client):
    """POST /api/v1/parse with wrong key returns 401."""
    resp = client.post(
        "/api/v1/parse",
        json={"gcode": SIMPLE_GCODE},
        headers={"X-Internal-Key": "wrong-key"},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Domain endpoint — success path
# ---------------------------------------------------------------------------


def test_parse_valid_gcode_returns_200(client, auth_headers):
    """POST /api/v1/parse with valid key and G-code returns 200 with ParseResponse shape."""
    resp = client.post(
        "/api/v1/parse",
        json={"gcode": SIMPLE_GCODE},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "blocks" in body
    assert "total_distance_mm" in body
    assert "machine_time_sec" in body
    assert "rapid_distance_mm" in body
    assert "cutting_distance_mm" in body
    assert "spindle_speed" in body
    assert "feed_rate" in body
    assert "total_commands" in body
    assert isinstance(body["blocks"], list)
    assert isinstance(body["total_distance_mm"], float)


def test_parse_distance_calculation(client, auth_headers):
    """G01 X30 Y40 from origin produces cutting_distance_mm ≈ 50."""
    gcode = "G90\nG00 X0 Y0 Z0\nG01 X30 Y40 F1000\n"
    resp = client.post("/api/v1/parse", json={"gcode": gcode}, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_distance_mm"] > 0
    assert abs(body["cutting_distance_mm"] - 50.0) < 0.5


def test_parse_gcode_block_structure(client, auth_headers):
    """Each block in the response has the expected keys."""
    gcode = "G90\nG00 X10 Y10 Z5\n"
    resp = client.post("/api/v1/parse", json={"gcode": gcode}, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    if body["blocks"]:
        block = body["blocks"][0]
        assert "command" in block
        assert "start_position" in block
        assert "end_position" in block
        assert "distance" in block
        assert "is_cutting" in block


# ---------------------------------------------------------------------------
# Validation — bad input
# ---------------------------------------------------------------------------


def test_parse_empty_gcode_returns_422(client, auth_headers):
    """POST /api/v1/parse with empty string fails Pydantic min_length → 422."""
    resp = client.post("/api/v1/parse", json={"gcode": ""}, headers=auth_headers)
    assert resp.status_code == 422


def test_parse_missing_gcode_field_returns_422(client, auth_headers):
    """POST /api/v1/parse with missing gcode field → 422."""
    resp = client.post("/api/v1/parse", json={}, headers=auth_headers)
    assert resp.status_code == 422
