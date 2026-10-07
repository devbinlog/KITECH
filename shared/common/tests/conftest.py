"""Shared fixtures for shared/common unit tests."""
import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _set_internal_key(monkeypatch):
    """Ensure INTERNAL_SERVICE_KEY is always set so require_internal works."""
    monkeypatch.setenv("INTERNAL_SERVICE_KEY", "test-internal-key")


@pytest.fixture
def auth_headers():
    """Valid internal auth headers."""
    return {"X-Internal-Key": "test-internal-key"}


@pytest.fixture
def app():
    """Minimal FastAPI app created via create_app."""
    from shared.common.service_base import create_app, make_capability

    return create_app(
        name="test-service",
        version="0.0.1",
        description="test",
        capabilities=[
            make_capability(name="ping", description="test", path="/ping")
        ],
    )


@pytest.fixture
def client(app):
    """Synchronous TestClient wrapping the test app."""
    return TestClient(app, raise_server_exceptions=False)
