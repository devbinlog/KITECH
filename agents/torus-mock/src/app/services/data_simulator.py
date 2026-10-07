"""Data Simulator — periodic updates to simulate CNC operation.

Runs as an asyncio background task, updating machine data
at configurable intervals to simulate real CNC behavior.
"""

from __future__ import annotations

import asyncio
import math
import random
import time
from datetime import datetime, timezone
from typing import Optional

from ..schemas import Alarm
from .machine_store import get_store


class DataSimulator:
    """Simulates CNC machine data changes."""

    def __init__(self, interval_ms: int = 500) -> None:
        self.interval_ms = interval_ms
        self.running = False
        self.tick_count = 0
        self._task: Optional[asyncio.Task] = None
        self._start_time = 0.0

    async def start(self) -> None:
        """Start the simulation loop."""
        if self.running:
            return
        self.running = True
        self.tick_count = 0
        self._start_time = time.time()
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        """Stop the simulation loop."""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _run(self) -> None:
        """Main simulation loop."""
        interval = self.interval_ms / 1000.0
        while self.running:
            try:
                self._tick()
                self.tick_count += 1
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception:
                # Don't crash the simulator on errors
                await asyncio.sleep(interval)

    def _tick(self) -> None:
        """Single simulation tick — update all machines."""
        store = get_store()
        elapsed = time.time() - self._start_time
        t = self.tick_count

        for machine_id, machine in store.machines.items():
            for ch_idx, channel in enumerate(machine.channel):
                self._update_axes(channel, t, elapsed)
                self._update_spindles(channel, t, elapsed)
                self._update_feed(channel, t)
                self._update_work_status(channel, t)
                self._update_program(channel, t)
                self._maybe_trigger_alarm(channel, t)

    def _update_axes(self, channel, t: int, elapsed: float) -> None:
        """Update axis positions with sinusoidal patterns."""
        for i, axis in enumerate(channel.axis):
            if not axis.axisEnabled:
                continue

            # Sinusoidal motion pattern with different phases per axis
            phase = i * math.pi / 3
            amplitude = 50.0 + i * 20.0

            # Machine position follows a sin pattern
            axis.machinePosition = round(amplitude * math.sin(elapsed * 0.5 + phase), 3)
            axis.workPosition = round(axis.machinePosition + axis.machineOrigin, 3)
            axis.distanceToGo = round(amplitude * abs(math.cos(elapsed * 0.5 + phase)) * 0.1, 3)

            # Feed rate per axis
            axis.axisFeed = round(abs(math.cos(elapsed * 0.5 + phase)) * 1000.0, 1)

            # Load simulation (higher during cutting)
            base_load = 10.0 + random.uniform(-2, 2)
            cutting_load = 30.0 * abs(math.sin(elapsed * 0.3))
            axis.axisLoad = round(base_load + cutting_load, 1)

            # Current
            axis.axisCurrent = round(axis.axisLoad * 0.1, 2)

            # Temperature: slowly rises then stabilizes
            target_temp = 28.0 + axis.axisLoad * 0.05
            axis.axisTemperature = round(
                axis.axisTemperature + (target_temp - axis.axisTemperature) * 0.01,
                1,
            )

            # Power
            axis.axisPower.actualPowerConsumption = round(axis.axisLoad * 0.05, 2)
            axis.axisPower.powerConsumption = round(axis.axisPower.actualPowerConsumption * 1.1, 2)

    def _update_spindles(self, channel, t: int, elapsed: float) -> None:
        """Update spindle speeds and loads."""
        for spindle in channel.spindle:
            if not spindle.spindleEnabled:
                continue

            # Simulate speed: idle → ramp up → cutting → ramp down
            cycle_pos = (elapsed % 30.0) / 30.0  # 30-second cycle
            if cycle_pos < 0.1:
                # Ramp up
                speed_factor = cycle_pos / 0.1
            elif cycle_pos < 0.8:
                # Cutting
                speed_factor = 1.0
            elif cycle_pos < 0.9:
                # Ramp down
                speed_factor = (0.9 - cycle_pos) / 0.1
            else:
                # Idle
                speed_factor = 0.0

            target_speed = spindle.spindleLimit * 0.6 * speed_factor
            spindle.rpm.commandedSpeed = round(target_speed, 0)
            spindle.rpm.actualSpeed = round(target_speed * (1.0 + random.uniform(-0.02, 0.02)), 0)

            # Load follows speed
            spindle.spindleLoad = round(speed_factor * 60.0 + random.uniform(-3, 3), 1)
            spindle.spindleCurrent = round(spindle.spindleLoad * 0.15, 2)

            # Temperature
            target_temp = 25.0 + spindle.spindleLoad * 0.1
            spindle.spindleTemperature = round(
                spindle.spindleTemperature + (target_temp - spindle.spindleTemperature) * 0.005,
                1,
            )

            # Power
            spindle.spindlePower.actualPowerConsumption = round(spindle.spindleLoad * 0.08, 2)

    def _update_feed(self, channel, t: int) -> None:
        """Update feed rate."""
        channel.feed.feedRate.commandedSpeed = round(500.0 + 300.0 * math.sin(t * 0.1), 1)
        channel.feed.feedRate.actualSpeed = round(
            channel.feed.feedRate.commandedSpeed
            * (channel.feed.feedOverride / 100.0)
            * (1.0 + random.uniform(-0.01, 0.01)),
            1,
        )

    def _update_work_status(self, channel, t: int) -> None:
        """Update work counters and machining time."""
        for ws in channel.workStatus:
            # Machining time accumulates
            ws.machiningTime.processingMachiningTime += self._interval_sec
            ws.machiningTime.machineOperationTime += self._interval_sec
            ws.machiningTime.actualCuttingTime += self._interval_sec * 0.7

            # Work counter increments periodically (every ~60 ticks ≈ 30s)
            if t > 0 and t % 60 == 0:
                ws.workCounter.totalWorkCounter += 1
                if ws.workCounter.currentWorkCounter < ws.workCounter.targetWorkCounter:
                    ws.workCounter.currentWorkCounter += 1

    def _update_program(self, channel, t: int) -> None:
        """Update current program block."""
        prog = channel.currentProgram
        if not prog.activePartProgram:
            return

        # Simulate block execution
        prog.currentBlockCounter = t % 1000
        prog.sequenceNumber = (t * 10) % 9999

        # Simulate G-code blocks
        blocks = [
            "G0 X0 Y0 Z50",
            "G1 X100 Y0 F500",
            "G1 X100 Y100",
            "G1 X0 Y100",
            "G1 X0 Y0",
            "G0 Z50",
            "G91 G28 Z0",
        ]
        block_idx = t % len(blocks)
        prog.lastBlock = blocks[(block_idx - 1) % len(blocks)]
        prog.currentBlock = blocks[block_idx]
        prog.nextBlock = blocks[(block_idx + 1) % len(blocks)]

    def _maybe_trigger_alarm(self, channel, t: int) -> None:
        """Randomly trigger/clear alarms."""
        # 0.5% chance per tick to add an alarm
        if random.random() < 0.005 and len(channel.alarm) < 5:
            alarm_types = ["WARNING", "ERROR", "INFO"]
            channel.alarm.append(
                Alarm(
                    alarmNumber=str(random.randint(1000, 9999)),
                    alarmText=f"Simulated alarm at tick {t}",
                    alarmCategory=random.choice(alarm_types),
                    raisedTimeStamp=datetime.now(timezone.utc).isoformat(),
                )
            )
            channel.numberOfAlarms = len(channel.alarm)
            channel.alarmStatus = 1

        # 2% chance to clear oldest alarm
        if random.random() < 0.02 and channel.alarm:
            channel.alarm.pop(0)
            channel.numberOfAlarms = len(channel.alarm)
            if not channel.alarm:
                channel.alarmStatus = 0

    @property
    def _interval_sec(self) -> float:
        return self.interval_ms / 1000.0

    def get_status(self) -> dict:
        """Get simulator status."""
        store = get_store()
        return {
            "running": self.running,
            "tick_count": self.tick_count,
            "interval_ms": self.interval_ms,
            "machines": list(store.machines.keys()),
        }


# ─── Singleton ───────────────────────────────────────────────────────────────

_simulator: Optional[DataSimulator] = None


def get_simulator() -> DataSimulator:
    """Get the singleton DataSimulator instance."""
    global _simulator
    if _simulator is None:
        _simulator = DataSimulator()
    return _simulator
