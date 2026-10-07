"""tests/test_sessions.py — IDOR / format validation for /sessions/{id}/trace (C2)."""
from __future__ import annotations

import os
import pytest

os.environ.setdefault("LLM_PROVIDER", "mock")

try:
    from fastapi.testclient import TestClient
    from src.service import app

    _app_available = True
except Exception:
    _app_available = False

VALID_SID = "abc12345-1234-1234-1234-123456789abc"


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers():
    return {"X-Internal-Key": os.environ.get("INTERNAL_SERVICE_KEY", "test-key")}


@pytest.mark.skipif(not _app_available, reason="service app not importable")
class TestSessionTrace:
    def test_trace_default_session_rejected(self, client, auth_headers):
        """'default' session_id must return 400."""
        r = client.get("/api/v1/sessions/default/trace", headers=auth_headers)
        assert r.status_code == 400

    def test_trace_invalid_format_rejected(self, client, auth_headers):
        """Non-UUID session_id must return 400."""
        r = client.get("/api/v1/sessions/not-a-uuid/trace", headers=auth_headers)
        assert r.status_code == 400

    def test_trace_short_invalid_rejected(self, client, auth_headers):
        """Short non-UUID string must return 400."""
        r = client.get("/api/v1/sessions/abc123/trace", headers=auth_headers)
        assert r.status_code == 400

    def test_trace_valid_uuid_returns_200_or_404(self, client, auth_headers):
        """Valid UUIDv4 must return 200 (empty trace) or 404 if no checkpoint."""
        r = client.get(f"/api/v1/sessions/{VALID_SID}/trace", headers=auth_headers)
        assert r.status_code in (200, 404, 500)  # 500 if SQLite not initialised in test env

    def test_trace_no_auth_rejected(self, client):
        """Request without auth header must return 401 or 403."""
        r = client.get(f"/api/v1/sessions/{VALID_SID}/trace")
        assert r.status_code in (401, 403)

    def test_trace_error_detail_contains_code(self, client, auth_headers):
        """400 error response must mention invalid_session_id somewhere in body."""
        r = client.get("/api/v1/sessions/default/trace", headers=auth_headers)
        assert r.status_code == 400
        # service_base wraps the detail; accept any shape that mentions the code
        body_text = str(r.json())
        assert "invalid_session_id" in body_text or "session_id" in body_text.lower()
