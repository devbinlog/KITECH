"""Replayer engine for monitoring data files."""

from datetime import datetime
from pathlib import Path
from typing import AsyncIterator, Optional, Callable, Awaitable

from ..models.monitoring_data import MonitoringRecord
from ..parsers.log_parser import LogParser
from ..parsers.tdms_parser import TDMSParser
from .speed_controller import SpeedController


class MonitoringReplayer:
    """
    Replays monitoring data from TDMS or LOG files.

    Supports:
    - Variable playback speed
    - Time range filtering
    - Pause/resume/stop controls
    - Async iteration
    """

    def __init__(self):
        """Initialize replayer."""
        self._speed_controller: Optional[SpeedController] = None
        self._current_path: Optional[Path] = None
        self._records_emitted: int = 0
        self._is_replaying: bool = False

    def _get_parser(self, path: Path):
        """Get appropriate parser for file type."""
        suffix = path.suffix.lower()
        if suffix == ".tdms":
            return TDMSParser(path)
        elif suffix in (".log", ".tsv", ".txt"):
            return LogParser(path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

    async def replay(
        self,
        path: str | Path,
        speed: float = 1.0,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        on_record: Optional[Callable[[MonitoringRecord], Awaitable[None]]] = None,
    ) -> AsyncIterator[MonitoringRecord]:
        """
        Replay monitoring data from file.

        Args:
            path: Path to TDMS or LOG file
            speed: Playback speed multiplier (1.0 = real-time)
            start_time: Optional start time filter
            end_time: Optional end time filter
            on_record: Optional callback for each record

        Yields:
            MonitoringRecord objects at appropriate timing
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        self._current_path = path
        self._speed_controller = SpeedController(speed)
        self._records_emitted = 0
        self._is_replaying = True

        try:
            parser = self._get_parser(path)

            for record in parser.parse():
                # Check stop condition
                if self._speed_controller.is_stopped:
                    break

                # Apply time filters
                if start_time and record.timestamp < start_time:
                    continue
                if end_time and record.timestamp > end_time:
                    break

                # Wait for appropriate time
                should_continue = await self._speed_controller.wait_for_timestamp(record.timestamp)
                if not should_continue:
                    break

                self._records_emitted += 1

                # Call callback if provided
                if on_record:
                    await on_record(record)

                yield record

        finally:
            self._is_replaying = False

    def stop(self) -> None:
        """Stop replay."""
        if self._speed_controller:
            self._speed_controller.stop()

    def pause(self) -> None:
        """Pause replay."""
        if self._speed_controller:
            self._speed_controller.pause()

    def resume(self) -> None:
        """Resume replay."""
        if self._speed_controller:
            self._speed_controller.resume()

    def set_speed(self, speed: float) -> None:
        """Change playback speed during replay."""
        if self._speed_controller:
            self._speed_controller.speed = speed

    @property
    def is_paused(self) -> bool:
        """Check if replay is paused."""
        return self._speed_controller.is_paused if self._speed_controller else False

    @property
    def is_replaying(self) -> bool:
        """Check if replay is in progress."""
        return self._is_replaying

    @property
    def records_emitted(self) -> int:
        """Get number of records emitted so far."""
        return self._records_emitted

    @property
    def current_speed(self) -> float:
        """Get current playback speed."""
        return self._speed_controller.speed if self._speed_controller else 1.0
