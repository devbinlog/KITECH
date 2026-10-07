"""
Event-driven communication module for agents-workspace.

Provides:
- Base event model
- Domain-specific events (production, scheduling, quality)
- Redis-based event bus for pub/sub
"""

from .base import Event, EventMetadata
from .production import (
    WorkOrderCreatedEvent,
    WorkOrderStatusChangedEvent,
    ProductionRecordedEvent,
)
from .scheduling import (
    ScheduleRequestedEvent,
    ScheduleCompletedEvent,
)
from .quality import (
    InspectionCompletedEvent,
    NCRCreatedEvent,
)
from .bus import EventBus, get_event_bus

__all__ = [
    # Base
    "Event",
    "EventMetadata",
    # Production
    "WorkOrderCreatedEvent",
    "WorkOrderStatusChangedEvent",
    "ProductionRecordedEvent",
    # Scheduling
    "ScheduleRequestedEvent",
    "ScheduleCompletedEvent",
    # Quality
    "InspectionCompletedEvent",
    "NCRCreatedEvent",
    # Bus
    "EventBus",
    "get_event_bus",
]
