"""PLC data parser."""

from typing import Any, Dict, Tuple

from .base_parser import BaseParser


class PlcParser(BaseParser):
    """Parser for PLC data."""

    def parse(self, raw_data: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        """
        Parse PLC raw data.

        Expected raw_data format:
        {
            "registers": {"D0": 100, "D1": 200, ...},
            "coils": {"M0": true, "M1": false, ...},
            "error_flag": false,
            "cycle_count": 12345,
            "running": true,
            ...
        }

        Returns:
            Tuple of (parsed_data, status)
        """
        parsed = {
            "registers": raw_data.get("registers", {}),
            "coils": raw_data.get("coils", {}),
            "error_flag": raw_data.get("error_flag", False),
            "cycle_count": raw_data.get("cycle_count", 0),
            "running": raw_data.get("running", False),
        }

        # Determine status
        if parsed["error_flag"]:
            status = "ERROR"
        elif parsed["running"]:
            status = "RUN"
        else:
            status = "STOP"

        return parsed, status
