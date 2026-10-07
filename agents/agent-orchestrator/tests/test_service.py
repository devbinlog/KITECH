"""test_service.py — FastAPI service smoke tests."""
import os
import pytest

os.environ.setdefault("LLM_PROVIDER", "mock")

try:
    from fastapi.testclient import TestClient
    from src.service import app

    _app_available = True
except Exception:
    _app_available = False


@pytest.mark.skipif(not _app_available, reason="service app not importable")
class TestServiceEndpoints:
    @pytest.fixture(autouse=True)
    def client(self):
        self._client = TestClient(app)

    def test_health(self):
        r = self._client.get("/health")
        assert r.status_code == 200
        assert r.json().get("status") == "ok"

    def test_health_full(self):
        r = self._client.get("/health/full")
        assert r.status_code == 200
        data = r.json()
        assert "llm_status" in data

    def test_capabilities(self):
        r = self._client.get("/capabilities")
        assert r.status_code == 200
        assert "tools" in r.json()

    def test_docs_accessible(self):
        r = self._client.get("/docs")
        assert r.status_code == 200
