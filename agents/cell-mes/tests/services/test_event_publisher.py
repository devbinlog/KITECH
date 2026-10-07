"""
Tests for EventPublisher service.

Validates event publishing behavior for work orders and production.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
import sys
from pathlib import Path

# Add shared to path
_shared_path = Path(__file__).parent.parent.parent.parent.parent / "shared"
if str(_shared_path) not in sys.path:
    sys.path.insert(0, str(_shared_path))


class TestEventPublisher:
    """Test EventPublisher behavior."""

    @pytest.fixture
    def mock_event_bus(self):
        """Create a mock event bus."""
        bus = AsyncMock()
        bus.connect = AsyncMock()
        bus.publish = AsyncMock(return_value=1)
        bus.disconnect = AsyncMock()
        return bus

    @pytest.fixture
    def publisher(self, mock_event_bus):
        """Create an EventPublisher with mock bus."""
        from src.app.services.event_publisher import EventPublisher

        pub = EventPublisher(event_bus=mock_event_bus)
        pub._connected = True
        return pub

    @pytest.mark.asyncio
    async def test_publish_work_order_created(self, publisher, mock_event_bus):
        """Test work order created event is published."""
        import asyncio

        done = asyncio.Event()

        async def _signal(*args, **kwargs):
            done.set()
            return 1

        mock_event_bus.publish.side_effect = _signal

        await publisher.publish_work_order_created(
            work_order_id=1,
            lot_no="LOT-001",
            product_id=10,
            product_code="PROD-A",
            order_qty=100,
            priority=80,
            due_date=datetime(2024, 12, 31),
        )

        await asyncio.wait_for(done.wait(), timeout=2)

        # Verify event was published
        assert mock_event_bus.publish.called
        event = mock_event_bus.publish.call_args[0][0]
        assert event.event_type == "work_order.created"
        assert event.work_order_id == 1
        assert event.lot_no == "LOT-001"
        assert event.product_code == "PROD-A"

    @pytest.mark.asyncio
    async def test_publish_work_order_status_changed(self, publisher, mock_event_bus):
        """Test work order status change event is published."""
        import asyncio

        done = asyncio.Event()

        async def _signal(*args, **kwargs):
            done.set()
            return 1

        mock_event_bus.publish.side_effect = _signal

        await publisher.publish_work_order_status_changed(
            work_order_id=1,
            lot_no="LOT-001",
            previous_status="READY",
            new_status="RUNNING",
            changed_by="operator1",
        )

        await asyncio.wait_for(done.wait(), timeout=2)

        assert mock_event_bus.publish.called
        event = mock_event_bus.publish.call_args[0][0]
        assert event.event_type == "work_order.status_changed"
        assert event.previous_status == "READY"
        assert event.new_status == "RUNNING"

    @pytest.mark.asyncio
    async def test_publish_production_recorded(self, publisher, mock_event_bus):
        """Test production recorded event is published."""
        import asyncio

        done = asyncio.Event()

        async def _signal(*args, **kwargs):
            done.set()
            return 1

        mock_event_bus.publish.side_effect = _signal

        now = datetime.now(timezone.utc)
        await publisher.publish_production_recorded(
            work_order_id=1,
            lot_no="LOT-001",
            operation_id=5,
            equipment_id=10,
            equipment_name="CNC-01",
            ok_qty=95,
            ng_qty=5,
            start_time=now,
            end_time=now,
        )

        await asyncio.wait_for(done.wait(), timeout=2)

        assert mock_event_bus.publish.called
        event = mock_event_bus.publish.call_args[0][0]
        assert event.event_type == "production.recorded"
        assert event.ok_qty == 95
        assert event.ng_qty == 5
        assert event.equipment_name == "CNC-01"

    @pytest.mark.asyncio
    async def test_disabled_publisher_skips_events(self, mock_event_bus):
        """Test disabled publisher doesn't publish events."""
        import asyncio

        from src.app.services.event_publisher import EventPublisher

        publisher = EventPublisher(event_bus=mock_event_bus)
        publisher._enabled = False

        await publisher.publish_work_order_created(
            work_order_id=1,
            lot_no="LOT-001",
            product_id=10,
            product_code="PROD-A",
            order_qty=100,
        )

        # When disabled, publish_fire_and_forget returns immediately without
        # creating a task — no event to wait for, assertion is synchronous.
        await asyncio.sleep(0)  # yield to event loop once to drain any tasks

        assert not mock_event_bus.publish.called

    @pytest.mark.asyncio
    async def test_connect_on_first_publish(self, mock_event_bus):
        """Test auto-connect on first publish."""
        from src.app.services.event_publisher import EventPublisher

        publisher = EventPublisher(event_bus=mock_event_bus)
        publisher._connected = False

        await publisher._publish_async(MagicMock(event_type="test"))

        mock_event_bus.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_failure_logs_warning(self, publisher, mock_event_bus, caplog):
        """Test that publish failure logs a warning but doesn't raise."""
        mock_event_bus.publish.side_effect = Exception("Redis connection error")

        # Should not raise
        await publisher._publish_async(MagicMock(event_type="test"))

        # Warning should be logged
        assert "Failed to publish event" in caplog.text


class TestEventPublisherIntegration:
    """Integration tests for EventPublisher with production endpoint."""

    @pytest.mark.asyncio
    async def test_create_order_publishes_event(self, client, db_session):
        """Test that creating a work order publishes an event."""
        # This test verifies the endpoint calls event_publisher
        # In a real test, we'd mock the publisher at the dependency level
        pass  # Placeholder - actual test depends on test infrastructure
