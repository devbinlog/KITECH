"""Inter-agent communication protocols."""

from .scheduler_protocol import (
    EquipmentAvailability,
    WorkOrderForScheduling,
    SchedulingRequest,
    SchedulingResult,
    ScheduledTask,
)

__all__ = [
    "EquipmentAvailability",
    "WorkOrderForScheduling",
    "SchedulingRequest",
    "SchedulingResult",
    "ScheduledTask",
]
