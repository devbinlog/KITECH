"""CNC machine data parser."""

from typing import Any, Dict, Tuple

from .base_parser import BaseParser


class CncParser(BaseParser):
    """Parser for CNC machine data."""

    def parse(self, raw_data: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        """
        Parse CNC machine raw data.

        Expected raw_data format:
        {
            "spindle_rpm": 15000,
            "load_percent": 45.5,
            "temperature": 80.2,
            "alarm_code": "0",
            "program_name": "O1234",
            "feed_rate": 5000,
            ...
        }

        Returns:
            Tuple of (parsed_data, status)
        """
        parsed = {
            "spindle_rpm": raw_data.get("spindle_rpm", 0),
            "load_percent": raw_data.get("load_percent", 0),
            "temperature": raw_data.get("temperature", 0),
            "alarm_code": str(raw_data.get("alarm_code", "0")),
            "program_name": raw_data.get("program_name", ""),
            "feed_rate": raw_data.get("feed_rate", 0),
            "axis_position": raw_data.get("axis_position", {}),
        }

        # Determine status based on alarm_code and spindle
        alarm = parsed["alarm_code"]
        if alarm and alarm != "0":
            status = "ERROR"
        elif parsed["spindle_rpm"] > 0:
            status = "RUN"
        else:
            status = "STOP"

        return parsed, status
