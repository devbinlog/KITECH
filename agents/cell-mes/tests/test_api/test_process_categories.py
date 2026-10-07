"""Tests for process categories API endpoints."""

import pytest
from httpx import AsyncClient


class TestProcessCategoryCRUD:
    """Process category CRUD tests."""

    @pytest.fixture
    async def category_data(self):
        """Sample category data."""
        return {"code": "MACHINING", "name": "기계가공"}

    async def test_create_process_category(
        self, client: AsyncClient, auth_headers: dict, category_data: dict
    ):
        """Test creating a process category."""
        response = await client.post(
            "/api/v1/masters/process-categories",
            json=category_data,
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["code"] == category_data["code"]
        assert data["name"] == category_data["name"]
        assert "id" in data
        assert "created_at" in data

    async def test_create_process_category_duplicate_code(
        self, client: AsyncClient, auth_headers: dict, category_data: dict
    ):
        """Test creating a category with duplicate code fails."""
        # Create first
        await client.post(
            "/api/v1/masters/process-categories",
            json=category_data,
            headers=auth_headers,
        )
        # Try to create duplicate
        response = await client.post(
            "/api/v1/masters/process-categories",
            json=category_data,
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    async def test_list_process_categories(
        self, client: AsyncClient, auth_headers: dict, category_data: dict
    ):
        """Test listing process categories."""
        # Create a category first
        await client.post(
            "/api/v1/masters/process-categories",
            json=category_data,
            headers=auth_headers,
        )
        response = await client.get(
            "/api/v1/masters/process-categories",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_get_process_category(
        self, client: AsyncClient, auth_headers: dict, category_data: dict
    ):
        """Test getting a single process category."""
        # Create first
        create_response = await client.post(
            "/api/v1/masters/process-categories",
            json=category_data,
            headers=auth_headers,
        )
        category_id = create_response.json()["id"]

        # Get by ID
        response = await client.get(
            f"/api/v1/masters/process-categories/{category_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == category_id
        assert data["code"] == category_data["code"]

    async def test_get_process_category_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test getting non-existent category returns 404."""
        response = await client.get(
            "/api/v1/masters/process-categories/99999",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_delete_process_category(
        self, client: AsyncClient, auth_headers: dict, category_data: dict
    ):
        """Test deleting a process category."""
        # Create first
        create_response = await client.post(
            "/api/v1/masters/process-categories",
            json=category_data,
            headers=auth_headers,
        )
        category_id = create_response.json()["id"]

        # Delete
        response = await client.delete(
            f"/api/v1/masters/process-categories/{category_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

        # Verify deleted
        get_response = await client.get(
            f"/api/v1/masters/process-categories/{category_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404

    async def test_delete_process_category_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test deleting non-existent category returns 404."""
        response = await client.delete(
            "/api/v1/masters/process-categories/99999",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestProcessCategoryValidation:
    """Process category validation tests."""

    async def test_create_category_invalid_code(self, client: AsyncClient, auth_headers: dict):
        """Test creating category with invalid code fails."""
        response = await client.post(
            "/api/v1/masters/process-categories",
            json={"code": "invalid code!", "name": "Test"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_create_category_empty_code(self, client: AsyncClient, auth_headers: dict):
        """Test creating category with empty code fails."""
        response = await client.post(
            "/api/v1/masters/process-categories",
            json={"code": "", "name": "Test"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_create_category_empty_name(self, client: AsyncClient, auth_headers: dict):
        """Test creating category with empty name fails."""
        response = await client.post(
            "/api/v1/masters/process-categories",
            json={"code": "TEST", "name": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422
