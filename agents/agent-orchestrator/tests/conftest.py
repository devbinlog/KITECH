"""conftest.py — Shared fixtures for agent-orchestrator tests."""
import os
import pytest

# Force mock LLM so tests never hit real providers
os.environ.setdefault("LLM_PROVIDER", "mock")
os.environ.setdefault("INTERNAL_SERVICE_KEY", "test-key")


@pytest.fixture
def auth_headers() -> dict:
    """Return minimal auth headers for TestClient requests."""
    return {"X-Internal-Key": "test-key"}


@pytest.fixture
def anyio_backend():
    return "asyncio"
