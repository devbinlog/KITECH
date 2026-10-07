"""Tests for ProdResult model and production results."""

import pytest
from datetime import datetime, timedelta, timezone

from src.app.models.production import WorkOrder, ProdResult


class TestProdResultModel:
    """Test ProdResult model properties."""

    def test_total_qty_calculation(self):
        """Total quantity is sum of OK and NG."""
        result = ProdResult(
            work_order_id=1,
            ok_qty=90,
            ng_qty=10,
        )

        assert result.total_qty == 100

    def test_total_qty_zero(self):
        """Total quantity is zero when both are zero."""
        result = ProdResult(
            work_order_id=1,
            ok_qty=0,
            ng_qty=0,
        )

        assert result.total_qty == 0

    def test_yield_rate_calculation(self):
        """Yield rate is calculated correctly."""
        result = ProdResult(
            work_order_id=1,
            ok_qty=90,
            ng_qty=10,
        )

        # 90/100 * 100 = 90%
        assert result.yield_rate == 90.0

    def test_yield_rate_perfect(self):
        """Yield rate is 100% when no NG."""
        result = ProdResult(
            work_order_id=1,
            ok_qty=100,
            ng_qty=0,
        )

        assert result.yield_rate == 100.0

    def test_yield_rate_zero(self):
        """Yield rate is 0% when all NG."""
        result = ProdResult(
            work_order_id=1,
            ok_qty=0,
            ng_qty=100,
        )

        assert result.yield_rate == 0.0

    def test_yield_rate_no_production(self):
        """Yield rate is 0% when no production."""
        result = ProdResult(
            work_order_id=1,
            ok_qty=0,
            ng_qty=0,
        )

        assert result.yield_rate == 0.0

    def test_yield_rate_precision(self):
        """Yield rate handles fractional percentages."""
        result = ProdResult(
            work_order_id=1,
            ok_qty=1,
            ng_qty=2,
        )

        # 1/3 * 100 = 33.333...
        assert abs(result.yield_rate - 33.333333) < 0.001

    def test_repr(self):
        """String representation is correct."""
        result = ProdResult(
            id=1,
            work_order_id=123,
            ok_qty=90,
            ng_qty=10,
        )

        repr_str = repr(result)
        assert "ProdResult" in repr_str
        assert "wo_id=123" in repr_str
        assert "ok=90" in repr_str
        assert "ng=10" in repr_str


class TestProdResultTimestamps:
    """Test ProdResult timestamp handling."""

    def test_start_end_times(self):
        """Start and end times are stored correctly."""
        start = datetime.now(timezone.utc)
        end = start + timedelta(hours=1)

        result = ProdResult(
            work_order_id=1,
            ok_qty=50,
            ng_qty=5,
            start_time=start,
            end_time=end,
        )

        assert result.start_time == start
        assert result.end_time == end

    def test_nullable_timestamps(self):
        """Timestamps can be None."""
        result = ProdResult(
            work_order_id=1,
            ok_qty=50,
            ng_qty=5,
        )

        assert result.start_time is None
        assert result.end_time is None


