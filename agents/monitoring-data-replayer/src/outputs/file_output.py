"""File output handler for saving monitoring data."""

import json
from pathlib import Path

import aiofiles

from ..models.monitoring_data import MonitoringRecord


class FileOutput:
    """Saves monitoring records to CSV or JSON files."""

    def __init__(
        self,
        output_path: str | Path,
        format: str = "csv",  # "csv" or "json"
        append: bool = False,
    ):
        """
        Initialize file output handler.

        Args:
            output_path: Path to output file
            format: Output format ("csv" or "json")
            append: Whether to append to existing file
        """
        self.output_path = Path(output_path)
        self.format = format.lower()
        self.append = append
        self._records_written = 0
        self._file_handle = None
        self._csv_writer = None
        self._header_written = False
        self._json_records: list[dict] = []

    async def __aenter__(self):
        """Async context manager entry."""
        await self.open()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def open(self) -> None:
        """Open output file for writing."""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        if self.format == "csv":
            mode = "a" if self.append else "w"
            self._file_handle = await aiofiles.open(self.output_path, mode=mode, newline="")
            # Check if header needs to be written
            if not self.append or self.output_path.stat().st_size == 0:
                self._header_written = False
            else:
                self._header_written = True
        elif self.format == "json":
            self._json_records = []
            if self.append and self.output_path.exists():
                async with aiofiles.open(self.output_path, "r") as f:
                    content = await f.read()
                    if content.strip():
                        self._json_records = json.loads(content)

    async def write(self, record: MonitoringRecord) -> None:
        """
        Write a single record to the output file.

        Args:
            record: MonitoringRecord to write
        """
        if self.format == "csv":
            await self._write_csv(record)
        elif self.format == "json":
            self._json_records.append(record.to_dict())

        self._records_written += 1

    async def _write_csv(self, record: MonitoringRecord) -> None:
        """Write record as CSV row."""
        if self._file_handle is None:
            raise RuntimeError("File not opened. Call open() first.")

        # Prepare row data
        row = {
            "timestamp": record.timestamp.isoformat(),
            "spindle_rpm": record.spindle_rpm,
            "cmd_spindle_rpm": record.cmd_spindle_rpm,
            "feedrate": record.feedrate,
            "cmd_feedrate": record.cmd_feedrate,
            "pos_x": record.position[0],
            "pos_y": record.position[1],
            "pos_z": record.position[2],
            "gcode_cmd": record.gcode_cmd,
            "vibration_rms": record.vibration_rms,
            "accel_rms": record.accel_rms,
            "cutting": int(record.cutting),
            "estimated_wear": record.estimated_wear,
            "estimated_force": record.estimated_force,
            "elapsed_time": record.elapsed_time,
            "program_name": record.program_name,
            "tool_number": record.tool_number,
        }

        # Write header if needed
        if not self._header_written:
            header_line = ",".join(row.keys()) + "\n"
            await self._file_handle.write(header_line)
            self._header_written = True

        # Write row
        values = [str(v) for v in row.values()]
        row_line = ",".join(values) + "\n"
        await self._file_handle.write(row_line)

    async def close(self) -> None:
        """Close output file and flush remaining data."""
        if self.format == "csv":
            if self._file_handle:
                await self._file_handle.close()
                self._file_handle = None
        elif self.format == "json":
            async with aiofiles.open(self.output_path, "w") as f:
                await f.write(json.dumps(self._json_records, indent=2))
            self._json_records = []

    @property
    def records_written(self) -> int:
        """Get number of records written."""
        return self._records_written

    def get_statistics(self) -> dict:
        """Get output statistics."""
        return {
            "output_path": str(self.output_path),
            "format": self.format,
            "records_written": self._records_written,
            "file_exists": self.output_path.exists(),
            "file_size_bytes": self.output_path.stat().st_size if self.output_path.exists() else 0,
        }
