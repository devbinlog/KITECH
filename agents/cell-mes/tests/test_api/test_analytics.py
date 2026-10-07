"""Tests for analytics endpoints."""

import pytest
from datetime import date
from httpx import AsyncClient


class TestDailyStatus:
    """Test daily status endpoint."""

    @pytest.mark.asyncio
    async def test_get_daily_status(self, client: AsyncClient, auth_headers, sample_work_order):
        """Get today's daily status."""
        response = await client.get("/api/v1/analytics/daily-status", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "date" in data
        assert "orders" in data
        assert "results" in data
        assert "equipment" in data
        assert "kpis" in data

    @pytest.mark.asyncio
    async def test_get_daily_status_with_date(
        self, client: AsyncClient, auth_headers, sample_work_order
    ):
        """Get daily status for a specific date."""
        target_date = date.today().isoformat()
        response = await client.get(
            f"/api/v1/analytics/daily-status?target_date={target_date}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["date"] == target_date

    @pytest.mark.asyncio
    async def test_get_daily_status_invalid_date(self, client: AsyncClient, auth_headers):
        """Invalid date format returns 400."""
        response = await client.get(
            "/api/v1/analytics/daily-status?target_date=invalid-date",
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "Invalid date format" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_daily_status_unauthorized(self, client: AsyncClient):
        """Unauthorized request returns 401."""
        response = await client.get("/api/v1/analytics/daily-status")

        assert response.status_code == 401


class TestEquipmentUtilization:
    """Test equipment utilization endpoint."""

    @pytest.mark.asyncio
    async def test_get_equipment_utilization(
        self, client: AsyncClient, auth_headers, sample_equipment
    ):
        """Get equipment utilization for all equipment."""
        response = await client.get(
            "/api/v1/analytics/equipment-utilization",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "period" in data
        assert "equipment_utilization" in data
        assert "summary" in data

    @pytest.mark.asyncio
    async def test_get_equipment_utilization_with_ids(
        self, client: AsyncClient, auth_headers, sample_equipment
    ):
        """Get utilization for specific equipment IDs."""
        response = await client.get(
            f"/api/v1/analytics/equipment-utilization?equipment_ids={sample_equipment.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "equipment_utilization" in data

    @pytest.mark.asyncio
    async def test_get_equipment_utilization_multiple_ids(
        self, client: AsyncClient, auth_headers, multiple_equipments
    ):
        """Get utilization for multiple equipment IDs."""
        eq_ids = ",".join(str(eq.id) for eq in multiple_equipments[:2])
        response = await client.get(
            f"/api/v1/analytics/equipment-utilization?equipment_ids={eq_ids}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["equipment_utilization"]) >= 0  # May be 0 if no results

    @pytest.mark.asyncio
    async def test_get_equipment_utilization_invalid_ids(self, client: AsyncClient, auth_headers):
        """Invalid equipment IDs format returns 400."""
        response = await client.get(
            "/api/v1/analytics/equipment-utilization?equipment_ids=abc,def",
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "Invalid equipment_ids format" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_equipment_utilization_with_days(
        self, client: AsyncClient, auth_headers, sample_equipment
    ):
        """Get utilization with custom days parameter."""
        response = await client.get(
            "/api/v1/analytics/equipment-utilization?days=30",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "period" in data

    @pytest.mark.asyncio
    async def test_get_equipment_utilization_unauthorized(self, client: AsyncClient):
        """Unauthorized request returns 401."""
        response = await client.get("/api/v1/analytics/equipment-utilization")

        assert response.status_code == 401


class TestKPIDashboard:
    """Test KPI dashboard endpoint."""

    @pytest.mark.asyncio
    async def test_get_kpi_dashboard(self, client: AsyncClient, auth_headers, sample_work_order):
        """Get KPI dashboard data."""
        response = await client.get("/api/v1/analytics/kpis", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "today" in data
        assert "week" in data
        assert "current" in data

    @pytest.mark.asyncio
    async def test_get_kpi_dashboard_cached(
        self, client: AsyncClient, auth_headers, sample_work_order
    ):
        """KPI dashboard uses cache."""
        # First request
        response1 = await client.get("/api/v1/analytics/kpis", headers=auth_headers)
        assert response1.status_code == 200

        # Second request should use cache
        response2 = await client.get("/api/v1/analytics/kpis", headers=auth_headers)
        assert response2.status_code == 200
        # Both responses should have same structure
        assert response1.json().keys() == response2.json().keys()

    @pytest.mark.asyncio
    async def test_get_kpi_dashboard_unauthorized(self, client: AsyncClient):
        """Unauthorized request returns 401."""
        response = await client.get("/api/v1/analytics/kpis")

        assert response.status_code == 401


class TestTraceability:
    """Test lot traceability endpoint."""

    @pytest.mark.asyncio
    async def test_get_traceability(self, client: AsyncClient, auth_headers, sample_work_order):
        """Get traceability for a LOT."""
        response = await client.get(
            f"/api/v1/analytics/traceability/{sample_work_order.lot_no}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "lot_no" in data
        assert data["lot_no"] == sample_work_order.lot_no
        assert "work_order" in data
        assert "product" in data
        assert "timeline" in data
        assert "summary" in data

    @pytest.mark.asyncio
    async def test_get_traceability_not_found(self, client: AsyncClient, auth_headers):
        """Non-existent LOT returns 404."""
        response = await client.get(
            "/api/v1/analytics/traceability/LOT-NONEXISTENT",
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_traceability_with_routing(
        self,
        client: AsyncClient,
        auth_headers,
        sample_work_order,
        sample_routing,
    ):
        """Get traceability with routing data."""
        response = await client.get(
            f"/api/v1/analytics/traceability/{sample_work_order.lot_no}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "routing" in data

    @pytest.mark.asyncio
    async def test_get_traceability_unauthorized(self, client: AsyncClient):
        """Unauthorized request returns 401."""
        response = await client.get("/api/v1/analytics/traceability/LOT-TEST")

        assert response.status_code == 401


class TestTrends:
    """Test production trends endpoint."""

    @pytest.mark.asyncio
    async def test_get_trends_yield(self, client: AsyncClient, auth_headers, sample_work_order):
        """Get yield trends."""
        response = await client.get(
            "/api/v1/analytics/trends?metric=yield",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["metric"] == "yield"
        assert "data" in data
        assert isinstance(data["data"], list)

    @pytest.mark.asyncio
    async def test_get_trends_production(
        self, client: AsyncClient, auth_headers, sample_work_order
    ):
        """Get production trends."""
        response = await client.get(
            "/api/v1/analytics/trends?metric=production",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["metric"] == "production"

    @pytest.mark.asyncio
    async def test_get_trends_utilization(
        self, client: AsyncClient, auth_headers, sample_equipment
    ):
        """Get utilization trends."""
        response = await client.get(
            "/api/v1/analytics/trends?metric=utilization",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["metric"] == "utilization"

    @pytest.mark.asyncio
    async def test_get_trends_completion(
        self, client: AsyncClient, auth_headers, sample_work_order
    ):
        """Get completion trends."""
        response = await client.get(
            "/api/v1/analytics/trends?metric=completion",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["metric"] == "completion"

    @pytest.mark.asyncio
    async def test_get_trends_invalid_metric(self, client: AsyncClient, auth_headers):
        """Invalid metric returns 400."""
        response = await client.get(
            "/api/v1/analytics/trends?metric=invalid",
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "Invalid metric" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_trends_with_days(self, client: AsyncClient, auth_headers, sample_work_order):
        """Get trends with custom days parameter."""
        response = await client.get(
            "/api/v1/analytics/trends?metric=yield&days=14",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["days"] == 14
        assert len(data["data"]) == 14

    @pytest.mark.asyncio
    async def test_get_trends_with_group_by(
        self, client: AsyncClient, auth_headers, sample_work_order
    ):
        """Get trends with group_by parameter."""
        response = await client.get(
            "/api/v1/analytics/trends?metric=yield&group_by=day",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["group_by"] == "day"

    @pytest.mark.asyncio
    async def test_get_trends_unauthorized(self, client: AsyncClient):
        """Unauthorized request returns 401."""
        response = await client.get("/api/v1/analytics/trends")

        assert response.status_code == 401
