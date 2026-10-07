"""CAM-related data models."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ToolData:
    """Tool information."""

    tool_id: int
    name: str
    diameter: float  # mm
    tool_type: str  # e.g., "endmill", "ballnose"
    description: str = ""


@dataclass
class CuttingData:
    """Cutting parameters for a tool path."""

    Ap: float  # Axial depth of cut (mm)
    Ae: float  # Radial depth of cut (mm)
    feed_per_tooth: float = 0  # mm/tooth
    spindle_speed: float = 0  # RPM
    tool_id: Optional[int] = None
    notes: str = ""

    @property
    def feed_rate(self) -> float:
        """Calculate feed rate (mm/min)."""
        # feed_rate = RPM * number_of_teeth * feed_per_tooth
        # This is a simplified version
        return self.spindle_speed * self.feed_per_tooth if self.feed_per_tooth > 0 else 0
