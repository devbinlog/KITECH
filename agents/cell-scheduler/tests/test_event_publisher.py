"""
Tests for Cell-Scheduler EventPublisher service.

Validates event publishing behavior for scheduling operations.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
import sys
from pathlib import Path

# Add shared to path
_shared_path = Path(__file__).parent.parent.parent.parent / "shared"
if str(_shared_path) not in sys.path:
    sys.path.insert(0, str(_shared_path))


class TestSchedulerEventPublisher:
    """Test Scheduler EventPublisher behavior."""

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
    async def test_publish_schedule_completed_success(self, publisher, mock_event_bus):
        """Test schedule completed event is published on success."""
        import asyncio

        done = asyncio.Event()

        async def _signal(*args, **kwargs):
            done.set()
            return 1

        mock_event_bus.publish.side_effect = _signal

        await publisher.publish_schedule_completed(
            request_id="req-001",
            success=True,
            solver_type="OR_TOOLS",
            makespan_hours=24.5,
            total_jobs_scheduled=10,
            total_machines_used=5,
            objective_value=1000.0,
            solve_time_sec=15.3,
            schedule_summary={
                "status": "OPTIMAL",
                "bottleneck_machines": ["CNC-01"],
            },
        )

        await asyncio.wait_for(done.wait(), timeout=2)

        assert mock_event_bus.publish.called
        event = mock_event_bus.publish.call_args[0][0]
        assert event.event_type == "schedule.completed"
        assert event.request_id == "req-001"
        assert event.success is True
        assert event.solver_type == "OR_TOOLS"
        assert event.makespan_hours == 24.5
        assert event.total_jobs_scheduled == 10

    @pytest.mark.asyncio
    async def test_publish_schedule_completed_failure(self, publisher, mock_event_bus):
        """Test schedule completed event is published on failure."""
        import asyncio

        done = asyncio.Event()

        async def _signal(*args, **kwargs):
            done.set()
            return 1

        mock_event_bus.publish.side_effect = _signal

        await publisher.publish_schedule_completed(
            request_id="req-002",
            success=False,
            solver_type="GA",
            error_message="No feasible solution found",
        )

        await asyncio.wait_for(done.wait(), timeout=2)

        assert mock_event_bus.publish.called
        event = mock_event_bus.publish.call_args[0][0]
        assert event.event_type == "schedule.completed"
        assert event.success is False
        assert event.error_message == "No feasible solution found"

    @pytest.mark.asyncio
    async def test_publish_schedule_requested(self, publisher, mock_event_bus):
        """Test schedule requested event is published."""
        import asyncio

        done = asyncio.Event()

        async def _signal(*args, **kwargs):
            done.set()
            return 1

        mock_event_bus.publish.side_effect = _signal

        await publisher.publish_schedule_requested(
            request_id="req-003",
            horizon_hours=48,
            solver_type="TABU",
            time_limit_sec=120,
            requested_by="system",
        )

        await asyncio.wait_for(done.wait(), timeout=2)

        assert mock_event_bus.publish.called
        event = mock_event_bus.publish.call_args[0][0]
        assert event.event_type == "schedule.requested"
        assert event.horizon_hours == 48
        assert event.solver_type == "TABU"

    @pytest.mark.asyncio
    async def test_disabled_publisher_skips_events(self, mock_event_bus):
        """Test disabled publisher doesn't publish events."""
        import asyncio

        from src.app.services.event_publisher import EventPublisher

        publisher = EventPublisher(event_bus=mock_event_bus)
        publisher._enabled = False

        await publisher.publish_schedule_completed(
            request_id="req-004",
            success=True,
            solver_type="SA",
        )

        # When disabled, publish_fire_and_forget returns immediately without
        # creating a task — yield once to drain any pending tasks.
        await asyncio.sleep(0)

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


class TestGetEventPublisher:
    """Test get_event_publisher singleton behavior."""

    def test_get_event_publisher_returns_same_instance(self):
        """Test that get_event_publisher returns the same instance."""
        from src.app.services.event_publisher import get_event_publisher
        import src.app.services.event_publisher as module

        # Reset global
        module._publisher = None

        pub1 = get_event_publisher()
        pub2 = get_event_publisher()

        assert pub1 is pub2

        # Cleanup
        module._publisher = None
