"""
Event publisher service for Cell-Scheduler.

Publishes scheduling events to Redis for consumption by other services.
Events are published asynchronously and don't block the main request.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add shared to path BEFORE importing from it
_shared_path = Path(__file__).parent.parent.parent.parent.parent / "shared"
if str(_shared_path) not in sys.path:
    sys.path.insert(0, str(_shared_path))

from shared.events import (
    EventBus,
    get_event_bus,
    ScheduleCompletedEvent,
    ScheduleRequestedEvent,
)

from ..config import settings

logger = logging.getLogger(__name__)


class EventPublisher:
    """
    Service for publishing scheduling events from Cell-Scheduler.

    Events are published fire-and-forget to avoid blocking the main request.
    If Redis is unavailable, events are logged and dropped.

    Usage:
        publisher = get_event_publisher()
        await publisher.publish_schedule_completed(result)
    """

    def __init__(self, event_bus: Optional[EventBus] = None):
        """
        Initialize the event publisher.

        Args:
            event_bus: Optional event bus instance (uses global if not provided)
        """
        self._event_bus = event_bus
        self._connected = False
        self._enabled = True  # Can be disabled for testing

    @property
    def event_bus(self) -> EventBus:
        """Get or create the event bus."""
        if self._event_bus is None:
            self._event_bus = get_event_bus(
                redis_url=settings.REDIS_URL,
                source_service="cell-scheduler",
            )
        return self._event_bus

    async def connect(self) -> bool:
        """
        Connect to Redis.

        Returns:
            True if connected, False otherwise
        """
        if self._connected:
            return True

        try:
            await self.event_bus.connect()
            self._connected = True
            logger.info("Event publisher connected to Redis")
            return True
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._event_bus:
            await self._event_bus.disconnect()
            self._connected = False

    async def _publish_async(self, event) -> None:
        """
        Publish an event asynchronously (fire-and-forget).

        Errors are logged but don't propagate.
        """
        if not self._enabled:
            return

        try:
            if not self._connected:
                await self.connect()

            if self._connected:
                await self.event_bus.publish(event)
                logger.debug(f"Published event: {event.event_type}")
        except Exception as e:
            logger.warning(f"Failed to publish event {event.event_type}: {e}")

    def publish_fire_and_forget(self, event) -> None:
        """
        Schedule event publishing without waiting.

        Creates a background task to publish the event.
        """
        if not self._enabled:
            return

        try:
            asyncio.create_task(self._publish_async(event))
        except RuntimeError:
            # No event loop running (e.g., during startup)
            logger.debug(f"Skipping event publish (no event loop): {event.event_type}")

    # =========================================================================
    # Scheduling Events
    # =========================================================================

    async def publish_schedule_requested(
        self,
        request_id: str,
        horizon_hours: int = 24,
        solver_type: str = "OR_TOOLS",
        time_limit_sec: int = 60,
        requested_by: Optional[str] = None,
    ) -> None:
        """Publish schedule requested event."""
        event = ScheduleRequestedEvent(
            request_id=request_id,
            horizon_hours=horizon_hours,
            solver_type=solver_type,
            time_limit_sec=time_limit_sec,
            requested_by=requested_by,
        )
        self.publish_fire_and_forget(event)

    async def publish_schedule_completed(
        self,
        request_id: str,
        success: bool,
        solver_type: str,
        makespan_hours: Optional[float] = None,
        total_jobs_scheduled: int = 0,
        total_machines_used: int = 0,
        objective_value: Optional[float] = None,
        solve_time_sec: float = 0.0,
        error_message: Optional[str] = None,
        schedule_summary: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Publish schedule completed event."""
        event = ScheduleCompletedEvent(
            request_id=request_id,
            success=success,
            solver_type=solver_type,
            makespan_hours=makespan_hours,
            total_jobs_scheduled=total_jobs_scheduled,
            total_machines_used=total_machines_used,
            objective_value=objective_value,
            solve_time_sec=solve_time_sec,
            error_message=error_message,
            schedule_summary=schedule_summary or {},
        )
        self.publish_fire_and_forget(event)


# Global publisher instance
_publisher: Optional[EventPublisher] = None


def get_event_publisher() -> EventPublisher:
    """Get the global event publisher instance."""
    global _publisher
    if _publisher is None:
        _publisher = EventPublisher()
    return _publisher


async def init_event_publisher() -> EventPublisher:
    """Initialize and connect the event publisher."""
    publisher = get_event_publisher()
    await publisher.connect()
    return publisher


async def shutdown_event_publisher() -> None:
    """Shutdown the event publisher."""
    global _publisher
    if _publisher:
        await _publisher.disconnect()
        _publisher = None
