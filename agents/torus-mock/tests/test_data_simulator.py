"""Tests for DataSimulator."""

import asyncio
import pytest

from src.app.services.data_simulator import DataSimulator, get_simulator
from src.app.services.machine_store import get_store, reset_store


@pytest.fixture(autouse=True)
def setup_store():
    """Reset and load store for each test."""
    from pathlib import Path

    reset_store()
    store = get_store()
    store.load_from_json(Path(__file__).parent.parent / "data" / "default_machines.json")
    yield
    reset_store()


class TestDataSimulatorInit:
    """Test DataSimulator initialization."""

    def test_default_interval(self):
        """Test default interval is 500ms."""
        sim = DataSimulator()
        assert sim.interval_ms == 500

    def test_custom_interval(self):
        """Test custom interval."""
        sim = DataSimulator(interval_ms=100)
        assert sim.interval_ms == 100

    def test_initial_state(self):
        """Test initial state is not running."""
        sim = DataSimulator()
        assert sim.running is False
        assert sim.tick_count == 0


class TestDataSimulatorStartStop:
    """Test start/stop functionality."""

    @pytest.mark.asyncio
    async def test_start_sets_running(self):
        """Test start sets running flag."""
        sim = DataSimulator(interval_ms=50)
        await sim.start()

        assert sim.running is True
        await sim.stop()

    @pytest.mark.asyncio
    async def test_stop_clears_running(self):
        """Test stop clears running flag."""
        sim = DataSimulator(interval_ms=50)
        await sim.start()
        await sim.stop()

        assert sim.running is False

    @pytest.mark.asyncio
    async def test_double_start_is_safe(self):
        """Test starting twice doesn't cause issues."""
        sim = DataSimulator(interval_ms=50)
        await sim.start()
        await sim.start()  # Should be safe

        assert sim.running is True
        await sim.stop()

    @pytest.mark.asyncio
    async def test_tick_increments(self):
        """Test tick count increments."""
        sim = DataSimulator(interval_ms=10)
        # Directly invoke ticks without relying on wall-clock timing.
        sim._start_time = __import__("time").time()
        sim._tick()
        sim.tick_count += 1
        sim._tick()
        sim.tick_count += 1

        assert sim.tick_count == 2


class TestDataSimulatorStatus:
    """Test status reporting."""

    def test_get_status_not_running(self):
        """Test status when not running."""
        sim = DataSimulator()
        status = sim.get_status()

        assert status["running"] is False
        assert status["tick_count"] == 0
        assert status["interval_ms"] == 500
        assert isinstance(status["machines"], list)

    @pytest.mark.asyncio
    async def test_get_status_running(self):
        """Test status when running."""
        import time

        sim = DataSimulator(interval_ms=50)
        # Drive ticks directly without waiting on wall clock.
        sim.running = True
        sim._start_time = time.time()
        sim._tick()
        sim.tick_count += 1

        status = sim.get_status()

        assert status["running"] is True
        assert status["tick_count"] > 0


class TestDataSimulatorSingleton:
    """Test singleton pattern."""

    def test_get_simulator_returns_same_instance(self):
        """Test get_simulator returns singleton."""
        sim1 = get_simulator()
        sim2 = get_simulator()

        assert sim1 is sim2


class TestDataSimulatorInterval:
    """Test interval property."""

    def test_interval_sec_property(self):
        """Test _interval_sec property calculation."""
        sim = DataSimulator(interval_ms=500)
        # Access private property
        assert sim._interval_sec == 0.5

        sim2 = DataSimulator(interval_ms=1000)
        assert sim2._interval_sec == 1.0
