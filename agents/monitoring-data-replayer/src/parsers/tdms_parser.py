"""TDMS file parser for CNC monitoring data using nptdms."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator, Optional

import numpy as np
from nptdms import TdmsFile

from ..models.monitoring_data import MonitoringRecord


class TDMSParser:
    """Parser for TDMS binary files from CNC monitoring systems."""

    # Channel name mapping - supports both standard names and TDMS-specific names
    CHANNEL_ALIASES = {
        # Standard LOG column names
        "crpm": ["crpm", "cnc-spindlespeed", "spindlespeed"],
        "ccrpm": ["ccrpm", "cnc-commandedrpm", "commandedrpm"],
        "cfr": ["cfr", "cnc-actualfeedrate", "actualfeedrate", "feedrate"],
        "ccfr": ["ccfr", "cnc-commandedfeedrate", "commandedfeedrate"],
        "cpx": ["cpx", "cnc-x-position", "x-position"],
        "cpy": ["cpy", "cnc-y-position", "y-position"],
        "cpz": ["cpz", "cnc-z-position", "z-position"],
        "cmdl": ["cmdl", "cnc-gmodal", "gmodal", "cnc-currentblock"],
        "ct": ["ct", "cnc-toolnumber", "toolnumber"],
        "cpn": ["cpn", "cnc-programname", "programname"],
        "time": ["time", "time channel cnc", "timestamp"],
        "ctime": ["ctime", "elapsed_time"],
        "cut": ["cut", "cutting"],
        "estwear": ["estwear", "estimated_wear"],
        "estforce": ["estforce", "estimated_force"],
        "asprms": ["asprms", "daq-spindle-c-r", "spindle-c-r"],
        "aaccrms": ["aaccrms", "daq-acc-1", "acc-1"],
    }

    def __init__(self, path: str | Path):
        """Initialize parser with file path."""
        self.path = Path(path)
        self._tdms_file: Optional[TdmsFile] = None
        self._channels: Optional[list[str]] = None
        self._record_count: Optional[int] = None
        self._time_range: Optional[tuple[datetime, datetime]] = None
        self._channel_cache: dict = {}

    def _get_tdms_file(self) -> TdmsFile:
        """Lazy load TDMS file."""
        if self._tdms_file is None:
            self._tdms_file = TdmsFile.read(self.path)
        return self._tdms_file

    def _find_channel_data(self, tdms_file: TdmsFile, standard_name: str):
        """Find channel data by standard name or aliases."""
        if standard_name in self._channel_cache:
            return self._channel_cache[standard_name]

        aliases = self.CHANNEL_ALIASES.get(standard_name, [standard_name])

        for group in tdms_file.groups():
            for channel in group.channels():
                ch_name_lower = channel.name.lower().replace(" ", "-")
                for alias in aliases:
                    if alias.lower() in ch_name_lower or ch_name_lower in alias.lower():
                        data = channel[:]
                        self._channel_cache[standard_name] = data
                        return data

        return None

    def _convert_timestamp(self, ts_value) -> datetime:
        """Convert various timestamp formats to datetime."""
        if isinstance(ts_value, np.datetime64):
            # numpy datetime64 to python datetime
            return ts_value.astype("datetime64[us]").astype(datetime)
        elif isinstance(ts_value, datetime):
            return ts_value
        elif isinstance(ts_value, str):
            return self._parse_timestamp_str(ts_value)
        else:
            return datetime.now(timezone.utc)

    def _parse_timestamp_str(self, time_str: str) -> datetime:
        """Parse timestamp from TDMS time string format."""
        try:
            parts = str(time_str).strip().split(" ")
            if len(parts) >= 2:
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
        return datetime.now(timezone.utc)

    def parse(self) -> Iterator[MonitoringRecord]:
        """Parse TDMS file and yield MonitoringRecord objects."""
        tdms_file = self._get_tdms_file()

        # Get main CNC group record count (shorter than DAQ data)
        record_count = 0
        for group in tdms_file.groups():
            if group.name.upper() == "CNC":
                for channel in group.channels():
                    ch_len = len(channel[:])
                    if ch_len > 0 and (record_count == 0 or ch_len < record_count):
                        record_count = ch_len
                break

        if record_count == 0:
            # Fallback to any group
            for group in tdms_file.groups():
                for channel in group.channels():
                    ch_len = len(channel[:])
                    if ch_len > 0:
                        record_count = ch_len
                        break
                if record_count > 0:
                    break

        # Pre-fetch channel data
        time_data = self._find_channel_data(tdms_file, "time")
        crpm_data = self._find_channel_data(tdms_file, "crpm")
        ccrpm_data = self._find_channel_data(tdms_file, "ccrpm")
        cfr_data = self._find_channel_data(tdms_file, "cfr")
        ccfr_data = self._find_channel_data(tdms_file, "ccfr")
        cpx_data = self._find_channel_data(tdms_file, "cpx")
        cpy_data = self._find_channel_data(tdms_file, "cpy")
        cpz_data = self._find_channel_data(tdms_file, "cpz")
        cmdl_data = self._find_channel_data(tdms_file, "cmdl")
        ct_data = self._find_channel_data(tdms_file, "ct")
        cpn_data = self._find_channel_data(tdms_file, "cpn")
        asprms_data = self._find_channel_data(tdms_file, "asprms")
        aaccrms_data = self._find_channel_data(tdms_file, "aaccrms")
        cut_data = self._find_channel_data(tdms_file, "cut")
        estwear_data = self._find_channel_data(tdms_file, "estwear")
        estforce_data = self._find_channel_data(tdms_file, "estforce")
        ctime_data = self._find_channel_data(tdms_file, "ctime")

        # Determine base time
        base_time = datetime.now(timezone.utc)
        if time_data is not None and len(time_data) > 0:
            base_time = self._convert_timestamp(time_data[0])

        def get_val(data, idx, default=0.0):
            if data is not None and idx < len(data):
                val = data[idx]
                if isinstance(val, (int, float, np.integer, np.floating)):
                    return float(val)
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return default
            return default

        def get_str(data, idx, default="") -> str:
            if data is not None and idx < len(data):
                val = data[idx]
                return str(val) if val is not None else default
            return default

        # Yield records
        for i in range(record_count):
            try:
                # Parse timestamp
                if time_data is not None and i < len(time_data):
                    timestamp = self._convert_timestamp(time_data[i])
                elif ctime_data is not None and i < len(ctime_data):
                    elapsed = float(ctime_data[i])
                    timestamp = base_time + timedelta(seconds=elapsed)
                else:
                    timestamp = base_time + timedelta(milliseconds=i * 100)

                position = (
                    get_val(cpx_data, i, 0.0),
                    get_val(cpy_data, i, 0.0),
                    get_val(cpz_data, i, 0.0),
                )

                yield MonitoringRecord(
                    timestamp=timestamp,
                    spindle_rpm=get_val(crpm_data, i, 0.0),
                    cmd_spindle_rpm=get_val(ccrpm_data, i, 0.0),
                    feedrate=get_val(cfr_data, i, 0.0),
                    cmd_feedrate=get_val(ccfr_data, i, 0.0),
                    position=position,
                    gcode_cmd=get_str(cmdl_data, i, ""),
                    vibration_rms=get_val(asprms_data, i, 0.0),
                    accel_rms=get_val(aaccrms_data, i, 0.0),
                    cutting=bool(int(get_val(cut_data, i, 0))),
                    estimated_wear=get_val(estwear_data, i, 0.0),
                    estimated_force=get_val(estforce_data, i, 0.0),
                    elapsed_time=get_val(ctime_data, i, 0.0),
                    program_name=get_str(cpn_data, i, ""),
                    tool_number=int(get_val(ct_data, i, 0)),
                )
            except Exception:
                continue  # Skip malformed records

    def get_channels(self) -> list[str]:
        """Get list of channel names in the TDMS file."""
        if self._channels is None:
            tdms_file = self._get_tdms_file()
            self._channels = []
            for group in tdms_file.groups():
                for channel in group.channels():
                    self._channels.append(f"{group.name}/{channel.name}")
        return self._channels

    def get_record_count(self) -> int:
        """Get total number of records (from CNC group, not DAQ)."""
        if self._record_count is None:
            tdms_file = self._get_tdms_file()
            # Prefer CNC group length
            for group in tdms_file.groups():
                if group.name.upper() == "CNC":
                    for channel in group.channels():
                        ch_len = len(channel[:])
                        if ch_len > 0:
                            self._record_count = ch_len
                            break
                    break

            if self._record_count is None:
                # Fallback
                max_len = 0
                for group in tdms_file.groups():
                    for channel in group.channels():
                        ch_len = len(channel[:])
                        if ch_len > max_len:
                            max_len = ch_len
                self._record_count = max_len

        return self._record_count

    def get_time_range(self) -> tuple[datetime, datetime]:
        """Get start and end timestamps from the file."""
        if self._time_range is None:
            first_ts = None
            last_ts = None

            for record in self.parse():
                if first_ts is None:
                    first_ts = record.timestamp
                last_ts = record.timestamp

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
            "format": "TDMS",
            "channels": self.get_channels(),
            "record_count": self.get_record_count(),
            "start_time": time_range[0].isoformat(),
            "end_time": time_range[1].isoformat(),
            "duration_seconds": (time_range[1] - time_range[0]).total_seconds(),
            "file_size_bytes": self.path.stat().st_size,
        }
