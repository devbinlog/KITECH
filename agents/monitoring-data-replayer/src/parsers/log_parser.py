"""LOG/TSV file parser for CNC monitoring data."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

from ..models.monitoring_data import MonitoringRecord


class LogParser:
    """Parser for tab-separated LOG files from CNC monitoring systems."""

    # Column mapping from LOG file to MonitoringRecord fields
    COLUMN_MAP = {
        "time": "time",
        "ctime": "elapsed_time",
        "crpm": "spindle_rpm",
        "ccrpm": "cmd_spindle_rpm",
        "cfr": "feedrate",
        "ccfr": "cmd_feedrate",
        "cmdl": "gcode_cmd",
        "cpx": "pos_x",
        "cpy": "pos_y",
        "cpz": "pos_z",
        "ct": "tool_number",
        "cpn": "program_name",
        "asprms": "vibration_rms",
        "aaccrms": "accel_rms",
        "cut": "cutting",
        "estwear": "estimated_wear",
        "estforce": "estimated_force",
    }

    def __init__(self, path: str | Path):
        """Initialize parser with file path."""
        self.path = Path(path)
        self._headers: list[str] = []
        self._record_count: Optional[int] = None
        self._time_range: Optional[tuple[datetime, datetime]] = None

    def _parse_timestamp(self, time_str: str) -> datetime:
        """Parse timestamp from LOG format (YYMMDD HH:MM:SS.mmm)."""
        # Format: "250112 11:18:11.450" -> 2025-01-12 11:18:11.450000
        try:
            parts = time_str.strip().split(" ")
            if len(parts) == 2:
                date_part = parts[0]  # YYMMDD
                time_part = parts[1]  # HH:MM:SS.mmm

                year = 2000 + int(date_part[:2])
                month = int(date_part[2:4])
                day = int(date_part[4:6])

                time_parts = time_part.split(":")
                hour = int(time_parts[0])
                minute = int(time_parts[1])
                sec_parts = time_parts[2].split(".")
                second = int(sec_parts[0])
                microsecond = int(sec_parts[1]) * 1000 if len(sec_parts) > 1 else 0

                return datetime(year, month, day, hour, minute, second, microsecond)
        except (ValueError, IndexError):
            pass

        # Fallback: return current time
        return datetime.now(timezone.utc)

    def _parse_row(self, headers: list[str], values: list[str]) -> MonitoringRecord:
        """Parse a single row into MonitoringRecord."""
        data: dict = {}

        for i, header in enumerate(headers):
            if i >= len(values):
                continue
            value = values[i].strip()

            if header == "time":
                data["timestamp"] = self._parse_timestamp(value)
            elif header == "ctime":
                data["elapsed_time"] = float(value) if value else 0.0
            elif header == "crpm":
                data["spindle_rpm"] = float(value) if value else 0.0
            elif header == "ccrpm":
                data["cmd_spindle_rpm"] = float(value) if value else 0.0
            elif header == "cfr":
                data["feedrate"] = float(value) if value else 0.0
            elif header == "ccfr":
                data["cmd_feedrate"] = float(value) if value else 0.0
            elif header == "cmdl":
                data["gcode_cmd"] = value
            elif header == "cpx":
                data["pos_x"] = float(value) if value else 0.0
            elif header == "cpy":
                data["pos_y"] = float(value) if value else 0.0
            elif header == "cpz":
                data["pos_z"] = float(value) if value else 0.0
            elif header == "ct":
                data["tool_number"] = int(float(value)) if value else 0
            elif header == "cpn":
                data["program_name"] = value
            elif header == "asprms":
                data["vibration_rms"] = float(value) if value else 0.0
            elif header == "aaccrms":
                data["accel_rms"] = float(value) if value else 0.0
            elif header == "cut":
                data["cutting"] = bool(int(float(value))) if value else False
            elif header == "estwear":
                data["estimated_wear"] = float(value) if value else 0.0
            elif header == "estforce":
                data["estimated_force"] = float(value) if value else 0.0

        # Build position tuple
        position = (
            data.pop("pos_x", 0.0),
            data.pop("pos_y", 0.0),
            data.pop("pos_z", 0.0),
        )

        return MonitoringRecord(
            timestamp=data.get("timestamp", datetime.now(timezone.utc)),
            spindle_rpm=data.get("spindle_rpm", 0.0),
            cmd_spindle_rpm=data.get("cmd_spindle_rpm", 0.0),
            feedrate=data.get("feedrate", 0.0),
            cmd_feedrate=data.get("cmd_feedrate", 0.0),
            position=position,
            gcode_cmd=data.get("gcode_cmd", ""),
            vibration_rms=data.get("vibration_rms", 0.0),
            accel_rms=data.get("accel_rms", 0.0),
            cutting=data.get("cutting", False),
            estimated_wear=data.get("estimated_wear", 0.0),
            estimated_force=data.get("estimated_force", 0.0),
            elapsed_time=data.get("elapsed_time", 0.0),
            program_name=data.get("program_name", ""),
            tool_number=data.get("tool_number", 0),
        )

    def parse(self) -> Iterator[MonitoringRecord]:
        """Parse LOG file and yield MonitoringRecord objects."""
        with open(self.path, "r", encoding="utf-8", errors="replace") as f:
            # Read header line
            header_line = f.readline()
            self._headers = [h.strip() for h in header_line.split("\t")]

            # Parse data lines
            for line in f:
                if not line.strip():
                    continue
                values = line.split("\t")
                try:
                    yield self._parse_row(self._headers, values)
                except Exception:
                    continue  # Skip malformed rows

    def get_headers(self) -> list[str]:
        """Get column headers from the file."""
        if not self._headers:
            with open(self.path, "r", encoding="utf-8", errors="replace") as f:
                header_line = f.readline()
                self._headers = [h.strip() for h in header_line.split("\t")]
        return self._headers

    def get_record_count(self) -> int:
        """Get total number of data records (excluding header)."""
        if self._record_count is None:
            with open(self.path, "r", encoding="utf-8", errors="replace") as f:
                self._record_count = sum(1 for line in f if line.strip()) - 1  # -1 for header
        return self._record_count

    def get_time_range(self) -> tuple[datetime, datetime]:
        """Get start and end timestamps from the file."""
        if self._time_range is None:
            first_ts = None
            last_ts = None

            with open(self.path, "r", encoding="utf-8", errors="replace") as f:
                headers = f.readline().split("\t")
                time_idx = 0
                for i, h in enumerate(headers):
                    if h.strip() == "time":
                        time_idx = i
                        break

                for line in f:
                    if not line.strip():
                        continue
                    values = line.split("\t")
                    if len(values) > time_idx:
                        ts = self._parse_timestamp(values[time_idx])
                        if first_ts is None:
                            first_ts = ts
                        last_ts = ts

            if first_ts is None:
                first_ts = datetime.now(timezone.utc)
            if last_ts is None:
                last_ts = first_ts

            self._time_range = (first_ts, last_ts)

        return self._time_range

    def get_file_info(self) -> dict:
        """Get file metadata."""
        time_range = self.get_time_range()
        return {
            "path": str(self.path),
            "format": "LOG",
            "headers": self.get_headers(),
            "record_count": self.get_record_count(),
            "start_time": time_range[0].isoformat(),
            "end_time": time_range[1].isoformat(),
            "duration_seconds": (time_range[1] - time_range[0]).total_seconds(),
            "file_size_bytes": self.path.stat().st_size,
        }
