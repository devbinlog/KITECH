"""Tests for scenario management endpoints."""

import pytest
from httpx import AsyncClient


class TestScenarioList:
    """Test scenario list endpoint."""

    @pytest.mark.asyncio
    async def test_list_scenarios(self, client: AsyncClient, auth_headers, sample_scenario):
        """List all active scenarios."""
        response = await client.get("/api/v1/masters/scenarios", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Scenario"
        assert data[0]["is_active"] is True

    @pytest.mark.asyncio
    async def test_list_scenarios_by_product(
        self, client: AsyncClient, auth_headers, sample_scenario, sample_product
    ):
        """List scenarios filtered by product."""
        response = await client.get(
            f"/api/v1/masters/scenarios?product_id={sample_product.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["product_id"] == sample_product.id

    @pytest.mark.asyncio
    async def test_list_scenarios_include_inactive(
        self, client: AsyncClient, auth_headers, sample_scenario, db_session
    ):
        """List scenarios including inactive ones."""
        # Deactivate the scenario
        sample_scenario.is_active = False
        db_session.add(sample_scenario)
        await db_session.commit()

        # With active_only=True (default), should return empty
        response = await client.get("/api/v1/masters/scenarios", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) == 0

        # With active_only=False, should return the inactive scenario
        response = await client.get(
            "/api/v1/masters/scenarios?active_only=false",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert len(response.json()) == 1

    @pytest.mark.asyncio
    async def test_list_scenarios_unauthorized(self, client: AsyncClient):
        """Unauthorized request returns 401."""
        response = await client.get("/api/v1/masters/scenarios")

        assert response.status_code == 401


class TestScenarioCreate:
    """Test scenario creation endpoint."""

    @pytest.mark.asyncio
    async def test_create_scenario(self, client: AsyncClient, auth_headers, sample_product):
        """Create a new scenario."""
        response = await client.post(
            "/api/v1/masters/scenarios",
            headers=auth_headers,
            json={
                "code": "SCN-NEW-001",
                "name": "New Scenario",
                "product_id": sample_product.id,
                "file_path": "scenarios/new.xml",
                "is_active": True,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Scenario"
        assert data["product_id"] == sample_product.id
        assert data["file_path"] == "scenarios/new.xml"
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_create_scenario_without_product(self, client: AsyncClient, auth_headers):
        """Create a scenario without product_id."""
        response = await client.post(
            "/api/v1/masters/scenarios",
            headers=auth_headers,
            json={
                "code": "SCN-GENERIC-001",
                "name": "Generic Scenario",
                "file_path": "scenarios/generic.xml",
                "is_active": True,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Generic Scenario"
        assert data["product_id"] is None

    @pytest.mark.asyncio
    async def test_create_scenario_invalid_product(self, client: AsyncClient, auth_headers):
        """Create scenario with non-existent product returns 400."""
        response = await client.post(
            "/api/v1/masters/scenarios",
            headers=auth_headers,
            json={
                "code": "SCN-INVALID-001",
                "name": "Invalid Scenario",
                "product_id": 9999,
                "file_path": "scenarios/invalid.xml",
            },
        )

        assert response.status_code == 400
        assert "Product not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_scenario_unauthorized(self, client: AsyncClient):
        """Unauthorized request returns 401."""
        response = await client.post(
            "/api/v1/masters/scenarios",
            json={"name": "Test", "file_path": "test.xml"},
        )

        assert response.status_code == 401


class TestScenarioGet:
    """Test scenario get by ID endpoint."""

    @pytest.mark.asyncio
    async def test_get_scenario(self, client: AsyncClient, auth_headers, sample_scenario):
        """Get scenario by ID."""
        response = await client.get(
            f"/api/v1/masters/scenarios/{sample_scenario.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_scenario.id
        assert data["name"] == sample_scenario.name
        assert data["file_path"] == sample_scenario.file_path

    @pytest.mark.asyncio
    async def test_get_scenario_not_found(self, client: AsyncClient, auth_headers):
        """Non-existent scenario returns 404."""
        response = await client.get(
            "/api/v1/masters/scenarios/9999",
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert "Scenario not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_scenario_unauthorized(self, client: AsyncClient):
        """Unauthorized request returns 401."""
        response = await client.get("/api/v1/masters/scenarios/1")

        assert response.status_code == 401


class TestScenarioToggleActive:
    """Test scenario active status toggle endpoint."""

    @pytest.mark.asyncio
    async def test_toggle_scenario_active_deactivate(
        self, client: AsyncClient, auth_headers, sample_scenario
    ):
        """Deactivate a scenario."""
        assert sample_scenario.is_active is True

        response = await client.patch(
            f"/api/v1/masters/scenarios/{sample_scenario.id}/active?is_active=false",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

    @pytest.mark.asyncio
    async def test_toggle_scenario_active_activate(
        self, client: AsyncClient, auth_headers, sample_scenario, db_session
    ):
        """Activate an inactive scenario."""
        # First deactivate
        sample_scenario.is_active = False
        db_session.add(sample_scenario)
        await db_session.commit()

        response = await client.patch(
            f"/api/v1/masters/scenarios/{sample_scenario.id}/active?is_active=true",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_toggle_scenario_active_not_found(self, client: AsyncClient, auth_headers):
        """Toggle non-existent scenario returns 404."""
        response = await client.patch(
            "/api/v1/masters/scenarios/9999/active?is_active=true",
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert "Scenario not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_toggle_scenario_active_unauthorized(self, client: AsyncClient):
        """Unauthorized request returns 401."""
        response = await client.patch("/api/v1/masters/scenarios/1/active?is_active=false")

        assert response.status_code == 401


class TestScenarioDelete:
    """Test scenario deletion endpoint."""

    @pytest.mark.asyncio
    async def test_delete_scenario(self, client: AsyncClient, auth_headers, sample_scenario):
        """Delete a scenario."""
        response = await client.delete(
            f"/api/v1/masters/scenarios/{sample_scenario.id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        # Verify deletion
        response = await client.get(
            f"/api/v1/masters/scenarios/{sample_scenario.id}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_scenario_not_found(self, client: AsyncClient, auth_headers):
        """Delete non-existent scenario returns 404."""
        response = await client.delete(
            "/api/v1/masters/scenarios/9999",
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert "Scenario not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_scenario_unauthorized(self, client: AsyncClient):
        """Unauthorized request returns 401."""
        response = await client.delete("/api/v1/masters/scenarios/1")

        assert response.status_code == 401
