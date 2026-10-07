"""Tests for cam-runner FastAPI service (src/service.py).

Covers the minimum required by api-design-principles.md:
  - /health → 200 (no auth)
  - /capabilities → 200, valid shape (no auth)
  - POST /api/v1/analyze → 200 with valid payload + auth
  - POST /api/v1/analyze → 401 without auth
  - POST /api/v1/analyze → 422 with bad payload
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Path setup — mirror conftest.py conventions for this package
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Set the shared secret before importing the app so require_internal works
_TEST_KEY = "test-internal-key-cam"
os.environ["INTERNAL_SERVICE_KEY"] = _TEST_KEY

from service import app  # noqa: E402  (must come after env setup)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client() -> TestClient:
    """TestClient with shared app instance."""
    return TestClient(app, raise_server_exceptions=True)


@pytest.fixture
def auth_headers() -> Dict[str, str]:
    return {"X-Internal-Key": _TEST_KEY}


@pytest.fixture
def simple_analyze_payload() -> Dict[str, Any]:
    """Minimal valid AnalyzeRequest body."""
    return {
        "gcode_blocks": [
            {
                "command": "G00",
                "start_position": {"X": 0, "Y": 0, "Z": 10},
                "end_position": {"X": 10, "Y": 10, "Z": 10},
                "is_cutting": False,
            },
            {
                "command": "G01",
                "start_position": {"X": 10, "Y": 10, "Z": 10},
                "end_position": {"X": 10, "Y": 10, "Z": 0},
                "is_cutting": True,
            },
            {
                "command": "G01",
                "start_position": {"X": 10, "Y": 10, "Z": 0},
                "end_position": {"X": 30, "Y": 50, "Z": 0},
                "is_cutting": True,
            },
        ],
        "cutting_distance": 50.0,
        "rapid_distance": 20.0,
        "feed_rate": 600.0,
        "dwell_time": 0.0,
    }


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------


class TestHealth:
    def test_health_200(self, client: TestClient) -> None:
        """Health endpoint returns 200 without auth."""
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_body(self, client: TestClient) -> None:
        body = client.get("/health").json()
        assert body["status"] == "ok"
        assert body["service"] == "cam-runner"
        assert "version" in body


# ---------------------------------------------------------------------------
# /capabilities
# ---------------------------------------------------------------------------


class TestCapabilities:
    def test_capabilities_200(self, client: TestClient) -> None:
        resp = client.get("/capabilities")
        assert resp.status_code == 200

    def test_capabilities_shape(self, client: TestClient) -> None:
        body = client.get("/capabilities").json()
        assert "service" in body
        assert "tools" in body
        assert isinstance(body["tools"], list)
        assert len(body["tools"]) >= 1

    def test_capabilities_has_analyze(self, client: TestClient) -> None:
        body = client.get("/capabilities").json()
        names: List[str] = [t["name"] for t in body["tools"]]
        assert "analyze_cam_path" in names


# ---------------------------------------------------------------------------
# POST /api/v1/analyze — authentication
# ---------------------------------------------------------------------------


class TestAnalyzeAuth:
    def test_no_auth_returns_401(
        self, client: TestClient, simple_analyze_payload: Dict[str, Any]
    ) -> None:
        """Missing X-Internal-Key must return 401."""
        resp = client.post("/api/v1/analyze", json=simple_analyze_payload)
        assert resp.status_code == 401

    def test_wrong_key_returns_401(
        self, client: TestClient, simple_analyze_payload: Dict[str, Any]
    ) -> None:
        resp = client.post(
            "/api/v1/analyze",
            json=simple_analyze_payload,
            headers={"X-Internal-Key": "wrong-key"},
        )
        assert resp.status_code == 401

    def test_valid_auth_returns_200(
        self,
        client: TestClient,
        auth_headers: Dict[str, str],
        simple_analyze_payload: Dict[str, Any],
    ) -> None:
        resp = client.post(
            "/api/v1/analyze", json=simple_analyze_payload, headers=auth_headers
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# POST /api/v1/analyze — response shape
# ---------------------------------------------------------------------------


class TestAnalyzeResponse:
    def test_response_has_required_fields(
        self,
        client: TestClient,
        auth_headers: Dict[str, str],
        simple_analyze_payload: Dict[str, Any],
    ) -> None:
        body = client.post(
            "/api/v1/analyze", json=simple_analyze_payload, headers=auth_headers
        ).json()
        assert "status" in body
        assert "message" in body
        assert "summary" in body
        assert "cycle_time" in body
        assert "paths" in body
        assert "total_segments" in body

    def test_status_is_success(
        self,
        client: TestClient,
        auth_headers: Dict[str, str],
        simple_analyze_payload: Dict[str, Any],
    ) -> None:
        body = client.post(
            "/api/v1/analyze", json=simple_analyze_payload, headers=auth_headers
        ).json()
        assert body["status"] in ("success", "warning")

    def test_cycle_time_fields(
        self,
        client: TestClient,
        auth_headers: Dict[str, str],
        simple_analyze_payload: Dict[str, Any],
    ) -> None:
        body = client.post(
            "/api/v1/analyze", json=simple_analyze_payload, headers=auth_headers
        ).json()
        ct = body["cycle_time"]
        for field in (
            "cutting_time_sec",
            "rapid_time_sec",
            "dwell_time_sec",
            "tool_change_time_sec",
            "total_cycle_time_sec",
            "total_cycle_time_min",
            "tool_change_count",
        ):
            assert field in ct, f"Missing cycle_time field: {field}"

    def test_summary_fields(
        self,
        client: TestClient,
        auth_headers: Dict[str, str],
        simple_analyze_payload: Dict[str, Any],
    ) -> None:
        body = client.post(
            "/api/v1/analyze", json=simple_analyze_payload, headers=auth_headers
        ).json()
        s = body["summary"]
        assert "total_paths" in s
        assert "cutting_segments" in s
        assert "tool_id" in s
        assert "tool_name" in s

    def test_summary_counts(
        self,
        client: TestClient,
        auth_headers: Dict[str, str],
        simple_analyze_payload: Dict[str, Any],
    ) -> None:
        """3 blocks submitted → total_paths == 3, cutting_segments == 2."""
        body = client.post(
            "/api/v1/analyze", json=simple_analyze_payload, headers=auth_headers
        ).json()
        s = body["summary"]
        assert s["total_paths"] == 3
        assert s["cutting_segments"] == 2


# ---------------------------------------------------------------------------
# POST /api/v1/analyze — cycle time calculation accuracy
# ---------------------------------------------------------------------------


class TestAnalyzeCycleTimeAccuracy:
    def test_cutting_time_calculation(
        self, client: TestClient, auth_headers: Dict[str, str]
    ) -> None:
        """cutting_time = cutting_distance / feed_rate * 60."""
        payload = {
            "gcode_blocks": [
                {
                    "command": "G01",
                    "start_position": {"X": 0, "Y": 0, "Z": 0},
                    "end_position": {"X": 100, "Y": 0, "Z": 0},
                    "is_cutting": True,
                }
            ],
            "cutting_distance": 600.0,
            "rapid_distance": 100.0,
            "feed_rate": 600.0,
            "dwell_time": 5.0,
        }
        body = client.post(
            "/api/v1/analyze", json=payload, headers=auth_headers
        ).json()
        ct = body["cycle_time"]
        assert ct["cutting_time_sec"] == 60.0   # 600/600*60
        assert ct["rapid_time_sec"] == 1.2       # 100/5000*60
        assert ct["dwell_time_sec"] == 5.0

    def test_total_cycle_time_components(
        self, client: TestClient, auth_headers: Dict[str, str]
    ) -> None:
        payload = {
            "gcode_blocks": [
                {
                    "command": "G01",
                    "start_position": {"X": 0, "Y": 0, "Z": 0},
                    "end_position": {"X": 10, "Y": 0, "Z": 0},
                    "is_cutting": True,
                }
            ],
            "cutting_distance": 0.0,
            "rapid_distance": 0.0,
            "feed_rate": 500.0,
            "dwell_time": 0.0,
        }
        body = client.post(
            "/api/v1/analyze", json=payload, headers=auth_headers
        ).json()
        ct = body["cycle_time"]
        assert ct["total_cycle_time_sec"] >= 0.0
        assert ct["total_cycle_time_min"] == round(ct["total_cycle_time_sec"] / 60, 2)


# ---------------------------------------------------------------------------
# POST /api/v1/analyze — input validation
# ---------------------------------------------------------------------------


class TestAnalyzeValidation:
    def test_missing_gcode_blocks_field_returns_422(
        self, client: TestClient, auth_headers: Dict[str, str]
    ) -> None:
        """gcode_blocks is required — omitting it must 422."""
        resp = client.post(
            "/api/v1/analyze",
            json={"cutting_distance": 10.0},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_empty_gcode_blocks_returns_200(
        self, client: TestClient, auth_headers: Dict[str, str]
    ) -> None:
        """Empty list is valid input; agent returns warning status."""
        payload = {"gcode_blocks": [], "cutting_distance": 0.0, "feed_rate": 500.0}
        resp = client.post("/api/v1/analyze", json=payload, headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] in ("success", "warning")

    def test_zero_feed_rate_rejected(
        self, client: TestClient, auth_headers: Dict[str, str]
    ) -> None:
        """feed_rate must be > 0 (gt=0 constraint)."""
        payload = {
            "gcode_blocks": [],
            "feed_rate": 0.0,
        }
        resp = client.post("/api/v1/analyze", json=payload, headers=auth_headers)
        assert resp.status_code == 422

    def test_flat_position_format_accepted(
        self, client: TestClient, auth_headers: Dict[str, str]
    ) -> None:
        """Flat start_x / end_x position format must be accepted."""
        payload = {
            "gcode_blocks": [
                {
                    "command": "G01",
                    "start_x": 0.0,
                    "start_y": 0.0,
                    "start_z": 10.0,
                    "end_x": 10.0,
                    "end_y": 10.0,
                    "end_z": 5.0,
                    "is_cutting": True,
                }
            ],
            "cutting_distance": 15.0,
            "feed_rate": 400.0,
        }
        resp = client.post("/api/v1/analyze", json=payload, headers=auth_headers)
        assert resp.status_code == 200

    def test_arc_blocks_accepted(
        self, client: TestClient, auth_headers: Dict[str, str]
    ) -> None:
        """Arc blocks (G02/G03) with I/J parameters must be accepted."""
        payload = {
            "gcode_blocks": [
                {
                    "command": "G02",
                    "start_position": {"X": 50, "Y": 0, "Z": 0},
                    "end_position": {"X": 100, "Y": 50, "Z": 0},
                    "parameters": {"I": 50, "J": 0},
                    "is_cutting": True,
                }
            ],
            "cutting_distance": 78.5,
            "feed_rate": 300.0,
        }
        resp = client.post("/api/v1/analyze", json=payload, headers=auth_headers)
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Import smoke test
# ---------------------------------------------------------------------------


class TestImportSmoke:
    def test_app_importable(self) -> None:
        """Verify the service module exports a FastAPI app."""
        from service import app as svc_app  # noqa: F401
        from fastapi import FastAPI
        assert isinstance(svc_app, FastAPI)

    def test_capabilities_declared(self) -> None:
        from service import CAPABILITIES
        assert len(CAPABILITIES) >= 1
        cap = CAPABILITIES[0]
        assert cap["name"] == "analyze_cam_path"
        assert cap["endpoint"]["path"] == "/api/v1/analyze"
