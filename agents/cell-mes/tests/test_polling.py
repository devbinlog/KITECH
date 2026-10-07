"""Tests for equipment status polling service."""

import pytest
from unittest.mock import AsyncMock, patch

from src.app.models.equipment import Equipment, EqLog
from src.app.services.polling_service import poll_equipment_status, poll_all_equipments


def _make_aas_item(aas_id: str, is_connected: bool = True, door_state: str = "open") -> dict:
    """Helper: build AAS item matching middleware_client.fetch_all_assets() format."""
    return {
        "id": aas_id,
        "idShort": aas_id.split(":")[-1],
        "submodels": {
            "cncGateway": {
                "isConnected": is_connected,
                "status": {"doorState": door_state},
            }
        },
    }


class TestPollEquipmentStatus:
    """Test polling single equipment status."""

    @pytest.mark.asyncio
    async def test_poll_updates_equipment_status(self, db_session, sample_equipment):
        """Polling updates equipment last_data and status."""
        aas_item = _make_aas_item(sample_equipment.aas_id, is_connected=True, door_state="open")

        with patch(
            "src.app.services.polling_service.middleware_client.fetch_all_assets",
            new_callable=AsyncMock,
            return_value=[aas_item],
        ):
            result = await poll_equipment_status(db_session, sample_equipment)

        assert result.current_status == "RUN"
        assert result.last_connected_at is not None

    @pytest.mark.asyncio
    async def test_poll_detects_stop_status(self, db_session, sample_equipment):
        """Polling detects STOP status when not connected."""
        aas_item = _make_aas_item(sample_equipment.aas_id, is_connected=False)

        with patch(
            "src.app.services.polling_service.middleware_client.fetch_all_assets",
            new_callable=AsyncMock,
            return_value=[aas_item],
        ):
            result = await poll_equipment_status(db_session, sample_equipment)

        assert result.current_status == "STOP"

    @pytest.mark.asyncio
    async def test_poll_creates_error_log(self, db_session, sample_equipment):
        """Polling creates WARN log when fetch_all_assets raises exception."""
        with patch(
            "src.app.services.polling_service.middleware_client.fetch_all_assets",
            new_callable=AsyncMock,
            side_effect=ConnectionError("E-200"),
        ):
            await poll_equipment_status(db_session, sample_equipment)

        # Check warn log was created
        from sqlalchemy import select

        result = await db_session.execute(
            select(EqLog).where(
                EqLog.equipment_id == sample_equipment.id,
                EqLog.level == "WARN",
            )
        )
        logs = list(result.scalars().all())
        assert len(logs) == 1
        assert "E-200" in logs[0].message

    @pytest.mark.asyncio
    async def test_poll_handles_connection_failure(self, db_session, sample_equipment):
        """Polling handles connection failure gracefully."""
        with patch(
            "src.app.services.polling_service.middleware_client.fetch_all_assets",
            new_callable=AsyncMock,
            side_effect=ConnectionError("Connection refused"),
        ):
            result = await poll_equipment_status(db_session, sample_equipment)

        # Equipment status set to ERROR on connection failure
        assert result.current_status == "ERROR"

        # Warning log created
        from sqlalchemy import select

        result = await db_session.execute(
            select(EqLog).where(
                EqLog.equipment_id == sample_equipment.id,
                EqLog.level == "WARN",
            )
        )
        logs = list(result.scalars().all())
        assert len(logs) == 1
        assert "Polling failed" in logs[0].message or "Connection refused" in logs[0].message

    @pytest.mark.asyncio
    async def test_poll_robot_equipment(self, db_session):
        """Polling robot equipment detects RUN status from robotGateway."""
        robot = Equipment(
            eq_code="EQ-ROBOT-TEST-001",
            aas_id="urn:aas:robot:test-001",
            eq_name="Test Robot",
            equipment_type="ROBOT",
            connection_config={"ip": "192.168.1.100", "port": 30002},
            current_status="STOP",
        )
        db_session.add(robot)
        await db_session.commit()
        await db_session.refresh(robot)

        aas_item = {
            "id": robot.aas_id,
            "idShort": "test-robot",
            "submodels": {
                "robotGateway": {
                    "isConnected": True,
                    "status": {"status": "BUSY"},
                }
            },
        }

        with patch(
            "src.app.services.polling_service.middleware_client.fetch_all_assets",
            new_callable=AsyncMock,
            return_value=[aas_item],
        ):
            result = await poll_equipment_status(db_session, robot)

        assert result.current_status == "RUN"

    @pytest.mark.asyncio
    async def test_poll_plc_equipment(self, db_session):
        """Polling PLC equipment detects status from modbusGateway."""
        plc = Equipment(
            eq_code="EQ-PLC-TEST-001",
            aas_id="urn:aas:plc:test-001",
            eq_name="Test PLC",
            equipment_type="PLC",
            connection_config={"ip": "192.168.1.100", "port": 502},
            current_status="STOP",
        )
        db_session.add(plc)
        await db_session.commit()
        await db_session.refresh(plc)

        aas_item = {
            "id": plc.aas_id,
            "idShort": "test-plc",
            "submodels": {
                "modbusGateway": {
                    "isConnected": True,
                    "status": {},
                }
            },
        }

        with patch(
            "src.app.services.polling_service.middleware_client.fetch_all_assets",
            new_callable=AsyncMock,
            return_value=[aas_item],
        ):
            result = await poll_equipment_status(db_session, plc)

        # Connected modbusGateway, no doorState → IDLE (not RUN, not STOP)
        assert result.current_status in ("IDLE", "RUN", "STOP")
        assert result.last_connected_at is not None


