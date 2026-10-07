"""tests/test_chat_ws.py — WebSocket /ws/chat auth + message flow tests (C5)."""
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

INTERNAL_KEY = "test-internal-key"
VALID_SID = "abc12345-1234-1234-1234-123456789abc"


@pytest.fixture(autouse=True)
def _set_key(monkeypatch):
    monkeypatch.setenv("INTERNAL_SERVICE_KEY", INTERNAL_KEY)


@pytest.mark.skipif(not _app_available, reason="service app not importable")
class TestWsChatAuth:
    def test_ws_chat_no_key_rejected(self):
        """Connection with no key must be closed before accept (1008)."""
        client = TestClient(app, raise_server_exceptions=False)
        with pytest.raises(Exception):
            with client.websocket_connect("/ws/chat") as ws:
                ws.receive_json()

    def test_ws_chat_wrong_key_rejected(self):
        """Connection with wrong key must be closed before accept."""
        client = TestClient(app, raise_server_exceptions=False)
        with pytest.raises(Exception):
            with client.websocket_connect("/ws/chat?key=wrong-key") as ws:
                ws.receive_json()

    def test_ws_chat_valid_key_accepts(self):
        """Connection with correct key must be accepted and respond."""
        client = TestClient(app, raise_server_exceptions=False)
        with client.websocket_connect(f"/ws/chat?key={INTERNAL_KEY}") as ws:
            ws.send_json({"session_id": VALID_SID, "message": "hello"})
            msgs = []
            for _ in range(10):
                try:
                    msg = ws.receive_json()
                    msgs.append(msg)
                    if msg.get("type") == "done":
                        break
                except Exception:
                    break
        assert any(m.get("type") in ("chunk", "message", "done", "error") for m in msgs)

    def test_ws_chat_invalid_session_id_rejected(self):
        """Non-UUIDv4 session_id must produce an error message (not close)."""
        client = TestClient(app, raise_server_exceptions=False)
        with client.websocket_connect(f"/ws/chat?key={INTERNAL_KEY}") as ws:
            ws.send_json({"session_id": "default", "message": "hello"})
            msg = ws.receive_json()
        assert msg.get("type") == "error"
        assert "session_id" in str(msg).lower() or "uuid" in str(msg).lower()

    def test_ws_chat_auto_generates_session_id(self):
        """When session_id is omitted, server auto-generates one (no error)."""
        client = TestClient(app, raise_server_exceptions=False)
        with client.websocket_connect(f"/ws/chat?key={INTERNAL_KEY}") as ws:
            ws.send_json({"message": "ping"})
            msgs = []
            for _ in range(10):
                try:
                    msg = ws.receive_json()
                    msgs.append(msg)
                    if msg.get("type") in ("done", "error"):
                        break
                except Exception:
                    break
        # Must not receive invalid_session_id error
        assert not any(
            m.get("code") == "invalid_session_id" for m in msgs
        )
