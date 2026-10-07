"""Integration tests for NL-Router ↔ Cell-MES communication

These tests require running services:
- Cell-MES on port 8080
- NL-Router on port 8001

Run with: pytest tests/integration/test_nlrouter_mes_integration.py -v
"""

import pytest
import httpx


# Skip all tests if services are not running
pytestmark = pytest.mark.integration


class TestNLRouterMESIntegration:
    """Test NL-Router to Cell-MES API integration"""

    @pytest.fixture
    def mes_url(self):
        return "http://localhost:8080"

    @pytest.fixture
    def nlrouter_url(self):
        return "http://localhost:8001"

    @pytest.fixture
    def internal_service_key(self):
        return "internal-service-key-change-in-production"

    @pytest.mark.asyncio
    async def test_services_health(self, mes_url, nlrouter_url):
        """Test that both services are running"""
        async with httpx.AsyncClient() as client:
            # Cell-MES health
            mes_response = await client.get(f"{mes_url}/health", timeout=5.0)
            assert mes_response.status_code == 200
            assert mes_response.json()["status"] == "healthy"

            # NL-Router health
            nlr_response = await client.get(f"{nlrouter_url}/health", timeout=5.0)
            assert nlr_response.status_code == 200
            assert nlr_response.json()["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_internal_service_auth(self, mes_url, internal_service_key):
        """Test internal service key authentication"""
        async with httpx.AsyncClient() as client:
            # Without key - should fail
            response_no_key = await client.get(
                f"{mes_url}/api/v1/analytics/daily-status", timeout=5.0
            )
            assert response_no_key.status_code == 401

            # With key - should succeed
            response_with_key = await client.get(
                f"{mes_url}/api/v1/analytics/daily-status",
                headers={"X-Internal-Service-Key": internal_service_key},
                timeout=5.0,
            )
            assert response_with_key.status_code == 200

    @pytest.mark.asyncio
    async def test_nlrouter_production_status_query(self, nlrouter_url):
        """Test NL-Router processes production status query"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{nlrouter_url}/api/v1/nlm/query", json={"query": "오늘 생산 현황"}, timeout=10.0,
                headers={"X-Internal-Service-Key": "internal-service-key-change-in-production"}
            )
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert data["intent"] == "production_status"
            assert len(data.get("errors", [])) == 0, f"Errors: {data.get('errors')}"

    @pytest.mark.asyncio
    async def test_nlrouter_error_diagnosis_query(self, nlrouter_url):
        """Test NL-Router processes error diagnosis query (colloquial)"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{nlrouter_url}/api/v1/nlm/query", json={"query": "이거 망가졌어"}, timeout=10.0,
                headers={"X-Internal-Service-Key": "internal-service-key-change-in-production"}
            )
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert data["intent"] == "error_diagnosis"
            assert len(data.get("errors", [])) == 0, f"Errors: {data.get('errors')}"

    @pytest.mark.asyncio
    async def test_nlrouter_equipment_status_query(self, nlrouter_url):
        """Test NL-Router processes equipment status query"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{nlrouter_url}/api/v1/nlm/query", json={"query": "설비 상태 어때"}, timeout=10.0,
                headers={"X-Internal-Service-Key": "internal-service-key-change-in-production"}
            )
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert data["intent"] == "equipment_status"

    @pytest.mark.asyncio
    async def test_today_date_parsing(self, mes_url, internal_service_key):
        """Test Cell-MES handles 'today' string in date parameter"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{mes_url}/api/v1/analytics/daily-status",
                params={"target_date": "today"},
                headers={"X-Internal-Service-Key": internal_service_key},
                timeout=5.0,
            )
            assert response.status_code == 200

            data = response.json()
            assert "date" in data  # Should return today's date

    @pytest.mark.asyncio
    async def test_nlrouter_returns_ui_schema(self, nlrouter_url):
        """Test NL-Router returns UI schema for rendering"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{nlrouter_url}/api/v1/nlm/query", json={"query": "오늘 생산 현황"}, timeout=10.0,
                headers={"X-Internal-Service-Key": "internal-service-key-change-in-production"}
            )
            assert response.status_code == 200

            data = response.json()
            assert "ui_schema" in data
            assert data["ui_schema"] is not None
            assert "layout" in data["ui_schema"]
            assert "components" in data["ui_schema"]


class TestServiceConfiguration:
    """Test service configuration and settings"""

    @pytest.mark.asyncio
    async def test_nlrouter_skills_endpoint(self):
        """Test NL-Router exposes skills list"""
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8001/api/v1/nlm/skills", timeout=5.0)
            assert response.status_code == 200

            data = response.json()
            assert "skills" in data
            assert data["total"] > 0

    @pytest.mark.asyncio
    async def test_mes_openapi_docs(self):
        """Test Cell-MES OpenAPI docs available"""
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8080/api/docs", timeout=5.0)
            assert response.status_code == 200
