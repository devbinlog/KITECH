"""Tests for /capabilities endpoint."""

import sys
from pathlib import Path

import pytest
from httpx import AsyncClient, ASGITransport

# Add agents/cell-scheduler as package root so relative imports in src work
workspace = Path(__file__).parent.parent.parent.parent
agent_root = workspace / "agents" / "cell-scheduler"
sys.path.insert(0, str(agent_root))
sys.path.insert(0, str(workspace / "shared"))

from src.app.main import app  # noqa: E402


@pytest.mark.asyncio
async def test_capabilities():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get("/capabilities")
    assert r.status_code == 200
    data = r.json()
    assert data["service"] == "cell-scheduler"
    assert isinstance(data["tools"], list)
    assert len(data["tools"]) > 0


@pytest.mark.asyncio
async def test_capabilities_no_auth():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get("/capabilities")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_capabilities_structure():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get("/capabilities")
    data = r.json()
    assert "version" in data
    assert "description" in data
    for tool in data["tools"]:
        assert "name" in tool
        assert "description" in tool
        assert "endpoint" in tool
        assert "method" in tool["endpoint"]
        assert "path" in tool["endpoint"]