class TestProdResultWithWorkOrder:
    """Test ProdResult with WorkOrder relationship."""

    @pytest.mark.asyncio
    async def test_create_result_for_order(self, db_session, sample_product):
        """Create production result for a work order."""
        # Create work order
        order = WorkOrder(
            lot_no="LOT-RESULT-001",
            product_id=sample_product.id,
            target_qty=100,
            status="RUNNING",
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        # Create result
        result = ProdResult(
            work_order_id=order.id,
            ok_qty=50,
            ng_qty=5,
            start_time=datetime.now(timezone.utc),
        )
        db_session.add(result)
        await db_session.commit()
        await db_session.refresh(result)

        assert result.work_order_id == order.id
        assert result.ok_qty == 50

    @pytest.mark.asyncio
    async def test_multiple_results_for_order(self, db_session, sample_product):
        """Multiple results can be created for one work order."""
        from sqlalchemy import select, func

        order = WorkOrder(
            lot_no="LOT-MULTI-RESULT",
            product_id=sample_product.id,
            target_qty=100,
            qty=100,
            status="RUNNING",
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        # Create multiple results (different operations)
        for i in range(3):
            result = ProdResult(
                work_order_id=order.id,
                process_routing_id=i + 1,  # Different operations
                ok_qty=30 + i,
                ng_qty=1,
            )
            db_session.add(result)
        await db_session.commit()

        # Query results count directly (async-safe)
        count_result = await db_session.execute(
            select(func.count()).where(ProdResult.work_order_id == order.id)
        )
        results_count = count_result.scalar()

        # Check results
        assert results_count == 3

    @pytest.mark.asyncio
    async def test_cascade_delete_results(self, db_session, sample_product):
        """Results are deleted when work order is deleted."""
        from sqlalchemy import select

        order = WorkOrder(
            lot_no="LOT-CASCADE",
            product_id=sample_product.id,
            target_qty=100,
            status="RUNNING",
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        # Add result
        result = ProdResult(
            work_order_id=order.id,
            ok_qty=50,
            ng_qty=5,
        )
        db_session.add(result)
        await db_session.commit()
        result_id = result.id

        # Delete work order
        await db_session.delete(order)
        await db_session.commit()

        # Check result is deleted
        query = select(ProdResult).where(ProdResult.id == result_id)
        db_result = await db_session.execute(query)
        assert db_result.scalar_one_or_none() is None


class TestProdResultAggregation:
    """Test production result aggregation."""

    @pytest.mark.asyncio
    async def test_calculate_total_production(self, db_session, sample_product):
        """Calculate total production from multiple results."""
        from sqlalchemy import select, func

        order = WorkOrder(
            lot_no="LOT-AGG-001",
            product_id=sample_product.id,
            target_qty=100,
            qty=100,
            status="RUNNING",
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        # Create multiple results
        results_data = [
            (30, 2),  # 30 OK, 2 NG
            (40, 1),  # 40 OK, 1 NG
            (25, 2),  # 25 OK, 2 NG
        ]

        for ok_qty, ng_qty in results_data:
            result = ProdResult(
                work_order_id=order.id,
                ok_qty=ok_qty,
                ng_qty=ng_qty,
            )
            db_session.add(result)
        await db_session.commit()

        # Calculate totals via query (async-safe)
        result = await db_session.execute(
            select(func.sum(ProdResult.ok_qty), func.sum(ProdResult.ng_qty)).where(
                ProdResult.work_order_id == order.id
            )
        )
        total_ok, total_ng = result.one()
        total_qty = (total_ok or 0) + (total_ng or 0)

        assert total_ok == 95  # 30 + 40 + 25
        assert total_ng == 5  # 2 + 1 + 2
        assert total_qty == 100

    @pytest.mark.asyncio
    async def test_calculate_overall_yield(self, db_session, sample_product):
        """Calculate overall yield rate from multiple results."""
        from sqlalchemy import select, func

        order = WorkOrder(
            lot_no="LOT-YIELD-001",
            product_id=sample_product.id,
            target_qty=100,
            qty=100,
            status="RUNNING",
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        # Create results
        results_data = [(80, 10), (100, 0), (70, 20)]

        for ok_qty, ng_qty in results_data:
            result = ProdResult(
                work_order_id=order.id,
                ok_qty=ok_qty,
                ng_qty=ng_qty,
            )
            db_session.add(result)
        await db_session.commit()

        # Calculate via query (async-safe)
        result = await db_session.execute(
            select(func.sum(ProdResult.ok_qty), func.sum(ProdResult.ng_qty)).where(
                ProdResult.work_order_id == order.id
            )
        )
        total_ok, total_ng = result.one()
        total_qty = (total_ok or 0) + (total_ng or 0)
        overall_yield = (total_ok / total_qty * 100) if total_qty > 0 else 0

        # 250 OK / 280 total * 100 = 89.28%
        assert abs(overall_yield - 89.285714) < 0.001


class TestProdResultWithEquipment:
    """Test ProdResult with equipment tracking."""

    @pytest.mark.asyncio
    async def test_result_with_equipment(self, db_session, sample_product, sample_equipment):
        """Production result can track which equipment was used."""
        order = WorkOrder(
            lot_no="LOT-EQ-001",
            product_id=sample_product.id,
            target_qty=100,
            status="RUNNING",
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        result = ProdResult(
            work_order_id=order.id,
            equipment_id=sample_equipment.id,
            ok_qty=50,
            ng_qty=2,
        )
        db_session.add(result)
        await db_session.commit()

        assert result.equipment_id == sample_equipment.id

    @pytest.mark.asyncio
    async def test_result_nullable_equipment(self, db_session, sample_product):
        """Equipment can be None for manual operations."""
        order = WorkOrder(
            lot_no="LOT-MANUAL-001",
            product_id=sample_product.id,
            target_qty=100,
            status="RUNNING",
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        result = ProdResult(
            work_order_id=order.id,
            equipment_id=None,  # Manual operation
            ok_qty=50,
            ng_qty=0,
        )
        db_session.add(result)
        await db_session.commit()

        assert result.equipment_id is None
