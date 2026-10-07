"""Regression tests: SchedulerIntegrationService facade.

Verifies that the public API of SchedulerIntegrationService is preserved
and delegates correctly to the sub-modules.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch


class TestFacadeInit:
    def test_instantiates_without_error(self):
        from src.app.services.scheduler_integration import SchedulerIntegrationService

        service = SchedulerIntegrationService(AsyncMock())
        assert hasattr(service, "_projector")
        assert hasattr(service, "_http")
        assert hasattr(service, "_applier")

    def test_no_solving_class_attribute(self):
        """The old class-level _solving flag must be gone."""
        from src.app.services.scheduler_integration import SchedulerIntegrationService

        assert not hasattr(SchedulerIntegrationService, "_solving"), (
            "_solving class attribute still present — not fully removed"
        )

    def test_no_solve_lock_class_attribute(self):
        """The old class-level _solve_lock must be gone."""
        from src.app.services.scheduler_integration import SchedulerIntegrationService

        assert not hasattr(SchedulerIntegrationService, "_solve_lock"), (
            "_solve_lock class attribute still present"
        )


class TestFacadeDelegation:
    """Verify public methods exist and delegate (smoke-test signatures)."""

    @pytest.fixture
    def service(self):
        from src.app.services.scheduler_integration import SchedulerIntegrationService

        return SchedulerIntegrationService(AsyncMock())

    def test_map_equipment_status_delegates(self, service):
        assert service._map_equipment_status("AVAILABLE") == "AVAILABLE"
        assert service._map_equipment_status("IDLE") == "AVAILABLE"
        assert service._map_equipment_status("UNKNOWN") == "OFFLINE"

    @pytest.mark.asyncio
    async def test_get_equipment_for_scheduler_delegates(self, service):
        service._projector.get_equipment_for_scheduler = AsyncMock(return_value=[])
        result = await service.get_equipment_for_scheduler()
        service._projector.get_equipment_for_scheduler.assert_awaited_once()
        assert result == []

    @pytest.mark.asyncio
    async def test_get_occupied_slots_delegates(self, service):
        service._projector.get_occupied_slots = AsyncMock(return_value={})
        now = datetime.now(timezone.utc)
        result = await service._get_occupied_slots([1], now, now)
        service._projector.get_occupied_slots.assert_awaited_once()
        assert result == {}

    @pytest.mark.asyncio
    async def test_get_work_orders_for_scheduler_delegates(self, service):
        service._projector.get_work_orders_for_scheduler = AsyncMock(return_value=[])
        result = await service.get_work_orders_for_scheduler()
        assert result == []

    @pytest.mark.asyncio
    async def test_call_scheduler_service_delegates(self, service):
        service._http.call_scheduler_service = AsyncMock(
            return_value={"status": "success", "scheduled_tasks": []}
        )
        result = await service.call_scheduler_service({})
        service._http.call_scheduler_service.assert_awaited_once()
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_get_current_schedule_delegates(self, service):
        service._projector.get_current_schedule = AsyncMock(
            return_value={"date": "2024-06-01", "availability": [], "summary": {}}
        )
        result = await service.get_current_schedule()
        service._projector.get_current_schedule.assert_awaited_once()
        assert "date" in result


class TestProcessSchedulingResultWithLock:
    """process_scheduling_result must use the Redis lock, not _solving flag."""

    @pytest.mark.asyncio
    async def test_succeeds_when_lock_acquired(self):
        from src.app.services.scheduler_integration import SchedulerIntegrationService
        import src.app.services.scheduling.lock as lock_mod
        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def _fake_lock_acquired(timeout_sec=300):
            yield True  # lock acquired

        service = SchedulerIntegrationService(AsyncMock())
        service._applier.apply = AsyncMock(
            return_value={"success": True, "updated_orders": [], "created_results": []}
        )

        with patch.object(lock_mod, "with_solver_lock", _fake_lock_acquired):
            import src.app.services.scheduler_integration as facade_mod
            with patch.object(facade_mod, "with_solver_lock", _fake_lock_acquired):
                result = await service.process_scheduling_result(
                    {"status": "success", "scheduled_tasks": []}
                )

        assert result["success"] is True
        service._applier.apply.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_409_dict_when_lock_not_acquired(self):
        from src.app.services.scheduler_integration import SchedulerIntegrationService
        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def _fake_lock_not_acquired(timeout_sec=300):
            yield False  # lock NOT acquired

        service = SchedulerIntegrationService(AsyncMock())
        service._applier.apply = AsyncMock()

        import src.app.services.scheduler_integration as facade_mod
        with patch.object(facade_mod, "with_solver_lock", _fake_lock_not_acquired):
            result = await service.process_scheduling_result(
                {"status": "success", "scheduled_tasks": []}
            )

        assert result["success"] is False
        assert result.get("error") == "concurrent_solve"
        service._applier.apply.assert_not_awaited()


class TestModuleLevelHelper:
    @pytest.mark.asyncio
    async def test_get_equipment_availability_helper(self):
        from src.app.services.scheduler_integration import get_equipment_availability

        db = AsyncMock()
        with patch(
            "src.app.services.scheduler_integration.SchedulerIntegrationService"
        ) as MockSvc:
            instance = MockSvc.return_value
            instance.get_equipment_for_scheduler = AsyncMock(return_value=[{"machine_id": "EQ-1"}])
            result = await get_equipment_availability(db)

        assert result == [{"machine_id": "EQ-1"}]
