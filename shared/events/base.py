"""
Base event model and metadata.

All domain events inherit from the Event base class.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field


class EventMetadata(BaseModel):
    """Metadata attached to every event."""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_service: str = ""
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    version: int = 1


class Event(BaseModel):
    """
    Base class for all domain events.

    Events are immutable records of something that happened in the system.
    They are published to the event bus and consumed by interested services.

    Example:
        class WorkOrderCreatedEvent(Event):
            event_type: str = "work_order.created"
            work_order_id: int
            lot_no: str
            product_id: int
    """

    model_config = ConfigDict(frozen=True)  # Events are immutable

    event_type: str = "base.event"
    metadata: EventMetadata = Field(default_factory=EventMetadata)
    payload: Dict[str, Any] = Field(default_factory=dict)

    def to_channel(self) -> str:
        """
        Get the Redis channel name for this event.

        Uses dot-separated event_type as channel name.
        Example: "work_order.created" -> "events:work_order.created"
        """
        return f"events:{self.event_type}"

    def with_correlation(self, correlation_id: str) -> "Event":
        """Create a copy with correlation ID set."""
        new_metadata = self.metadata.model_copy(update={"correlation_id": correlation_id})
        return self.model_copy(update={"metadata": new_metadata})

    def with_causation(self, causation_id: str) -> "Event":
        """Create a copy with causation ID set (ID of the event that caused this one)."""
        new_metadata = self.metadata.model_copy(update={"causation_id": causation_id})
        return self.model_copy(update={"metadata": new_metadata})

    def with_source(self, source_service: str) -> "Event":
        """Create a copy with source service set."""
        new_metadata = self.metadata.model_copy(update={"source_service": source_service})
        return self.model_copy(update={"metadata": new_metadata})