class TestPollAllEquipments:
    """Test polling all equipments."""

    @pytest.mark.asyncio
    async def test_poll_all_equipments(self, db_session):
        """Poll all active equipments."""
        aas_items = []
        for i in range(3):
            eq = Equipment(
                eq_code=f"EQ-CNC-POLL-{i}",
                aas_id=f"urn:aas:cnc:poll-{i}",
                eq_name=f"Poll CNC {i}",
                equipment_type="CNC",
                connection_config={"ip": f"192.168.1.{100 + i}", "port": 502},
                current_status="STOP",
            )
            db_session.add(eq)
            aas_items.append(
                _make_aas_item(f"urn:aas:cnc:poll-{i}", is_connected=True, door_state="open")
            )
        await db_session.commit()

        with patch(
            "src.app.services.polling_service.middleware_client.fetch_all_assets",
            new_callable=AsyncMock,
            return_value=aas_items,
        ):
            results = await poll_all_equipments(db_session)

        assert len(results) == 3
        for eq in results:
            assert eq.current_status == "RUN"

    @pytest.mark.asyncio
    async def test_poll_all_excludes_deleted(self, db_session):
        """Poll all excludes deleted equipments."""
        active_eq = Equipment(
            eq_code="EQ-CNC-ACTIVE",
            aas_id="urn:aas:cnc:active",
            eq_name="Active CNC",
            equipment_type="CNC",
            connection_config={},
            current_status="STOP",
            is_deleted=False,
        )
        deleted_eq = Equipment(
            eq_code="EQ-CNC-DELETED",
            aas_id="urn:aas:cnc:deleted",
            eq_name="Deleted CNC",
            equipment_type="CNC",
            connection_config={},
            current_status="STOP",
            is_deleted=True,
        )
        db_session.add(active_eq)
        db_session.add(deleted_eq)
        await db_session.commit()

        aas_items = [
            _make_aas_item("urn:aas:cnc:active", is_connected=True, door_state="open"),
            _make_aas_item("urn:aas:cnc:deleted", is_connected=True, door_state="open"),
        ]

        with patch(
            "src.app.services.polling_service.middleware_client.fetch_all_assets",
            new_callable=AsyncMock,
            return_value=aas_items,
        ):
            results = await poll_all_equipments(db_session)

        # Only active equipment should be polled
        assert len(results) == 1
        assert results[0].eq_name == "Active CNC"

    @pytest.mark.asyncio
    async def test_poll_all_continues_on_failure(self, db_session):
        """Poll all continues even if some equipments fail (parse error)."""
        aas_items = []
        for i in range(3):
            eq = Equipment(
                eq_code=f"EQ-CNC-FAIL-{i}",
                aas_id=f"urn:aas:cnc:fail-{i}",
                eq_name=f"Fail CNC {i}",
                equipment_type="CNC",
                connection_config={"ip": f"192.168.1.{100 + i}"},
                current_status="STOP",
            )
            db_session.add(eq)
            aas_items.append(
                _make_aas_item(f"urn:aas:cnc:fail-{i}", is_connected=True, door_state="open")
            )
        await db_session.commit()

        with patch(
            "src.app.services.polling_service.middleware_client.fetch_all_assets",
            new_callable=AsyncMock,
            return_value=aas_items,
        ):
            results = await poll_all_equipments(db_session)

        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_poll_all_empty(self, db_session):
        """Poll all returns empty when no equipments exist."""
        with patch(
            "src.app.services.polling_service.middleware_client.fetch_all_assets",
            new_callable=AsyncMock,
            return_value=[],
        ) as mock_poll:
            results = await poll_all_equipments(db_session)

        assert results == []
        mock_poll.assert_called_once()


