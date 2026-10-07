"""Tests for monitoring-data-replayer FastAPI service.

Covers the mandatory 4-kind matrix from api-design-principles.md:
  - /health → 200
  - /capabilities → correct shape
  - core endpoint (POST /api/v1/replay) → 200 success, 400/422 bad input, 401 no auth
  - GET /api/v1/sessions, GET /api/v1/sessions/{id}, DELETE /api/v1/sessions/{id}
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure project root (containing shared/) is on sys.path so that
# `from shared.common.service_base import ...` resolves when running
# pytest from the agent directory.
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

os.environ.setdefault("INTERNAL_SERVICE_KEY", "test-secret")

from fastapi.testclient import TestClient

from src.service import app, _sessions

HEADERS = {"X-Internal-Key": "test-secret"}
BAD_HEADERS = {"X-Internal-Key": "wrong-key"}

client = TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _clear_sessions():
    _sessions.clear()


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------


class TestHealth:
    def test_health_200(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["service"] == "monitoring-data-replayer"

    def test_health_no_auth_required(self):
        """Health endpoint must not require authentication."""
        resp = client.get("/health")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# /capabilities
# ---------------------------------------------------------------------------


class TestCapabilities:
    def test_capabilities_200(self):
        resp = client.get("/capabilities")
        assert resp.status_code == 200

    def test_capabilities_shape(self):
        resp = client.get("/capabilities")
        body = resp.json()
        assert "service" in body
        assert "tools" in body
        tools = body["tools"]
        assert isinstance(tools, list)
        assert len(tools) >= 1
        names = [t["name"] for t in tools]
        assert "start_replay" in names

    def test_capabilities_no_auth_required(self):
        resp = client.get("/capabilities")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# POST /api/v1/replay — auth checks
# ---------------------------------------------------------------------------


class TestReplayAuth:
    def test_replay_401_no_key(self):
        resp = client.post("/api/v1/replay", json={"file_path": "/some/file.log"})
        assert resp.status_code == 401

    def test_replay_401_wrong_key(self):
        resp = client.post(
            "/api/v1/replay",
            json={"file_path": "/some/file.log"},
            headers=BAD_HEADERS,
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /api/v1/replay — input validation
# ---------------------------------------------------------------------------


class TestReplayValidation:
    def test_replay_422_missing_file_path(self):
        resp = client.post("/api/v1/replay", json={}, headers=HEADERS)
        assert resp.status_code == 422

    def test_replay_422_file_not_found(self):
        resp = client.post(
            "/api/v1/replay",
            json={"file_path": "/nonexistent/path/file.log"},
            headers=HEADERS,
        )
        assert resp.status_code == 422

    def test_replay_422_invalid_speed(self):
        """Speed must be > 0 (pydantic gt=0 constraint)."""
        resp = client.post(
            "/api/v1/replay",
            json={"file_path": "/some/file.log", "speed": -1.0},
            headers=HEADERS,
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/v1/replay — dry_run success (no real file needed via mock)
# ---------------------------------------------------------------------------


class TestReplayDryRun:
    def setup_method(self):
        _clear_sessions()

    def test_dry_run_returns_statistics(self, tmp_path):
        """dry_run=True returns statistics without starting a background task."""
        # Create a minimal temp .log file so path existence check passes
        log_file = tmp_path / "sample.log"
        log_file.write_text("timestamp\tcrpm\n2024-01-01T00:00:00\t1000\n")

        fake_stats = {
            "total_records": 1,
            "cutting_records": 0,
            "cutting_ratio": 0.0,
            "spindle_rpm": {"min": 1000.0, "max": 1000.0, "avg": 1000.0, "stdev": 0.0},
        }

        with patch(
            "src.service.MonitoringDataReplayerAgent.get_statistics",
            return_value=fake_stats,
        ):
            resp = client.post(
                "/api/v1/replay",
                json={"file_path": str(log_file), "dry_run": True},
                headers=HEADERS,
            )

        assert resp.status_code == 202
        body = resp.json()
        assert body["dry_run"] is True
        assert body["status"] == "completed"
        assert body["statistics"] is not None
        assert body["statistics"]["total_records"] == 1

    def test_dry_run_statistics_error_422(self, tmp_path):
        """dry_run with an unreadable file returns 422."""
        log_file = tmp_path / "bad.log"
        log_file.write_text("bad content")

        with patch(
            "src.service.MonitoringDataReplayerAgent.get_statistics",
            side_effect=ValueError("cannot parse file"),
        ):
            resp = client.post(
                "/api/v1/replay",
                json={"file_path": str(log_file), "dry_run": True},
                headers=HEADERS,
            )

        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/v1/replay — async session creation
# ---------------------------------------------------------------------------


class TestReplaySessionCreation:
    def setup_method(self):
        _clear_sessions()

    def test_replay_creates_session(self, tmp_path):
        """POST /replay with valid file starts a session and returns session_id."""
        log_file = tmp_path / "sample.log"
        log_file.write_text("data\n")

        # Patch agent replay to be an async no-op generator
        async def _noop_replay(*args, **kwargs):
            return
            yield  # make it an async generator

        with patch("src.service.MonitoringDataReplayerAgent.replay", _noop_replay):
            resp = client.post(
                "/api/v1/replay",
                json={"file_path": str(log_file), "speed": 10.0},
                headers=HEADERS,
            )

        assert resp.status_code == 202
        body = resp.json()
        assert "session_id" in body
        assert body["status"] == "running"
        assert body["speed"] == 10.0
        assert body["dry_run"] is False


# ---------------------------------------------------------------------------
# GET /api/v1/sessions
# ---------------------------------------------------------------------------


class TestListSessions:
    def setup_method(self):
        _clear_sessions()

    def test_list_sessions_401_no_auth(self):
        resp = client.get("/api/v1/sessions")
        assert resp.status_code == 401

    def test_list_sessions_empty(self):
        resp = client.get("/api/v1/sessions", headers=HEADERS)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 0
        assert body["sessions"] == []

    def test_list_sessions_contains_created(self, tmp_path):
        log_file = tmp_path / "s.log"
        log_file.write_text("data\n")

        async def _noop(*args, **kwargs):
            return
            yield

        with patch("src.service.MonitoringDataReplayerAgent.replay", _noop):
            client.post(
                "/api/v1/replay",
                json={"file_path": str(log_file)},
                headers=HEADERS,
            )

        resp = client.get("/api/v1/sessions", headers=HEADERS)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1


# ---------------------------------------------------------------------------
# GET /api/v1/sessions/{id}
# ---------------------------------------------------------------------------


class TestGetSession:
    def setup_method(self):
        _clear_sessions()

    def test_get_session_404_unknown(self):
        resp = client.get("/api/v1/sessions/nonexistent-id", headers=HEADERS)
        assert resp.status_code == 404

    def test_get_session_401_no_auth(self):
        resp = client.get("/api/v1/sessions/some-id")
        assert resp.status_code == 401

    def test_get_session_returns_status(self, tmp_path):
        log_file = tmp_path / "t.log"
        log_file.write_text("data\n")

        async def _noop(*args, **kwargs):
            return
            yield

        with patch("src.service.MonitoringDataReplayerAgent.replay", _noop):
            create_resp = client.post(
                "/api/v1/replay",
                json={"file_path": str(log_file)},
                headers=HEADERS,
            )
        session_id = create_resp.json()["session_id"]

        resp = client.get(f"/api/v1/sessions/{session_id}", headers=HEADERS)
        assert resp.status_code == 200
        body = resp.json()
        assert body["session_id"] == session_id
        assert body["file_path"] == str(log_file)


# ---------------------------------------------------------------------------
# DELETE /api/v1/sessions/{id}
# ---------------------------------------------------------------------------


class TestStopSession:
    def setup_method(self):
        _clear_sessions()

    def test_stop_session_404_unknown(self):
        resp = client.delete("/api/v1/sessions/nonexistent-id", headers=HEADERS)
        assert resp.status_code == 404

    def test_stop_session_401_no_auth(self):
        resp = client.delete("/api/v1/sessions/some-id")
        assert resp.status_code == 401

    def test_stop_running_session(self, tmp_path):
        """DELETE on a running session stops it and returns 204."""
        log_file = tmp_path / "r.log"
        log_file.write_text("data\n")

        async def _noop(*args, **kwargs):
            return
            yield

        with patch("src.service.MonitoringDataReplayerAgent.replay", _noop):
            create_resp = client.post(
                "/api/v1/replay",
                json={"file_path": str(log_file)},
                headers=HEADERS,
            )
        session_id = create_resp.json()["session_id"]

        # Force session into running state for the stop test
        from src.service import _sessions as sess

        if session_id in sess:
            sess[session_id]["status"] = "running"

        resp = client.delete(f"/api/v1/sessions/{session_id}", headers=HEADERS)
        assert resp.status_code == 204
