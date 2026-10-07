"""Robot/AMR data parser."""

from typing import Any, Dict, Tuple

from .base_parser import BaseParser


class RobotParser(BaseParser):
    """Parser for Robot and AMR data."""

    def parse(self, raw_data: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        """
        Parse Robot/AMR raw data.

        Expected raw_data format:
        {
            "joint_angles": [0, 45, 90, -45, 0, 0],
            "battery_level": 85,
            "current_position": {"x": 100.0, "y": 200.0, "z": 50.0},
            "is_moving": true,
            "error_code": null,
            "task_id": "TASK-001",
            ...
        }

        Returns:
            Tuple of (parsed_data, status)
        """
        parsed = {
            "joint_angles": raw_data.get("joint_angles", []),
            "battery_level": raw_data.get("battery_level", 0),
            "current_position": raw_data.get("current_position", {}),
            "is_moving": raw_data.get("is_moving", False),
            "error_code": raw_data.get("error_code"),
            "task_id": raw_data.get("task_id", ""),
            "speed_percent": raw_data.get("speed_percent", 0),
        }

        # Determine status
        error = parsed["error_code"]
        if error and error != "0" and error != "":
            status = "ERROR"
        elif parsed["is_moving"]:
            status = "RUN"
        else:
            status = "STOP"

        return parsed, status
