"""Tests for equipment status polling service."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.services.polling_service import poll_all_equipments, poll_equipment_status


def _make_equipment(eq_id: int = 1, eq_type: str = "CNC", aas_id: str = "urn:aas:cnc:test") -> MagicMock:
    """Create a mock Equipment object."""
    eq = MagicMock()
    eq.id = eq_id
    eq.equipment_type = eq_type
    eq.aas_id = aas_id
    eq.connection_config = {"ip": "192.168.1.1", "port": 502}
    eq.current_status = "IDLE"
    eq.last_data = {}
    eq.last_connected_at = None
    return eq


def _make_db_session() -> AsyncMock:
    """Create a mock async DB session."""
    db = AsyncMock(spec=AsyncSession)
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


def _make_aas_response(aas_id: str, is_connected: bool = True, door_state: str = "open") -> list:
    """Build a fetch_all_assets() response list."""
    return [
        {
            "id": aas_id,
            "idShort": aas_id.split(":")[-1],
            "submodels": {
                "cncGateway": {
                    "isConnected": is_connected,
                    "status": {"doorState": door_state},
                }
            },
        }
    ]


class TestPollEquipmentStatus:
    """Tests for poll_equipment_status function."""

    @pytest.mark.asyncio
    async def test_successful_poll_updates_equipment(self):
        equipment = _make_equipment(aas_id="urn:aas:cnc:test")
        db = _make_db_session()

        with patch(
            "src.app.services.polling_service.middleware_client.fetch_all_assets",
            new_callable=AsyncMock,
            return_value=_make_aas_response("urn:aas:cnc:test", is_connected=True, door_state="open"),
        ):
            result = await poll_equipment_status(db, equipment)

        assert equipment.current_status == "RUN"
        assert equipment.last_connected_at is not None
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(equipment)

    @pytest.mark.asyncio
    async def test_error_status_creates_eq_log(self):
        equipment = _make_equipment(aas_id="urn:aas:cnc:test")
        db = _make_db_session()

        with patch(
            "src.app.services.polling_service.middleware_client.fetch_all_assets",
            new_callable=AsyncMock,
            side_effect=RuntimeError("E001"),
        ):
            await poll_equipment_status(db, equipment)

        # db.add should be called for the EqLog
        db.add.assert_called_once()
        call_arg = db.add.call_args[0][0]
        assert call_arg.level == "WARN"
        assert "E001" in call_arg.message

    @pytest.mark.asyncio
    async def test_middleware_failure_sets_error_status(self):
        equipment = _make_equipment(aas_id="urn:aas:cnc:test")
        db = _make_db_session()

        with patch(
            "src.app.services.polling_service.middleware_client.fetch_all_assets",
            new_callable=AsyncMock,
            side_effect=ConnectionError("Timeout"),
        ):
            result = await poll_equipment_status(db, equipment)

        assert equipment.current_status == "ERROR"
        # EqLog should be created for the failure
        db.add.assert_called_once()
        log = db.add.call_args[0][0]
        assert log.level == "WARN"
        assert "Timeout" in log.message

    @pytest.mark.asyncio
    async def test_middleware_failure_commits_and_refreshes(self):
        equipment = _make_equipment(aas_id="urn:aas:cnc:test")
        db = _make_db_session()

        with patch(
            "src.app.services.polling_service.middleware_client.fetch_all_assets",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Connection refused"),
        ):
            await poll_equipment_status(db, equipment)

        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(equipment)

    @pytest.mark.asyncio
    async def test_last_connected_at_uses_utc(self):
        equipment = _make_equipment(aas_id="urn:aas:cnc:test")
        db = _make_db_session()

        with patch(
            "src.app.services.polling_service.middleware_client.fetch_all_assets",
            new_callable=AsyncMock,
            return_value=_make_aas_response("urn:aas:cnc:test", is_connected=True),
        ):
            await poll_equipment_status(db, equipment)

        ts = equipment.last_connected_at
        assert ts is not None
        assert ts.tzinfo is not None
        assert ts.tzinfo.utcoffset(ts).total_seconds() == 0

    @pytest.mark.asyncio
    async def test_returns_equipment_object(self):
        equipment = _make_equipment(aas_id="urn:aas:cnc:test")
        db = _make_db_session()

        with patch(
            "src.app.services.polling_service.middleware_client.fetch_all_assets",
            new_callable=AsyncMock,
            return_value=_make_aas_response("urn:aas:cnc:test", is_connected=True, door_state="open"),
        ):
            result = await poll_equipment_status(db, equipment)

        assert result is equipment


class TestPollAllEquipments:
    """Tests for poll_all_equipments function."""

    @pytest.mark.asyncio
    async def test_polls_all_non_deleted_equipments(self):
        eq1 = _make_equipment(1, aas_id="urn:aas:cnc:eq1")
        eq2 = _make_equipment(2, aas_id="urn:aas:cnc:eq2")
        db = _make_db_session()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [eq1, eq2]
        db.execute = AsyncMock(return_value=mock_result)

        aas_items = [
            {
                "id": "urn:aas:cnc:eq1",
                "idShort": "eq1",
                "submodels": {"cncGateway": {"isConnected": True, "status": {"doorState": "open"}}},
            },
            {
                "id": "urn:aas:cnc:eq2",
                "idShort": "eq2",
                "submodels": {"cncGateway": {"isConnected": True, "status": {"doorState": "open"}}},
            },
        ]

        with patch(
            "src.app.services.polling_service.middleware_client.fetch_all_assets",
            new_callable=AsyncMock,
            return_value=aas_items,
        ):
            results = await poll_all_equipments(db)

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_continues_polling_on_individual_failure(self):
        eq1 = _make_equipment(1, aas_id="urn:aas:cnc:eq1")
        eq2 = _make_equipment(2, aas_id="urn:aas:cnc:eq2")
        db = _make_db_session()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [eq1, eq2]
        db.execute = AsyncMock(return_value=mock_result)

        # eq1 has a bad submodels entry that will raise on parse; eq2 is fine
        aas_items = [
            {
                "id": "urn:aas:cnc:eq1",
                "idShort": "eq1",
                "submodels": {"cncGateway": {"isConnected": True, "status": {"doorState": "open"}}},
            },
            {
                "id": "urn:aas:cnc:eq2",
                "idShort": "eq2",
                "submodels": {"cncGateway": {"isConnected": True, "status": {"doorState": "open"}}},
            },
        ]

        with patch(
            "src.app.services.polling_service.middleware_client.fetch_all_assets",
            new_callable=AsyncMock,
            return_value=aas_items,
        ):
            results = await poll_all_equipments(db)

        # Both should be in results
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_equipments(self):
        db = _make_db_session()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=mock_result)

        with patch(
            "src.app.services.polling_service.middleware_client.fetch_all_assets",
            new_callable=AsyncMock,
            return_value=[],
        ):
            results = await poll_all_equipments(db)

        assert results == []
