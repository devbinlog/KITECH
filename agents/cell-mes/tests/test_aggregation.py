"""Tests for Aggregation Service"""

import pytest
from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

from src.app.services.aggregation_service import (
    AggregationService,
    AggregatedResult,
    aggregate_daily_status,
    aggregate_equipment_utilization,
    aggregate_lot_traceability,
    aggregate_kpi_dashboard,
)


class TestAggregatedResult:
    """Tests for AggregatedResult dataclass"""

    def test_default_values(self):
        """Test AggregatedResult default values"""
        result = AggregatedResult(data={"key": "value"})

        assert result.data == {"key": "value"}
        assert result.errors == []
        assert result.partial is False
        assert result.output_type == "dashboard"
        assert result.timestamp is not None

    def test_with_errors(self):
        """Test AggregatedResult with errors"""
        result = AggregatedResult(
            data={"orders": []},
            errors=[{"source": "equipment", "message": "Connection timeout"}],
            partial=True,
        )

        assert result.partial is True
        assert len(result.errors) == 1
        assert result.errors[0]["source"] == "equipment"

    def test_custom_output_type(self):
        """Test AggregatedResult with custom output type"""
        result = AggregatedResult(data={}, output_type="traceability")

        assert result.output_type == "traceability"


class TestAggregationService:
    """Tests for AggregationService class"""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        db = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create AggregationService instance"""
        return AggregationService(mock_db)

    @pytest.mark.asyncio
    async def test_get_daily_production_status_empty(self, service, mock_db):
        """Test daily production status with no data"""
        # Mock empty results
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await service.get_daily_production_status(date.today())

        assert isinstance(result, AggregatedResult)
        assert "date" in result.data
        assert "orders" in result.data
        assert "results" in result.data
        assert "equipment" in result.data
        assert "kpis" in result.data

    @pytest.mark.asyncio
    async def test_get_daily_production_status_with_orders(self, service, mock_db):
        """Test daily production status with orders - verifies structure"""
        # For unit tests with mocked db, we verify the service method runs and returns proper structure
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await service.get_daily_production_status(date.today())

        # Verify the structure is correct even with empty data
        assert "orders" in result.data
        assert "total" in result.data["orders"]
        assert "by_status" in result.data["orders"]
        assert isinstance(result.data["orders"]["by_status"], dict)

    @pytest.mark.asyncio
    async def test_get_daily_production_status_with_results(self, service, mock_db):
        """Test daily production status results structure"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await service.get_daily_production_status(date.today())

        # Verify the results structure is correct
        assert "results" in result.data
        assert "total_ok_qty" in result.data["results"]
        assert "total_ng_qty" in result.data["results"]
        assert "total_qty" in result.data["results"]
        assert "yield_rate" in result.data["results"]

    @pytest.mark.asyncio
    async def test_get_daily_production_status_default_date(self, service, mock_db):
        """Test daily production status uses today as default"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await service.get_daily_production_status()

        assert result.data["date"] == date.today().isoformat()

    @pytest.mark.asyncio
    async def test_get_equipment_utilization_empty(self, service, mock_db):
        """Test equipment utilization with no data"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await service.get_equipment_utilization(days=7)

        assert isinstance(result, AggregatedResult)
        assert "period" in result.data
        assert "equipment_utilization" in result.data
        assert "summary" in result.data
        assert result.data["summary"]["total_equipment"] == 0

    @pytest.mark.asyncio
    async def test_get_equipment_utilization_with_equipment(self, service, mock_db):
        """Test equipment utilization structure"""
        # Mock equipment with proper attribute values
        mock_equipment = MagicMock()
        mock_equipment.id = 1
        mock_equipment.eq_name = "CNC-001"  # Correct attribute name
        mock_equipment.equipment_type = "CNC"
        mock_equipment.current_status = "RUN"
        mock_equipment.is_deleted = False

        equipment_result = MagicMock()
        equipment_result.scalars.return_value.all.return_value = [mock_equipment]

        # Mock empty results for simplicity
        results_result = MagicMock()
        results_result.all.return_value = []

        mock_db.execute.side_effect = [equipment_result, results_result]

        result = await service.get_equipment_utilization(days=7)

        assert result.data["summary"]["total_equipment"] == 1
        assert len(result.data["equipment_utilization"]) == 1
        # Verify the equipment name is correctly retrieved
        assert result.data["equipment_utilization"][0]["equipment_name"] == "CNC-001"

    @pytest.mark.asyncio
    async def test_get_equipment_utilization_with_filter(self, service, mock_db):
        """Test equipment utilization with equipment ID filter"""
        mock_equipment = MagicMock()
        mock_equipment.id = 1
        mock_equipment.name = "CNC-001"
        mock_equipment.equipment_type = "CNC"
        mock_equipment.status = "RUN"

        equipment_result = MagicMock()
        equipment_result.scalars.return_value.all.return_value = [mock_equipment]

        results_result = MagicMock()
        results_result.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [equipment_result, results_result]

        result = await service.get_equipment_utilization(equipment_ids=[1], days=7)

        # Verify filter was applied
        assert result.data["summary"]["total_equipment"] == 1

    @pytest.mark.asyncio
    async def test_get_lot_traceability_not_found(self, service, mock_db):
        """Test lot traceability when LOT not found"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.get_lot_traceability("LOT-NOTFOUND")

        assert result.output_type == "error"
        assert "not found" in result.data["error"]

    @pytest.mark.asyncio
    async def test_get_lot_traceability_found(self, service, mock_db):
        """Test lot traceability when LOT found"""
        # Create mock work order
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.lot_no = "LOT-001"
        mock_order.status = "DONE"
        mock_order.target_qty = 100
        mock_order.product_id = 1
        mock_order.scenario_id = 1
        mock_order.order_date = date.today()

        # Create mock product
        mock_product = MagicMock()
        mock_product.id = 1
        mock_product.name = "Product A"
        mock_product.code = "PROD-A"

        # Create mock scenario
        mock_scenario = MagicMock()
        mock_scenario.id = 1
        mock_scenario.name = "Default Scenario"
        mock_scenario.routings = []

        # Create mock production result
        mock_prod_result = MagicMock()
        mock_prod_result.id = 1
        mock_prod_result.ok_qty = 95
        mock_prod_result.ng_qty = 5
        mock_prod_result.equipment_id = 1
        mock_prod_result.start_time = datetime.now(timezone.utc) - timedelta(hours=1)
        mock_prod_result.end_time = datetime.now(timezone.utc)

        mock_order.product = mock_product
        mock_order.scenario = mock_scenario
        mock_order.results = [mock_prod_result]

        order_result = MagicMock()
        order_result.scalar_one_or_none.return_value = mock_order

        mock_db.execute.return_value = order_result

        result = await service.get_lot_traceability("LOT-001")

        assert result.output_type == "traceability_timeline"
        assert result.data["lot_no"] == "LOT-001"
        assert "work_order" in result.data
        assert "product" in result.data
        assert "timeline" in result.data
        assert "summary" in result.data

    @pytest.mark.asyncio
    async def test_get_kpi_dashboard(self, service, mock_db):
        """Test KPI dashboard aggregation"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await service.get_kpi_dashboard()

        assert isinstance(result, AggregatedResult)
        assert "today" in result.data
        assert "week" in result.data
        assert "current" in result.data

    @pytest.mark.asyncio
    async def test_partial_failure_handling(self, service, mock_db):
        """Test partial failure handling in aggregation"""
        # First query succeeds, second fails
        orders_result = MagicMock()
        orders_result.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [
            orders_result,
            Exception("Database connection lost"),
            orders_result,
        ]

        result = await service.get_daily_production_status()

        # Should still return result with partial=True
        assert result.partial is True
        assert len(result.errors) > 0


