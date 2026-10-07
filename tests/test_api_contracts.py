"""API Contract Tests - Verify API schemas are consistent.

These tests require running services. They dynamically check
service availability and skip if services are not running.
"""

import pytest
import httpx


def _service_available(url: str) -> bool:
    """Check if a service is available."""
    try:
        response = httpx.get(f"{url}/health", timeout=3)
        return response.status_code == 200
    except Exception:
        return False


class TestCellMESContracts:
    """Test Cell-MES API contracts"""

    BASE_URL = "http://localhost:8080"

    @pytest.fixture(autouse=True)
    def check_service(self):
        if not _service_available(self.BASE_URL):
            pytest.skip("Cell-MES service not running")

    def test_openapi_docs_available(self):
        """Test OpenAPI docs endpoint is available"""
        response = httpx.get(f"{self.BASE_URL}/api/docs", timeout=5)
        assert response.status_code == 200

    def test_health_endpoint(self):
        """Test health endpoint returns expected structure"""
        response = httpx.get(f"{self.BASE_URL}/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "app" in data

    def test_analytics_requires_auth(self):
        """Test analytics endpoint requires internal service key"""
        response = httpx.get(
            f"{self.BASE_URL}/api/v1/analytics/daily-status", timeout=5
        )
        assert response.status_code == 401, "Analytics should require authentication"

    def test_analytics_with_service_key(self):
        """Test analytics endpoint works with internal service key"""
        response = httpx.get(
            f"{self.BASE_URL}/api/v1/analytics/daily-status",
            headers={"X-Internal-Service-Key": "internal-service-key-change-in-production"},
            timeout=5,
        )
        assert response.status_code == 200
        data = response.json()
        assert "date" in data


class TestNLRouterContracts:
    """Test NL-Router API contracts"""

    BASE_URL = "http://localhost:8001"

    @pytest.fixture(autouse=True)
    def check_service(self):
        if not _service_available(self.BASE_URL):
            pytest.skip("NL-Router service not running")

    def test_query_endpoint_accepts_valid_format(self):
        """Test query endpoint accepts expected request format"""
        response = httpx.post(
            f"{self.BASE_URL}/api/v1/nlm/query",
            json={"query": "설비 상태"},
            timeout=10,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "intent" in data

    def test_query_endpoint_rejects_empty_query(self):
        """Test query endpoint rejects empty query"""
        response = httpx.post(
            f"{self.BASE_URL}/api/v1/nlm/query",
            json={"query": ""},
            timeout=10,
        )
        assert response.status_code == 422, "Empty query should be rejected"

    def test_skills_endpoint(self):
        """Test skills listing endpoint"""
        response = httpx.get(
            f"{self.BASE_URL}/api/v1/nlm/skills", timeout=5
        )
        assert response.status_code == 200
        data = response.json()
        assert "skills" in data
        assert data["total"] > 0


class TestSchedulerContracts:
    """Test Cell-Scheduler API contracts"""

    BASE_URL = "http://localhost:8002"

    @pytest.fixture(autouse=True)
    def check_service(self):
        if not _service_available(self.BASE_URL):
            pytest.skip("Cell-Scheduler service not running")

    def test_health_endpoint(self):
        """Test scheduler health endpoint"""
        response = httpx.get(f"{self.BASE_URL}/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_solve_endpoint_handles_empty_request(self):
        """Test solve endpoint handles empty work orders gracefully"""
        response = httpx.post(
            f"{self.BASE_URL}/api/v1/schedule/solve",
            json={
                "work_orders": [],
                "machines": [],
                "scheduling_horizon": {
                    "start": "2026-02-15T00:00:00",
                    "end": "2026-02-16T00:00:00",
                },
                "machine_type_params": {},
                "options": {"solver_type": "OR_TOOLS", "time_limit_sec": 5},
            },
            timeout=10,
        )
        # After fix: returns 400 with validation error
        # Before fix: returns 200 with empty schedule
        assert response.status_code in [200, 400], (
            f"Unexpected status {response.status_code}: {response.text[:200]}"
        )
        if response.status_code == 200:
            data = response.json()
            assert data["statistics"]["total_tasks"] == 0

    def test_available_solvers(self):
        """Test solvers listing endpoint"""
        response = httpx.get(f"{self.BASE_URL}/api/v1/schedule/solvers", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "solvers" in data
        assert len(data["solvers"]) >= 5  # OR-Tools, GA, SA, Tabu, ALNS
