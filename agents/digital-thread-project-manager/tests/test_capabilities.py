"""Tests for /health and /capabilities endpoints in DTP server."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock


@pytest_asyncio.fixture
async def client():
    """Create an async test client for the DTP FastAPI app."""
    # Patch MongoDB startup so tests run without a real DB connection
    with patch(
        "src.database.get_db",
        new_callable=AsyncMock,
        return_value=AsyncMock(),
    ), patch(
        "src.database.ensure_asset_indexes",
        new_callable=AsyncMock,
        return_value=None,
    ):
        from src.server import app
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


class TestHealth:
    """Tests for GET /health."""

    @pytest.mark.asyncio
    async def test_health_returns_200(self, client: AsyncClient):
        """Health endpoint must return 200."""
        response = await client.get("/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_service_field(self, client: AsyncClient):
        """Response must identify service as dtp."""
        response = await client.get("/health")
        data = response.json()
        assert data["service"] == "dtp"

    @pytest.mark.asyncio
    async def test_health_status_ok(self, client: AsyncClient):
        """Response status must be ok."""
        response = await client.get("/health")
        data = response.json()
        assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_health_has_version(self, client: AsyncClient):
        """Response must include a version string."""
        response = await client.get("/health")
        data = response.json()
        assert "version" in data


class TestCapabilities:
    """Tests for GET /capabilities."""

    @pytest.mark.asyncio
    async def test_capabilities_returns_200(self, client: AsyncClient):
        """Capabilities endpoint must return 200."""
        response = await client.get("/capabilities")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_capabilities_no_auth_required(self, client: AsyncClient):
        """Metadata endpoint requires no auth token."""
        response = await client.get("/capabilities")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_capabilities_service_field(self, client: AsyncClient):
        """Response must identify service as dtp."""
        response = await client.get("/capabilities")
        data = response.json()
        assert data["service"] == "dtp"

    @pytest.mark.asyncio
    async def test_capabilities_has_tools_list(self, client: AsyncClient):
        """Response must include a tools list."""
        response = await client.get("/capabilities")
        data = response.json()
        assert "tools" in data
        assert isinstance(data["tools"], list)

    @pytest.mark.asyncio
    async def test_capabilities_minimum_tool_count(self, client: AsyncClient):
        """At least 3 tools must be exposed."""
        response = await client.get("/capabilities")
        data = response.json()
        assert len(data["tools"]) >= 3

    @pytest.mark.asyncio
    async def test_capabilities_tool_structure(self, client: AsyncClient):
        """Each tool must have name, description, endpoint, and idempotent fields."""
        response = await client.get("/capabilities")
        data = response.json()
        for tool in data["tools"]:
            assert "name" in tool, f"Tool missing 'name': {tool}"
            assert "description" in tool, f"Tool missing 'description': {tool}"
            assert "endpoint" in tool, f"Tool missing 'endpoint': {tool}"
            assert "idempotent" in tool, f"Tool missing 'idempotent': {tool}"

    @pytest.mark.asyncio
    async def test_capabilities_contains_expected_tools(self, client: AsyncClient):
        """Key tools must be present."""
        response = await client.get("/capabilities")
        data = response.json()
        names = {t["name"] for t in data["tools"]}
        expected = {"get_projects", "create_project", "upload_project_to_dp"}
        assert expected.issubset(names), f"Missing tools: {expected - names}"
