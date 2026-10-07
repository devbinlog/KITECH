"""Main agent for monitoring data replay."""

from datetime import datetime
from pathlib import Path
from typing import Optional, AsyncIterator
import statistics

from .models.monitoring_data import MonitoringRecord
from .parsers.log_parser import LogParser
from .parsers.tdms_parser import TDMSParser
from .replay.replayer import MonitoringReplayer
from .outputs.websocket_output import WebSocketOutput
from .outputs.file_output import FileOutput


class MonitoringDataReplayerAgent:
    """
    Agent for replaying CNC monitoring data from TDMS and LOG files.

    Features:
    - List and inspect monitoring data files
    - Replay data at various speeds
    - Stream to WebSocket clients
    - Save to CSV/JSON files
    - Calculate statistics
    """

    def __init__(self):
        """Initialize agent."""
        self._replayer = MonitoringReplayer()
        self._websocket_output: Optional[WebSocketOutput] = None
        self._file_output: Optional[FileOutput] = None

    def _get_parser(self, path: Path):
        """Get appropriate parser for file type."""
        suffix = path.suffix.lower()
        if suffix == ".tdms":
            return TDMSParser(path)
        elif suffix in (".log", ".tsv", ".txt"):
            return LogParser(path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

    def list_files(self, directory: str) -> list[dict]:
        """
        List monitoring data files in a directory.

        Args:
            directory: Path to directory to scan

        Returns:
            List of file info dictionaries
        """
        dir_path = Path(directory).expanduser()
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        files = []
        for pattern in ["*.tdms", "*.log", "*.tsv"]:
            for file_path in dir_path.glob(pattern):
                files.append(
                    {
                        "path": str(file_path),
                        "name": file_path.name,
                        "format": file_path.suffix[1:].upper(),
                        "size_bytes": file_path.stat().st_size,
                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                    }
                )

        return sorted(files, key=lambda x: x["name"])

    def get_file_info(self, path: str) -> dict:
        """
        Get detailed information about a monitoring data file.

        Args:
            path: Path to the file

        Returns:
            File metadata including channels, record count, time range
        """
        file_path = Path(path).expanduser()
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        parser = self._get_parser(file_path)
        return parser.get_file_info()

    async def replay(
        self,
        path: str,
        speed: float = 1.0,
        output: Optional[str] = None,  # "websocket", "csv", "json", or file path
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        websocket_port: int = 8765,
    ) -> AsyncIterator[MonitoringRecord]:
        """
        Replay monitoring data from file.

        Args:
            path: Path to TDMS or LOG file
            speed: Playback speed multiplier (1.0 = real-time)
            output: Output destination ("websocket", "csv", "json", or file path)
            start_time: Optional start time filter
            end_time: Optional end time filter
            websocket_port: Port for WebSocket server (if output="websocket")

        Yields:
            MonitoringRecord objects at appropriate timing
        """
        file_path = Path(path).expanduser()

        # Setup output handler
        if output == "websocket":
            self._websocket_output = WebSocketOutput(port=websocket_port)
            await self._websocket_output.start()

            async def on_record(record: MonitoringRecord):
                await self._websocket_output.broadcast(record)

        elif output in ("csv", "json"):
            output_path = file_path.with_suffix(f".output.{output}")
            self._file_output = FileOutput(output_path, format=output)
            await self._file_output.open()

            async def on_record(record: MonitoringRecord):
                await self._file_output.write(record)

        elif output and Path(output).suffix:
            # Custom file path
            output_path = Path(output).expanduser()
            fmt = output_path.suffix[1:].lower()
            if fmt not in ("csv", "json"):
                fmt = "csv"
            self._file_output = FileOutput(output_path, format=fmt)
            await self._file_output.open()

            async def on_record(record: MonitoringRecord):
                await self._file_output.write(record)
        else:
            on_record = None

        try:
            async for record in self._replayer.replay(
                file_path,
                speed=speed,
                start_time=start_time,
                end_time=end_time,
                on_record=on_record,
            ):
                yield record
        finally:
            # Cleanup outputs
            if self._websocket_output:
                await self._websocket_output.stop()
                self._websocket_output = None
            if self._file_output:
                await self._file_output.close()
                self._file_output = None

    def stop(self) -> None:
        """Stop current replay."""
        self._replayer.stop()

    def pause(self) -> None:
        """Pause current replay."""
        self._replayer.pause()

    def resume(self) -> None:
        """Resume paused replay."""
        self._replayer.resume()

    def set_speed(self, speed: float) -> None:
        """Change playback speed during replay."""
        self._replayer.set_speed(speed)

    @property
    def is_replaying(self) -> bool:
        """Check if replay is in progress."""
        return self._replayer.is_replaying

    @property
    def is_paused(self) -> bool:
        """Check if replay is paused."""
        return self._replayer.is_paused

    def get_statistics(self, path: str) -> dict:
        """
        Calculate statistics for a monitoring data file.

        Args:
            path: Path to the file

        Returns:
            Statistics including min/max/avg for key metrics
        """
        file_path = Path(path).expanduser()
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        parser = self._get_parser(file_path)

        # Collect data
        spindle_rpms = []
        feedrates = []
        vibration_rms = []
        accel_rms = []
        cutting_records = 0
        total_records = 0

        for record in parser.parse():
            total_records += 1
            spindle_rpms.append(record.spindle_rpm)
            feedrates.append(record.feedrate)
            vibration_rms.append(record.vibration_rms)
            accel_rms.append(record.accel_rms)
            if record.cutting:
                cutting_records += 1

        def calc_stats(values: list[float]) -> dict:
            if not values:
                return {"min": 0, "max": 0, "avg": 0, "stdev": 0}
            return {
                "min": min(values),
                "max": max(values),
                "avg": statistics.mean(values),
                "stdev": statistics.stdev(values) if len(values) > 1 else 0,
            }

        file_info = parser.get_file_info()

        return {
            "file_info": file_info,
            "total_records": total_records,
            "cutting_records": cutting_records,
            "cutting_ratio": cutting_records / total_records if total_records > 0 else 0,
            "spindle_rpm": calc_stats(spindle_rpms),
            "feedrate": calc_stats(feedrates),
            "vibration_rms": calc_stats(vibration_rms),
            "accel_rms": calc_stats(accel_rms),
        }

    def get_status(self) -> dict:
        """Get current agent status."""
        status = {
            "is_replaying": self._replayer.is_replaying,
            "is_paused": self._replayer.is_paused,
            "records_emitted": self._replayer.records_emitted,
            "current_speed": self._replayer.current_speed,
        }

        if self._websocket_output:
            status["websocket"] = self._websocket_output.get_statistics()
        if self._file_output:
            status["file_output"] = self._file_output.get_statistics()

        return status
