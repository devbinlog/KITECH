"""Tests for scheduling/projector.py — read-side projection."""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock


def _make_db(scalars_all=None):
    """Return a mock AsyncSession whose execute() returns *scalars_all*."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = scalars_all or []
    mock_result.scalars.return_value = mock_scalars
    db.execute = AsyncMock(return_value=mock_result)
    return db


class TestMapEquipmentStatus:
    def test_known_statuses(self):
        from src.app.services.scheduling.projector import SchedulerProjector

        p = SchedulerProjector(AsyncMock())
        assert p._map_equipment_status("AVAILABLE") == "AVAILABLE"
        assert p._map_equipment_status("RUNNING") == "RUNNING"
        assert p._map_equipment_status("RUN") == "RUNNING"
        assert p._map_equipment_status("IDLE") == "AVAILABLE"
        assert p._map_equipment_status("STOP") == "AVAILABLE"
        assert p._map_equipment_status("ERROR") == "ERROR"
        assert p._map_equipment_status("MAINTENANCE") == "MAINTENANCE"
        assert p._map_equipment_status("OFFLINE") == "OFFLINE"

    def test_unknown_status_defaults_to_offline(self):
        from src.app.services.scheduling.projector import SchedulerProjector

        p = SchedulerProjector(AsyncMock())
        assert p._map_equipment_status("UNKNOWN_XYZ") == "OFFLINE"
        assert p._map_equipment_status("") == "OFFLINE"


class TestCalculateAvailableFrom:
    def _make_eq(self, status, last_data=None, spec_data=None):
        eq = MagicMock()
        eq.current_status = status
        eq.last_data = last_data
        eq.spec_data = spec_data
        return eq

    def test_available_returns_now(self):
        from src.app.services.scheduling.projector import SchedulerProjector

        p = SchedulerProjector(AsyncMock())
        before = datetime.now(timezone.utc)
        result = p._calculate_available_from(self._make_eq("AVAILABLE"))
        after = datetime.now(timezone.utc)
        assert before <= result <= after

    def test_running_defaults_to_30min(self):
        from src.app.services.scheduling.projector import SchedulerProjector

        p = SchedulerProjector(AsyncMock())
        before = datetime.now(timezone.utc)
        result = p._calculate_available_from(self._make_eq("RUNNING"))
        assert result >= before + timedelta(minutes=29)

    def test_running_uses_estimated_end_time(self):
        from src.app.services.scheduling.projector import SchedulerProjector

        future = datetime.now(timezone.utc) + timedelta(hours=2)
        p = SchedulerProjector(AsyncMock())
        result = p._calculate_available_from(
            self._make_eq("RUNNING", last_data={"estimated_end_time": future.isoformat()})
        )
        assert abs((result - future).total_seconds()) < 2

    def test_maintenance_defaults_to_2h(self):
        from src.app.services.scheduling.projector import SchedulerProjector

        p = SchedulerProjector(AsyncMock())
        result = p._calculate_available_from(self._make_eq("MAINTENANCE"))
        assert result >= datetime.now(timezone.utc) + timedelta(hours=1, minutes=59)

    def test_error_defaults_to_1h(self):
        from src.app.services.scheduling.projector import SchedulerProjector

        p = SchedulerProjector(AsyncMock())
        result = p._calculate_available_from(self._make_eq("ERROR"))
        assert result >= datetime.now(timezone.utc) + timedelta(minutes=59)


class TestGetOccupiedSlots:
    def _make_prod_result(self, eq_id, wo_id, start, end):
        pr = MagicMock()
        pr.target_equipment_id = eq_id
        pr.work_order_id = wo_id
        pr.start_time = start
        pr.end_time = end
        return pr

    def _make_db_multi(self, first_call_results, second_call_results=None):
        """DB mock that returns different results per execute() call."""
        db = AsyncMock()
        call_count = [0]

        def _side_effect(*args, **kwargs):
            idx = call_count[0]
            call_count[0] += 1
            mock_result = MagicMock()
            mock_scalars = MagicMock()
            mock_scalars.all.return_value = (
                second_call_results if idx > 0 and second_call_results is not None
                else first_call_results
            )
            mock_result.scalars.return_value = mock_scalars
            return mock_result

        db.execute = AsyncMock(side_effect=_side_effect)
        return db

    @pytest.mark.asyncio
    async def test_returns_correct_structure(self):
        from src.app.services.scheduling.projector import SchedulerProjector

        now = datetime(2024, 6, 1, 9, 0, 0, tzinfo=timezone.utc)
        pr1 = self._make_prod_result(1, 10, now, now + timedelta(hours=1))
        pr2 = self._make_prod_result(2, 11, now, now + timedelta(hours=2))

        db = self._make_db_multi([pr1, pr2], second_call_results=[])
        p = SchedulerProjector(db)
        result = await p.get_occupied_slots([1, 2], now, now + timedelta(hours=24))

        assert 1 in result
        assert 2 in result
        assert len(result[1]) == 1
        assert len(result[2]) == 1

    @pytest.mark.asyncio
    async def test_time_conversion_to_seconds(self):
        from src.app.services.scheduling.projector import SchedulerProjector

        now = datetime(2024, 6, 1, 9, 0, 0, tzinfo=timezone.utc)
        pr = self._make_prod_result(1, 10, now, now + timedelta(hours=1))

        db = self._make_db_multi([pr], second_call_results=[])
        p = SchedulerProjector(db)
        result = await p.get_occupied_slots([1], now, now + timedelta(hours=24))

        slot = result[1][0]
        assert slot["start"] == 0
        assert slot["end"] == 3600
        assert slot["wo_id"] == "WO-10"

    @pytest.mark.asyncio
    async def test_clamps_negative_start_to_zero(self):
        from src.app.services.scheduling.projector import SchedulerProjector

        now = datetime(2024, 6, 1, 9, 0, 0, tzinfo=timezone.utc)
        # Starts 1h before horizon
        pr = self._make_prod_result(1, 5, now - timedelta(hours=1), now + timedelta(minutes=30))

        db = self._make_db_multi([pr], second_call_results=[])
        p = SchedulerProjector(db)
        result = await p.get_occupied_slots([1], now, now + timedelta(hours=24))

        slot = result[1][0]
        assert slot["start"] == 0
        assert slot["end"] == 1800

    @pytest.mark.asyncio
    async def test_empty_when_no_results(self):
        from src.app.services.scheduling.projector import SchedulerProjector

        db = self._make_db_multi([], second_call_results=[])
        p = SchedulerProjector(db)
        now = datetime(2024, 6, 1, 9, 0, 0, tzinfo=timezone.utc)
        result = await p.get_occupied_slots([1, 2], now, now + timedelta(hours=24))
        assert result == {}


class TestBuildMachineTypeParams:
    def test_groups_by_machine_type(self):
        from src.app.services.scheduling.projector import SchedulerProjector

        p = SchedulerProjector(AsyncMock())
        machines = [
            {"machine_type": "CNC"},
            {"machine_type": "CNC"},
            {"machine_type": "ROBOT"},
        ]
        result = p.build_machine_type_params_from_machines(machines)
        assert "CNC" in result["machine_types"]
        assert "ROBOT" in result["machine_types"]
        assert len(result["machine_types"]) == 2

    def test_default_params_present(self):
        from src.app.services.scheduling.projector import SchedulerProjector

        p = SchedulerProjector(AsyncMock())
        result = p.build_machine_type_params_from_machines([{"machine_type": "CNC"}])
        params = result["machine_types"]["CNC"]
        assert "loading_type" in params
        assert "amr_transport_qty" in params

    def test_empty_machines_returns_empty_dict(self):
        from src.app.services.scheduling.projector import SchedulerProjector

        p = SchedulerProjector(AsyncMock())
        result = p.build_machine_type_params_from_machines([])
        assert result == {"machine_types": {}}