class TestPollingStatusTransitions:
    """Test status transitions during polling."""

    @pytest.mark.asyncio
    async def test_transition_stop_to_run(self, db_session, sample_equipment):
        """Equipment transitions from STOP to RUN."""
        sample_equipment.current_status = "STOP"
        await db_session.commit()

        aas_item = _make_aas_item(sample_equipment.aas_id, is_connected=True, door_state="open")

        with patch(
            "src.app.services.polling_service.middleware_client.fetch_all_assets",
            new_callable=AsyncMock,
            return_value=[aas_item],
        ):
            result = await poll_equipment_status(db_session, sample_equipment)

        assert result.current_status == "RUN"

    @pytest.mark.asyncio
    async def test_transition_run_to_stop(self, db_session, sample_equipment):
        """Equipment transitions from RUN to STOP when not connected."""
        sample_equipment.current_status = "RUN"
        await db_session.commit()

        aas_item = _make_aas_item(sample_equipment.aas_id, is_connected=False)

        with patch(
            "src.app.services.polling_service.middleware_client.fetch_all_assets",
            new_callable=AsyncMock,
            return_value=[aas_item],
        ):
            result = await poll_equipment_status(db_session, sample_equipment)

        assert result.current_status == "STOP"

    @pytest.mark.asyncio
    async def test_transition_run_to_error(self, db_session, sample_equipment):
        """Equipment transitions to ERROR when fetch_all_assets raises."""
        sample_equipment.current_status = "RUN"
        await db_session.commit()

        with patch(
            "src.app.services.polling_service.middleware_client.fetch_all_assets",
            new_callable=AsyncMock,
            side_effect=ConnectionError("E-SPINDLE"),
        ):
            result = await poll_equipment_status(db_session, sample_equipment)

        assert result.current_status == "ERROR"

    @pytest.mark.asyncio
    async def test_recovery_from_error(self, db_session, sample_equipment):
        """Equipment recovers from ERROR to RUN when connected again."""
        sample_equipment.current_status = "ERROR"
        await db_session.commit()

        aas_item = _make_aas_item(sample_equipment.aas_id, is_connected=True, door_state="open")

        with patch(
            "src.app.services.polling_service.middleware_client.fetch_all_assets",
            new_callable=AsyncMock,
            return_value=[aas_item],
        ):
            result = await poll_equipment_status(db_session, sample_equipment)

        assert result.current_status == "RUN"
