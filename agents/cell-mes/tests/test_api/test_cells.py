"""Tests for cells API endpoints."""

import pytest
from httpx import AsyncClient


class TestCellCRUD:
    """Cell CRUD tests."""

    @pytest.fixture
    async def cell_data(self):
        """Sample cell data."""
        return {"code": "CELL-01", "name": "CNC 가공 셀 1", "location": "A동 1층"}

    async def test_create_cell(self, client: AsyncClient, auth_headers: dict, cell_data: dict):
        """Test creating a cell."""
        response = await client.post(
            "/api/v1/masters/cells",
            json=cell_data,
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["code"] == cell_data["code"]
        assert data["name"] == cell_data["name"]
        assert data["location"] == cell_data["location"]
        assert "id" in data
        assert "created_at" in data

    async def test_create_cell_without_location(self, client: AsyncClient, auth_headers: dict):
        """Test creating a cell without location."""
        response = await client.post(
            "/api/v1/masters/cells",
            json={"code": "CELL-02", "name": "로봇 셀"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["location"] is None

    async def test_create_cell_duplicate_code(
        self, client: AsyncClient, auth_headers: dict, cell_data: dict
    ):
        """Test creating a cell with duplicate code fails."""
        # Create first
        await client.post(
            "/api/v1/masters/cells",
            json=cell_data,
            headers=auth_headers,
        )
        # Try to create duplicate
        response = await client.post(
            "/api/v1/masters/cells",
            json=cell_data,
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    async def test_list_cells(self, client: AsyncClient, auth_headers: dict, cell_data: dict):
        """Test listing cells."""
        # Create a cell first
        await client.post(
            "/api/v1/masters/cells",
            json=cell_data,
            headers=auth_headers,
        )
        response = await client.get(
            "/api/v1/masters/cells",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_get_cell(self, client: AsyncClient, auth_headers: dict, cell_data: dict):
        """Test getting a single cell."""
        # Create first
        create_response = await client.post(
            "/api/v1/masters/cells",
            json=cell_data,
            headers=auth_headers,
        )
        cell_id = create_response.json()["id"]

        # Get by ID
        response = await client.get(
            f"/api/v1/masters/cells/{cell_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == cell_id
        assert data["code"] == cell_data["code"]

    async def test_get_cell_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test getting non-existent cell returns 404."""
        response = await client.get(
            "/api/v1/masters/cells/99999",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_delete_cell(self, client: AsyncClient, auth_headers: dict, cell_data: dict):
        """Test deleting a cell."""
        # Create first
        create_response = await client.post(
            "/api/v1/masters/cells",
            json=cell_data,
            headers=auth_headers,
        )
        cell_id = create_response.json()["id"]

        # Delete
        response = await client.delete(
            f"/api/v1/masters/cells/{cell_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

        # Verify deleted
        get_response = await client.get(
            f"/api/v1/masters/cells/{cell_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404

    async def test_delete_cell_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test deleting non-existent cell returns 404."""
        response = await client.delete(
            "/api/v1/masters/cells/99999",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestCellValidation:
    """Cell validation tests."""

    async def test_create_cell_invalid_code(self, client: AsyncClient, auth_headers: dict):
        """Test creating cell with invalid code fails."""
        response = await client.post(
            "/api/v1/masters/cells",
            json={"code": "invalid code!", "name": "Test"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_create_cell_empty_code(self, client: AsyncClient, auth_headers: dict):
        """Test creating cell with empty code fails."""
        response = await client.post(
            "/api/v1/masters/cells",
            json={"code": "", "name": "Test"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_create_cell_empty_name(self, client: AsyncClient, auth_headers: dict):
        """Test creating cell with empty name fails."""
        response = await client.post(
            "/api/v1/masters/cells",
            json={"code": "TEST", "name": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422
