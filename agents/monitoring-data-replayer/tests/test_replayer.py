"""Tests for replay engine."""

import pytest
import asyncio
from pathlib import Path
from datetime import datetime, timedelta, timezone

from src.replay.replayer import MonitoringReplayer
from src.replay.speed_controller import SpeedController
from src.models.monitoring_data import MonitoringRecord

# Sample data path
SAMPLES_DIR = (
    Path(__file__).parent.parent.parent.parent
    / "samples"
    / "digital-thread-project-manager"
    / "tdms"
)


class TestSpeedController:
    """Test cases for SpeedController."""

    def test_initial_state(self):
        """Test initial controller state."""
        controller = SpeedController(speed=2.0)

        assert controller.speed == 2.0
        assert not controller.is_paused
        assert not controller.is_stopped

    def test_pause_resume(self):
        """Test pause and resume."""
        controller = SpeedController()

        controller.pause()
        assert controller.is_paused

        controller.resume()
        assert not controller.is_paused

    def test_stop(self):
        """Test stop."""
        controller = SpeedController()

        controller.stop()
        assert controller.is_stopped

    def test_speed_limits(self):
        """Test speed is limited to minimum."""
        controller = SpeedController(speed=0.001)

        # Should be clamped to minimum
        assert controller.speed >= 0.01

        controller.speed = -1.0
        assert controller.speed >= 0.01

    @pytest.mark.asyncio
    async def test_wait_for_timestamp_first_record(self):
        """Test waiting for first timestamp."""
        controller = SpeedController(speed=1.0)

        ts = datetime.now(timezone.utc)
        result = await controller.wait_for_timestamp(ts)

        assert result is True

    @pytest.mark.asyncio
    async def test_wait_for_timestamp_stopped(self):
        """Test that stopped controller returns False."""
        controller = SpeedController()
        controller.stop()

        result = await controller.wait_for_timestamp(datetime.now(timezone.utc))

        assert result is False

    @pytest.mark.asyncio
    async def test_wait_timing_at_speed(self):
        """Test that timing scales with speed."""
        controller = SpeedController(speed=10.0)  # 10x speed

        ts1 = datetime.now(timezone.utc)
        await controller.wait_for_timestamp(ts1)

        # Second timestamp 1 second later in data
        ts2 = ts1 + timedelta(seconds=1.0)

        start = asyncio.get_event_loop().time()
        await controller.wait_for_timestamp(ts2)
        elapsed = asyncio.get_event_loop().time() - start

        # At 10x speed, 1s of data should take ~0.1s real time
        assert elapsed < 0.2  # Some tolerance

    def test_calculate_remaining_time(self):
        """Test remaining time calculation."""
        controller = SpeedController(speed=2.0)

        current = datetime.now(timezone.utc)
        end = current + timedelta(seconds=100)

        remaining = controller.calculate_remaining_time(current, end)

        # At 2x speed, 100s of data = 50s real time
        assert remaining == pytest.approx(50.0, rel=0.01)


class TestMonitoringReplayer:
    """Test cases for MonitoringReplayer."""

    @pytest.fixture
    def sample_log_path(self) -> Path:
        """Get path to sample LOG file."""
        return SAMPLES_DIR / "sample.log"

    @pytest.fixture
    def replayer(self) -> MonitoringReplayer:
        """Create replayer instance."""
        return MonitoringReplayer()

    def test_initial_state(self, replayer: MonitoringReplayer):
        """Test initial replayer state."""
        assert not replayer.is_replaying
        assert not replayer.is_paused
        assert replayer.records_emitted == 0

    @pytest.mark.asyncio
    async def test_replay_log_file(self, replayer: MonitoringReplayer, sample_log_path: Path):
        """Test replaying LOG file."""
        if not sample_log_path.exists():
            pytest.skip(f"Sample file not found: {sample_log_path}")

        records = []
        count = 0

        async for record in replayer.replay(sample_log_path, speed=1000.0):  # Very fast
            records.append(record)
            count += 1
            if count >= 50:
                replayer.stop()
                break

        assert len(records) > 0
        assert all(isinstance(r, MonitoringRecord) for r in records)
        print(f"Replayed {len(records)} records")

    @pytest.mark.asyncio
    async def test_replay_with_time_filter(
        self, replayer: MonitoringReplayer, sample_log_path: Path
    ):
        """Test replay with time range filter."""
        if not sample_log_path.exists():
            pytest.skip(f"Sample file not found: {sample_log_path}")

        # Get time range from file
        from src.parsers.log_parser import LogParser

        parser = LogParser(sample_log_path)
        start_time, end_time = parser.get_time_range()

        # Filter to first 10 seconds
        filter_end = start_time + timedelta(seconds=10)

        records = []
        async for record in replayer.replay(
            sample_log_path,
            speed=1000.0,
            start_time=start_time,
            end_time=filter_end,
        ):
            records.append(record)

        assert len(records) > 0
        # All records should be within time range
        for r in records:
            assert r.timestamp >= start_time
            assert r.timestamp <= filter_end

        print(f"Filtered replay: {len(records)} records in 10s window")

    @pytest.mark.asyncio
    async def test_stop_during_replay(self, replayer: MonitoringReplayer, sample_log_path: Path):
        """Test stopping replay mid-stream."""
        if not sample_log_path.exists():
            pytest.skip(f"Sample file not found: {sample_log_path}")

        count = 0
        async for record in replayer.replay(sample_log_path, speed=1000.0):
            count += 1
            if count == 25:
                replayer.stop()

        # Should stop at or around 25 records
        assert count >= 25
        assert count < 50  # Should not continue much further

    @pytest.mark.asyncio
    async def test_callback_on_record(self, replayer: MonitoringReplayer, sample_log_path: Path):
        """Test callback function during replay."""
        if not sample_log_path.exists():
            pytest.skip(f"Sample file not found: {sample_log_path}")

        callback_records = []

        async def on_record(record: MonitoringRecord):
            callback_records.append(record)

        count = 0
        async for record in replayer.replay(
            sample_log_path,
            speed=1000.0,
            on_record=on_record,
        ):
            count += 1
            if count >= 20:
                replayer.stop()
                break

        # Callback should have been called for each record
        assert len(callback_records) >= 20


class TestReplayerIntegration:
    """Integration tests for replayer."""

    @pytest.fixture
    def sample_log_path(self) -> Path:
        return SAMPLES_DIR / "sample.log"

    @pytest.mark.asyncio
    async def test_full_replay_small(self, sample_log_path: Path):
        """Test replaying a small portion of data."""
        if not sample_log_path.exists():
            pytest.skip(f"Sample file not found: {sample_log_path}")

        replayer = MonitoringReplayer()

        # Replay first 100 records at max speed
        records = []
        async for record in replayer.replay(sample_log_path, speed=10000.0):
            records.append(record)
            if len(records) >= 100:
                replayer.stop()
                break

        assert len(records) >= 100

        # Check timing consistency
        timestamps = [r.timestamp for r in records]
        for i in range(1, len(timestamps)):
            # Timestamps should be non-decreasing
            assert timestamps[i] >= timestamps[i - 1], f"Timestamp went backwards at index {i}"

        print(f"Replay integrity check passed: {len(records)} records")
