"""Tests for EventPublisher service."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from src.app.services.event_publisher import EventPublisher, get_event_publisher


class TestEventPublisherConnect:
    """Test connection management."""

    @pytest.mark.asyncio
    async def test_connect_returns_true_on_success(self):
        mock_bus = AsyncMock()
        mock_bus.connect = AsyncMock()
        publisher = EventPublisher(event_bus=mock_bus)
        result = await publisher.connect()
        assert result is True
        assert publisher._connected is True

    @pytest.mark.asyncio
    async def test_connect_returns_false_on_failure(self):
        mock_bus = AsyncMock()
        mock_bus.connect = AsyncMock(side_effect=ConnectionRefusedError("Redis down"))
        publisher = EventPublisher(event_bus=mock_bus)
        result = await publisher.connect()
        assert result is False
        assert publisher._connected is False

    @pytest.mark.asyncio
    async def test_connect_is_idempotent(self):
        mock_bus = AsyncMock()
        mock_bus.connect = AsyncMock()
        publisher = EventPublisher(event_bus=mock_bus)
        await publisher.connect()
        await publisher.connect()
        # connect() on bus should only be called once
        mock_bus.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_clears_connected_flag(self):
        mock_bus = AsyncMock()
        mock_bus.connect = AsyncMock()
        mock_bus.disconnect = AsyncMock()
        publisher = EventPublisher(event_bus=mock_bus)
        await publisher.connect()
        await publisher.disconnect()
        assert publisher._connected is False
        mock_bus.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_when_no_bus(self):
        publisher = EventPublisher(event_bus=None)
        # Should not raise even if _event_bus is None
        publisher._event_bus = None
        await publisher.disconnect()  # no-op


class TestEventPublisherPublish:
    """Test event publishing behavior."""

    def _make_connected_publisher(self) -> tuple[EventPublisher, AsyncMock]:
        mock_bus = AsyncMock()
        mock_bus.publish = AsyncMock()
        publisher = EventPublisher(event_bus=mock_bus)
        publisher._connected = True
        return publisher, mock_bus

    @pytest.mark.asyncio
    async def test_publish_async_calls_bus_publish(self):
        publisher, mock_bus = self._make_connected_publisher()
        mock_event = MagicMock()
        mock_event.event_type = "test.event"
        await publisher._publish_async(mock_event)
        mock_bus.publish.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_publish_async_skipped_when_disabled(self):
        publisher, mock_bus = self._make_connected_publisher()
        publisher._enabled = False
        mock_event = MagicMock()
        mock_event.event_type = "test.event"
        await publisher._publish_async(mock_event)
        mock_bus.publish.assert_not_called()

    @pytest.mark.asyncio
    async def test_publish_async_handles_bus_error_gracefully(self):
        mock_bus = AsyncMock()
        mock_bus.publish = AsyncMock(side_effect=RuntimeError("Redis error"))
        publisher = EventPublisher(event_bus=mock_bus)
        publisher._connected = True
        mock_event = MagicMock()
        mock_event.event_type = "test.event"
        # Should not raise
        await publisher._publish_async(mock_event)

    @pytest.mark.asyncio
    async def test_publish_async_connects_if_not_connected(self):
        mock_bus = AsyncMock()
        mock_bus.connect = AsyncMock()
        mock_bus.publish = AsyncMock()
        publisher = EventPublisher(event_bus=mock_bus)
        publisher._connected = False
        mock_event = MagicMock()
        mock_event.event_type = "test.event"
        await publisher._publish_async(mock_event)
        mock_bus.connect.assert_called_once()

    def test_publish_fire_and_forget_skipped_when_disabled(self):
        mock_bus = AsyncMock()
        publisher = EventPublisher(event_bus=mock_bus)
        publisher._enabled = False
        mock_event = MagicMock()
        mock_event.event_type = "test.event"
        # Should not raise and should do nothing
        publisher.publish_fire_and_forget(mock_event)


class TestWorkOrderEvents:
    """Test work order event publishing."""

    @pytest.mark.asyncio
    async def test_publish_work_order_created(self):
        mock_bus = AsyncMock()
        mock_bus.publish = AsyncMock()
        publisher = EventPublisher(event_bus=mock_bus)
        publisher._connected = True

        with patch.object(publisher, "publish_fire_and_forget") as mock_ff:
            await publisher.publish_work_order_created(
                work_order_id=1,
                lot_no="LOT-001",
                product_id=10,
                product_code="PROD-A",
                order_qty=50,
                priority=30,
            )
            mock_ff.assert_called_once()
            event = mock_ff.call_args[0][0]
            assert event.work_order_id == 1
            assert event.lot_no == "LOT-001"
            assert event.product_code == "PROD-A"
            assert event.order_qty == 50

    @pytest.mark.asyncio
    async def test_publish_work_order_status_changed(self):
        publisher = EventPublisher(event_bus=AsyncMock())
        with patch.object(publisher, "publish_fire_and_forget") as mock_ff:
            await publisher.publish_work_order_status_changed(
                work_order_id=2,
                lot_no="LOT-002",
                previous_status="READY",
                new_status="RUNNING",
                changed_by="operator1",
            )
            mock_ff.assert_called_once()
            event = mock_ff.call_args[0][0]
            assert event.previous_status == "READY"
            assert event.new_status == "RUNNING"
            assert event.changed_by == "operator1"


class TestProductionEvents:
    """Test production event publishing."""

    @pytest.mark.asyncio
    async def test_publish_production_recorded(self):
        from datetime import datetime, timezone

        publisher = EventPublisher(event_bus=AsyncMock())
        now = datetime.now(timezone.utc)

        with patch.object(publisher, "publish_fire_and_forget") as mock_ff:
            await publisher.publish_production_recorded(
                work_order_id=1,
                lot_no="LOT-001",
                operation_id=5,
                equipment_id=3,
                equipment_name="CNC-01",
                ok_qty=90,
                ng_qty=5,
                start_time=now,
                end_time=now,
                scrap_qty=2,
                defect_codes=["D001"],
            )
            mock_ff.assert_called_once()
            event = mock_ff.call_args[0][0]
            assert event.ok_qty == 90
            assert event.ng_qty == 5
            assert event.defect_codes == ["D001"]


class TestQualityEvents:
    """Test quality event publishing."""

    @pytest.mark.asyncio
    async def test_publish_inspection_completed(self):
        publisher = EventPublisher(event_bus=AsyncMock())
        with patch.object(publisher, "publish_fire_and_forget") as mock_ff:
            await publisher.publish_inspection_completed(
                inspection_id=10,
                work_order_id=1,
                lot_no="LOT-001",
                inspection_type="IN_PROCESS",
                result="PASS",
                sample_size=5,
                defects_found=0,
            )
            mock_ff.assert_called_once()
            event = mock_ff.call_args[0][0]
            assert event.result == "PASS"
            assert event.sample_size == 5

    @pytest.mark.asyncio
    async def test_publish_ncr_created(self):
        publisher = EventPublisher(event_bus=AsyncMock())
        with patch.object(publisher, "publish_fire_and_forget") as mock_ff:
            await publisher.publish_ncr_created(
                ncr_id=99,
                ncr_number="NCR-2026-0001",
                ncr_type="DIMENSION",
                severity="MAJOR",
                description="Diameter out of spec",
                affected_qty=3,
                work_order_id=1,
                lot_no="LOT-001",
            )
            mock_ff.assert_called_once()
            event = mock_ff.call_args[0][0]
            assert event.ncr_number == "NCR-2026-0001"
            assert event.severity == "MAJOR"
            assert event.affected_qty == 3

    @pytest.mark.asyncio
    async def test_publish_inspection_completed_defaults_empty_collections(self):
        publisher = EventPublisher(event_bus=AsyncMock())
        with patch.object(publisher, "publish_fire_and_forget") as mock_ff:
            await publisher.publish_inspection_completed(
                inspection_id=1,
                work_order_id=1,
                lot_no="L",
                inspection_type="FINAL",
                result="FAIL",
            )
            event = mock_ff.call_args[0][0]
            assert event.measurements == {}
            assert event.out_of_spec_items == []


class TestGetEventPublisher:
    """Test global event publisher singleton."""

    def test_returns_event_publisher_instance(self):
        pub = get_event_publisher()
        assert isinstance(pub, EventPublisher)

    def test_returns_same_instance_each_call(self):
        pub1 = get_event_publisher()
        pub2 = get_event_publisher()
        assert pub1 is pub2
