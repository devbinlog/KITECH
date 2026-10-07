"""Speed controller for replay timing."""

import asyncio
from datetime import datetime
from typing import Optional


class SpeedController:
    """Controls replay speed and timing."""

    def __init__(self, speed: float = 1.0):
        """
        Initialize speed controller.

        Args:
            speed: Playback speed multiplier (1.0 = real-time, 2.0 = 2x speed)
        """
        self._speed = max(0.01, speed)  # Minimum 0.01x speed
        self._paused = False
        self._stopped = False
        self._last_timestamp: Optional[datetime] = None
        self._last_real_time: Optional[float] = None

    @property
    def speed(self) -> float:
        """Get current playback speed."""
        return self._speed

    @speed.setter
    def speed(self, value: float) -> None:
        """Set playback speed."""
        self._speed = max(0.01, value)

    @property
    def is_paused(self) -> bool:
        """Check if playback is paused."""
        return self._paused

    @property
    def is_stopped(self) -> bool:
        """Check if playback is stopped."""
        return self._stopped

    def pause(self) -> None:
        """Pause playback."""
        self._paused = True

    def resume(self) -> None:
        """Resume playback."""
        self._paused = False
        # Reset timing to avoid large jumps after resume
        self._last_timestamp = None
        self._last_real_time = None

    def stop(self) -> None:
        """Stop playback."""
        self._stopped = True
        self._paused = False

    def reset(self) -> None:
        """Reset controller state."""
        self._paused = False
        self._stopped = False
        self._last_timestamp = None
        self._last_real_time = None

    async def wait_for_timestamp(self, timestamp: datetime) -> bool:
        """
        Wait until the appropriate time to emit a record.

        Args:
            timestamp: The timestamp of the record to emit

        Returns:
            True if should continue, False if stopped
        """
        if self._stopped:
            return False

        # Wait while paused
        while self._paused and not self._stopped:
            await asyncio.sleep(0.1)

        if self._stopped:
            return False

        current_time = asyncio.get_event_loop().time()

        # First record - initialize timing
        if self._last_timestamp is None:
            self._last_timestamp = timestamp
            self._last_real_time = current_time
            return True

        # Calculate delay based on timestamp difference
        data_delta = (timestamp - self._last_timestamp).total_seconds()
        if data_delta < 0:
            data_delta = 0

        # Adjust for playback speed
        real_delay = data_delta / self._speed

        # Calculate when we should emit this record
        expected_time = self._last_real_time + real_delay
        wait_time = expected_time - current_time

        if wait_time > 0:
            # Clamp wait time to avoid extremely long waits
            wait_time = min(wait_time, 10.0)  # Max 10 second wait
            await asyncio.sleep(wait_time)

        # Check if stopped during wait
        if self._stopped:
            return False

        # Update tracking
        self._last_timestamp = timestamp
        self._last_real_time = asyncio.get_event_loop().time()

        return True

    def calculate_remaining_time(
        self, current_timestamp: datetime, end_timestamp: datetime
    ) -> float:
        """
        Calculate remaining playback time in seconds.

        Args:
            current_timestamp: Current position timestamp
            end_timestamp: End timestamp

        Returns:
            Estimated remaining time in seconds (adjusted for speed)
        """
        data_remaining = (end_timestamp - current_timestamp).total_seconds()
        return data_remaining / self._speed if data_remaining > 0 else 0
