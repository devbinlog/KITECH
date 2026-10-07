"""Tests for /capabilities endpoint."""

import pytest
from httpx import AsyncClient


class TestCapabilities:
    """Tests for GET /capabilities."""

    @pytest.mark.asyncio
    async def test_capabilities_returns_200(self, client: AsyncClient):
        """Endpoint should return 200 without authentication."""
        response = await client.get("/capabilities")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_capabilities_no_auth_required(self, client: AsyncClient):
        """Metadata endpoint requires no auth token."""
        response = await client.get("/capabilities")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_capabilities_service_field(self, client: AsyncClient):
        """Response must identify service as cell-mes."""
        response = await client.get("/capabilities")
        data = response.json()
        assert data["service"] == "cell-mes"

    @pytest.mark.asyncio
    async def test_capabilities_has_version(self, client: AsyncClient):
        """Response must include a version string."""
        response = await client.get("/capabilities")
        data = response.json()
        assert "version" in data
        assert isinstance(data["version"], str)

    @pytest.mark.asyncio
    async def test_capabilities_has_description(self, client: AsyncClient):
        """Response must include a description."""
        response = await client.get("/capabilities")
        data = response.json()
        assert "description" in data

    @pytest.mark.asyncio
    async def test_capabilities_returns_tools_list(self, client: AsyncClient):
        """Response must include a tools list."""
        response = await client.get("/capabilities")
        data = response.json()
        assert "tools" in data
        assert isinstance(data["tools"], list)

    @pytest.mark.asyncio
    async def test_capabilities_minimum_tool_count(self, client: AsyncClient):
        """At least 5 tools must be exposed."""
        response = await client.get("/capabilities")
        data = response.json()
        assert len(data["tools"]) >= 5

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
            assert "method" in tool["endpoint"], f"Endpoint missing 'method': {tool}"
            assert "path" in tool["endpoint"], f"Endpoint missing 'path': {tool}"

    @pytest.mark.asyncio
    async def test_capabilities_tool_names_unique(self, client: AsyncClient):
        """Tool names must be unique."""
        response = await client.get("/capabilities")
        data = response.json()
        names = [t["name"] for t in data["tools"]]
        assert len(names) == len(set(names)), "Duplicate tool names found"

    @pytest.mark.asyncio
    async def test_capabilities_contains_expected_tools(self, client: AsyncClient):
        """Key tools must be present."""
        response = await client.get("/capabilities")
        data = response.json()
        names = {t["name"] for t in data["tools"]}
        expected = {
            "list_products",
            "list_equipments",
            "list_work_orders",
            "list_production_results",
            "list_alarms",
        }
        assert expected.issubset(names), f"Missing tools: {expected - names}"
