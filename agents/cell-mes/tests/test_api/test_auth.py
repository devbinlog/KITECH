"""Tests for authentication endpoints."""

import pytest
from httpx import AsyncClient


class TestAuthLogin:
    """Test authentication login endpoint."""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user):
        """Valid credentials return JWT token."""
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": "testpassword"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        """Invalid password returns 401."""
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": "wrongpassword"},
        )

        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Non-existent user returns 401."""
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "nonexistent", "password": "password"},
        )

        assert response.status_code == 401


class TestAuthRegister:
    """Test user registration endpoint."""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        """New user registration succeeds."""
        response = await client.post(
            "/api/v1/auth/register",
            json={"username": "newuser", "password": "newpassword", "role": "OPERATOR"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["role"] == "OPERATOR"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client: AsyncClient, test_user):
        """Duplicate username returns 400."""
        response = await client.post(
            "/api/v1/auth/register",
            json={"username": "testuser", "password": "password", "role": "OPERATOR"},
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_short_password(self, client: AsyncClient):
        """Short password fails validation."""
        response = await client.post(
            "/api/v1/auth/register",
            json={"username": "newuser", "password": "short", "role": "OPERATOR"},
        )

        assert response.status_code == 422  # Validation error


class TestAuthMe:
    """Test current user endpoint."""

    @pytest.mark.asyncio
    async def test_get_current_user(self, client: AsyncClient, auth_headers):
        """Authenticated user can get their info."""
        response = await client.get("/api/v1/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["role"] == "OPERATOR"

    @pytest.mark.asyncio
    async def test_get_current_user_no_auth(self, client: AsyncClient):
        """Unauthenticated request returns 401."""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401


class TestInternalServiceAuth:
    """Test internal service key authentication for service-to-service calls."""

    @pytest.mark.asyncio
    async def test_internal_service_key_access(self, client: AsyncClient):
        """Valid internal service key grants access."""
        response = await client.get(
            "/api/v1/analytics/daily-status",
            headers={"X-Internal-Service-Key": "internal-service-key-change-in-production"},
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_invalid_internal_service_key(self, client: AsyncClient):
        """Invalid internal service key returns 401."""
        response = await client.get(
            "/api/v1/analytics/daily-status",
            headers={"X-Internal-Service-Key": "wrong-key"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_no_auth_returns_401(self, client: AsyncClient):
        """No authentication returns 401."""
        response = await client.get("/api/v1/analytics/daily-status")

        assert response.status_code == 401
