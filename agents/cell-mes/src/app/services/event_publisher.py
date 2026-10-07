"""
Event publisher service for Cell-MES.

Publishes integration events to Redis for consumption by other services.
Events are published asynchronously and don't block the main request.

(Naming: previously called "domain events" — that DDD layer was removed in
commit 7ae4c39. Now simply "events" or "integration events".)
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

# Add shared to path BEFORE importing from it
_shared_path = Path(__file__).parent.parent.parent.parent.parent / "shared"
if str(_shared_path) not in sys.path:
    sys.path.insert(0, str(_shared_path))

from shared.events import (
    EventBus,
    get_event_bus,
    WorkOrderCreatedEvent,
    WorkOrderStatusChangedEvent,
    ProductionRecordedEvent,
    InspectionCompletedEvent,
    NCRCreatedEvent,
)

from ..core.config import settings

logger = logging.getLogger(__name__)


class EventPublisher:
    """
    Service for publishing events from Cell-MES.

    Events are published fire-and-forget to avoid blocking the main request.
    If Redis is unavailable, events are logged and dropped.

    Usage:
        publisher = get_event_publisher()
        await publisher.publish_work_order_created(work_order)
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
                source_service="cell-mes",
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
    # Work Order Events
    # =========================================================================

    async def publish_work_order_created(
        self,
        work_order_id: int,
        lot_no: str,
        product_id: int,
        product_code: str,
        order_qty: int,
        priority: int = 50,
        due_date=None,
        release_date=None,
    ) -> None:
        """Publish work order created event."""
        event = WorkOrderCreatedEvent(
            work_order_id=work_order_id,
            lot_no=lot_no,
            product_id=product_id,
            product_code=product_code,
            order_qty=order_qty,
            priority=priority,
            due_date=due_date,
            release_date=release_date,
        )
        self.publish_fire_and_forget(event)

    async def publish_work_order_status_changed(
        self,
        work_order_id: int,
        lot_no: str,
        previous_status: str,
        new_status: str,
        changed_by: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> None:
        """Publish work order status changed event."""
        event = WorkOrderStatusChangedEvent(
            work_order_id=work_order_id,
            lot_no=lot_no,
            previous_status=previous_status,
            new_status=new_status,
            changed_by=changed_by,
            reason=reason,
        )
        self.publish_fire_and_forget(event)

    # =========================================================================
    # Production Events
    # =========================================================================

    async def publish_production_recorded(
        self,
        work_order_id: int,
        lot_no: str,
        operation_id: int,
        equipment_id: int,
        equipment_name: str,
        ok_qty: int,
        ng_qty: int,
        start_time,
        end_time,
        scrap_qty: int = 0,
        defect_codes=None,
    ) -> None:
        """Publish production recorded event."""
        event = ProductionRecordedEvent(
            work_order_id=work_order_id,
            lot_no=lot_no,
            operation_id=operation_id,
            equipment_id=equipment_id,
            equipment_name=equipment_name,
            ok_qty=ok_qty,
            ng_qty=ng_qty,
            scrap_qty=scrap_qty,
            start_time=start_time,
            end_time=end_time,
            defect_codes=defect_codes or [],
        )
        self.publish_fire_and_forget(event)

    # =========================================================================
    # Quality Events
    # =========================================================================

    async def publish_inspection_completed(
        self,
        inspection_id: int,
        work_order_id: int,
        lot_no: str,
        inspection_type: str,
        result: str,
        sample_size: int = 0,
        defects_found: int = 0,
        operation_id: Optional[int] = None,
        inspector_id: Optional[str] = None,
        measurements: Optional[dict] = None,
        out_of_spec_items: Optional[list] = None,
    ) -> None:
        """Publish inspection completed event."""
        event = InspectionCompletedEvent(
            inspection_id=inspection_id,
            work_order_id=work_order_id,
            lot_no=lot_no,
            inspection_type=inspection_type,
            result=result,
            sample_size=sample_size,
            defects_found=defects_found,
            operation_id=operation_id,
            inspector_id=inspector_id,
            measurements=measurements or {},
            out_of_spec_items=out_of_spec_items or [],
        )
        self.publish_fire_and_forget(event)

    async def publish_ncr_created(
        self,
        ncr_id: int,
        ncr_number: str,
        ncr_type: str,
        severity: str = "MINOR",
        description: str = "",
        affected_qty: int = 0,
        work_order_id: Optional[int] = None,
        lot_no: Optional[str] = None,
        product_id: Optional[int] = None,
        equipment_id: Optional[int] = None,
        source: str = "INSPECTION",
        created_by: Optional[str] = None,
    ) -> None:
        """Publish NCR created event."""
        event = NCRCreatedEvent(
            ncr_id=ncr_id,
            ncr_number=ncr_number,
            ncr_type=ncr_type,
            severity=severity,
            description=description,
            affected_qty=affected_qty,
            work_order_id=work_order_id,
            lot_no=lot_no,
            product_id=product_id,
            equipment_id=equipment_id,
            source=source,
            created_by=created_by,
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
