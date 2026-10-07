"""Pytest configuration and fixtures for cam-runner tests."""

import pytest
import sys
from pathlib import Path

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cam_runner_agent import CAMRunnerAgent, CutterConfig


@pytest.fixture
def agent():
    """Create a CAMRunnerAgent instance."""
    return CAMRunnerAgent()


@pytest.fixture
def custom_config_agent():
    """Agent with custom configuration."""
    config = {"custom_setting": True}
    return CAMRunnerAgent(config=config)


@pytest.fixture
def cyl_cutter():
    """Cylindrical cutter configuration."""
    return CutterConfig(
        tool_id=1,
        name="Test Cyl Cutter",
        cutter_type="CylCutter",
        diameter=6.0,
        length=50.0,
    )


@pytest.fixture
def ball_cutter():
    """Ball cutter configuration."""
    return CutterConfig(
        tool_id=2,
        name="Test Ball Cutter",
        cutter_type="BallCutter",
        diameter=4.0,
        length=50.0,
    )


@pytest.fixture
def bull_cutter():
    """Bull cutter configuration."""
    return CutterConfig(
        tool_id=3,
        name="Test Bull Cutter",
        cutter_type="BullCutter",
        diameter=8.0,
        length=50.0,
    )


@pytest.fixture
def sample_gcode_blocks():
    """Sample G-code blocks for testing."""
    return {
        "gcode_blocks": [
            {
                "command": "G00",
                "start_position": {"X": 0, "Y": 0, "Z": 10},
                "end_position": {"X": 10, "Y": 10, "Z": 10},
                "is_cutting": False,
            },
            {
                "command": "G01",
                "start_position": {"X": 10, "Y": 10, "Z": 10},
                "end_position": {"X": 10, "Y": 10, "Z": 0},
                "is_cutting": True,
            },
            {
                "command": "G01",
                "start_position": {"X": 10, "Y": 10, "Z": 0},
                "end_position": {"X": 30, "Y": 50, "Z": 0},
                "is_cutting": True,
            },
        ]
    }


@pytest.fixture
def arc_gcode_blocks():
    """G-code blocks with arc movements."""
    return {
        "gcode_blocks": [
            {
                "command": "G00",
                "start_position": {"X": 0, "Y": 0, "Z": 10},
                "end_position": {"X": 50, "Y": 0, "Z": 0},
                "is_cutting": False,
            },
            {
                "command": "G02",
                "start_position": {"X": 50, "Y": 0, "Z": 0},
                "end_position": {"X": 100, "Y": 50, "Z": 0},
                "parameters": {"I": 50, "J": 0},
                "is_cutting": True,
            },
            {
                "command": "G03",
                "start_position": {"X": 100, "Y": 50, "Z": 0},
                "end_position": {"X": 50, "Y": 100, "Z": 0},
                "parameters": {"I": 0, "J": 50},
                "is_cutting": True,
            },
        ]
    }