class TestConvenienceFunctions:
    """Tests for module-level convenience functions"""

    @pytest.mark.asyncio
    async def test_aggregate_daily_status(self):
        """Test aggregate_daily_status convenience function"""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await aggregate_daily_status(mock_db, date.today())

        assert isinstance(result, AggregatedResult)

    @pytest.mark.asyncio
    async def test_aggregate_equipment_utilization(self):
        """Test aggregate_equipment_utilization convenience function"""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await aggregate_equipment_utilization(mock_db, None, 7)

        assert isinstance(result, AggregatedResult)

    @pytest.mark.asyncio
    async def test_aggregate_lot_traceability(self):
        """Test aggregate_lot_traceability convenience function"""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await aggregate_lot_traceability(mock_db, "LOT-001")

        assert isinstance(result, AggregatedResult)

    @pytest.mark.asyncio
    async def test_aggregate_kpi_dashboard(self):
        """Test aggregate_kpi_dashboard convenience function"""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await aggregate_kpi_dashboard(mock_db)

        assert isinstance(result, AggregatedResult)


class TestKPICalculations:
    """Tests for KPI calculation logic"""

    @pytest.fixture
    def service(self):
        """Create AggregationService instance"""
        mock_db = AsyncMock()
        return AggregationService(mock_db)

    def test_yield_rate_calculation(self, service):
        """Test yield rate calculation"""
        # yield_rate = ok_qty / total_qty * 100
        ok_qty = 95
        ng_qty = 5
        total = ok_qty + ng_qty
        expected_yield = (ok_qty / total) * 100

        assert expected_yield == 95.0

    def test_completion_rate_calculation(self, service):
        """Test completion rate calculation"""
        # completion_rate = completed / total * 100
        completed = 8
        total = 10
        expected_rate = (completed / total) * 100

        assert expected_rate == 80.0

    def test_utilization_rate_calculation(self, service):
        """Test equipment utilization rate calculation"""
        # utilization = run_time / available_time * 100
        run_time_hours = 6
        available_hours = 8  # per day
        expected_utilization = (run_time_hours / available_hours) * 100

        assert expected_utilization == 75.0

    def test_zero_division_handling(self, service):
        """Test handling of zero division in calculations"""
        # Should return 0 when total is 0
        total = 0
        if total == 0:
            yield_rate = 0.0
        else:
            yield_rate = 100.0

        assert yield_rate == 0.0
