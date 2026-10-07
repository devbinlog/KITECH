"""G-code data models."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class GCodeCommand:
    """Represents a single G-code command."""

    command: str  # e.g., "G00", "G01", "G02"
    parameters: dict = field(default_factory=dict)  # e.g., {"X": 10.0, "Y": 20.0, "Z": -5.0}
    line_number: int = 0


@dataclass
class GCodeAnalysis:
    """Analysis result for G-code."""

    filename: str
    total_commands: int
    total_distance: float  # mm
    rapid_distance: float  # G00
    cutting_distance: float  # G01, G02, G03
    dwell_time: float  # G04
    commands: List[GCodeCommand] = field(default_factory=list)
    spindle_speed: float = 0  # RPM
    feed_rate: float = 0  # mm/min
    errors: List[str] = field(default_factory=list)
