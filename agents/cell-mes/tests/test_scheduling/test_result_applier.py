"""Tests for scheduling/result_applier.py — write-side persistence."""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch, call


def _make_scheduling_result(status="success", tasks=None):
    now = datetime.now(timezone.utc)
    return {
        "status": status,
        "scheduled_tasks": tasks or [],
        "gantt_data": {"start": now.isoformat()},
        "statistics": {},
        "quality_metrics": {},
    }


def _make_task(wo_id="WO-1", op_id="OP-1", machine_id="EQ-1", start=0, end=3600):
    return {
        "wo_id": wo_id,
        "op_id": op_id,
        "machine_id": machine_id,
        "start_time": start,
        "end_time": end,
        "quantity": 10,
    }


class TestAggregateLots:
    def test_single_task_unchanged(self):
        from src.app.services.scheduling.result_applier import SchedulingResultApplier

        tasks = [_make_task(start=0, end=100)]
        result = SchedulingResultApplier._aggregate_lots(tasks)
        assert len(result) == 1
        assert result[0]["start_time"] == 0
        assert result[0]["end_time"] == 100

    def test_two_lots_same_op_aggregated(self):
        from src.app.services.scheduling.result_applier import SchedulingResultApplier

        tasks = [
            _make_task(op_id="OP-1", start=0, end=100),
            _make_task(op_id="OP-1", start=50, end=200),
        ]
        result = SchedulingResultApplier._aggregate_lots(tasks)
        assert len(result) == 1
        assert result[0]["start_time"] == 0   # min
        assert result[0]["end_time"] == 200    # max

    def test_different_ops_kept_separate(self):
        from src.app.services.scheduling.result_applier import SchedulingResultApplier

        tasks = [
            _make_task(op_id="OP-1", start=0, end=100),
            _make_task(op_id="OP-2", start=100, end=200),
        ]
        result = SchedulingResultApplier._aggregate_lots(tasks)
        assert len(result) == 2


class TestApplyFailedStatus:
    @pytest.mark.asyncio
    async def test_returns_failure_for_non_success_status(self):
        from src.app.services.scheduling.result_applier import SchedulingResultApplier

        db = AsyncMock()
        applier = SchedulingResultApplier(db)
        result = await applier.apply({"status": "error", "error": "solver failed"})

        assert result["success"] is False
        assert "error" in result["message"].lower() or "failed" in result["message"].lower()


class TestApplySuccess:
    def _make_order(self, order_id=1, status="READY", lot_no="LOT-001"):
        order = MagicMock()
        order.id = order_id
        order.status = status
        order.lot_no = lot_no
        order.start_time = None
        order.end_time = None
        return order

    def _make_db(self, order=None, del_rowcount=0):
        db = AsyncMock()

        # execute returns for: delete, select-WorkOrder
        del_result = MagicMock()
        del_result.rowcount = del_rowcount

        select_result = MagicMock()
        select_scalars = MagicMock()
        select_scalars.all.return_value = [order] if order else []
        select_result.scalars.return_value = select_scalars

        # begin_nested() returns a savepoint context manager
        nested = AsyncMock()
        nested.__aenter__ = AsyncMock(return_value=nested)
        nested.__aexit__ = AsyncMock(return_value=False)
        nested.commit = AsyncMock()
        nested.rollback = AsyncMock()
        db.begin_nested = AsyncMock(return_value=nested)

        call_count = [0]

        def _execute_side_effect(*args, **kwargs):
            idx = call_count[0]
            call_count[0] += 1
            if idx == 0:
                return del_result
            return select_result

        db.execute = AsyncMock(side_effect=_execute_side_effect)
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_ready_order_set_to_scheduled(self):
        from src.app.services.scheduling.result_applier import SchedulingResultApplier

        order = self._make_order(order_id=1, status="READY")
        db = self._make_db(order=order)

        applier = SchedulingResultApplier(db)
        result = await applier.apply(
            _make_scheduling_result(tasks=[_make_task(wo_id="WO-1")])
        )

        assert result["success"] is True
        assert order.status == "SCHEDULED"

    @pytest.mark.asyncio
    async def test_running_order_keeps_status(self):
        from src.app.services.scheduling.result_applier import SchedulingResultApplier

        order = self._make_order(order_id=1, status="RUNNING")
        db = self._make_db(order=order)

        applier = SchedulingResultApplier(db)
        await applier.apply(
            _make_scheduling_result(tasks=[_make_task(wo_id="WO-1")])
        )

        assert order.status == "RUNNING"

    @pytest.mark.asyncio
    async def test_created_results_populated(self):
        from src.app.services.scheduling.result_applier import SchedulingResultApplier

        order = self._make_order(order_id=1, status="READY")
        db = self._make_db(order=order)

        applier = SchedulingResultApplier(db)
        result = await applier.apply(
            _make_scheduling_result(tasks=[_make_task(wo_id="WO-1", op_id="OP-1")])
        )

        assert result["success"] is True
        assert len(result["created_results"]) == 1
        assert result["created_results"][0]["op_id"] == "OP-1"

    @pytest.mark.asyncio
    async def test_unknown_wo_id_adds_to_errors(self):
        from src.app.services.scheduling.result_applier import SchedulingResultApplier

        db = self._make_db(order=None)  # no matching order
        applier = SchedulingResultApplier(db)
        result = await applier.apply(
            _make_scheduling_result(tasks=[_make_task(wo_id="WO-999")])
        )

        assert result["success"] is True  # partial success
        assert result["error_count"] > 0

    @pytest.mark.asyncio
    async def test_db_commit_failure_returns_failure(self):
        from src.app.services.scheduling.result_applier import SchedulingResultApplier

        order = self._make_order(order_id=1, status="READY")
        db = self._make_db(order=order)
        db.commit = AsyncMock(side_effect=Exception("DB unavailable"))

        applier = SchedulingResultApplier(db)
        result = await applier.apply(
            _make_scheduling_result(tasks=[_make_task(wo_id="WO-1")])
        )

        assert result["success"] is False
        db.rollback.assert_awaited()
