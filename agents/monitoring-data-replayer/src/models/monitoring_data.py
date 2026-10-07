"""MonitoringRecord dataclass for CNC monitoring data."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any


@dataclass
class MonitoringRecord:
    """
    A single monitoring record from CNC machine.

    Attributes:
        timestamp: Record timestamp
        spindle_rpm: Actual spindle RPM (crpm)
        cmd_spindle_rpm: Commanded spindle RPM (ccrpm)
        feedrate: Actual feedrate mm/min (cfr)
        cmd_feedrate: Commanded feedrate mm/min (ccfr)
        position: Machine position (cpx, cpy, cpz)
        gcode_cmd: Current G-code command (cmdl)
        vibration_rms: Vibration RMS value (asprms)
        accel_rms: Acceleration RMS value (aaccrms)
        cutting: Whether cutting is active (cut)
        estimated_wear: Estimated tool wear (estwear)
        estimated_force: Estimated cutting force (estforce)
    """

    timestamp: datetime
    spindle_rpm: float = 0.0
    cmd_spindle_rpm: float = 0.0
    feedrate: float = 0.0
    cmd_feedrate: float = 0.0
    position: tuple[float, float, float] = field(default_factory=lambda: (0.0, 0.0, 0.0))
    gcode_cmd: str = ""
    vibration_rms: float = 0.0
    accel_rms: float = 0.0
    cutting: bool = False
    estimated_wear: float = 0.0
    estimated_force: float = 0.0

    # Optional extended fields
    elapsed_time: float = 0.0  # ctime
    program_name: str = ""  # cpn
    tool_number: int = 0  # ct

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["position"] = list(self.position)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MonitoringRecord":
        """Create from dictionary."""
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        if isinstance(data.get("position"), (list, tuple)):
            data["position"] = tuple(data["position"])
        return cls(**data)

    def __repr__(self) -> str:
        return (
            f"MonitoringRecord(t={self.timestamp.strftime('%H:%M:%S.%f')[:-3]}, "
            f"rpm={self.spindle_rpm:.0f}, fr={self.feedrate:.0f}, "
            f"pos=({self.position[0]:.2f}, {self.position[1]:.2f}, {self.position[2]:.2f}), "
            f"cut={self.cutting})"
        )
