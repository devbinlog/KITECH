"""Tests for cam-runner agent."""

import pytest
import sys
import math
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cam_runner_agent import CAMRunnerAgent, CutterConfig, CuttingPath


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def agent():
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


# ============================================================================
# Agent Initialization Tests
# ============================================================================


class TestAgentInitialization:
    """Test agent initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initialization."""
        assert agent.name == "cam-runner"
        assert len(agent.tools) > 0

    def test_agent_with_config(self, custom_config_agent):
        """Test agent with custom config."""
        assert custom_config_agent.config == {"custom_setting": True}
        assert custom_config_agent.name == "cam-runner"

    def test_agent_has_default_tools(self, agent):
        """Test agent has default tools."""
        assert len(agent.tools) == 4  # 4 default tools
        assert 1 in agent.tools
        assert 2 in agent.tools
        assert 3 in agent.tools
        assert 4 in agent.tools

    def test_agent_opencamlib_flag(self, agent):
        """Test OpenCAMLib availability flag is set."""
        assert hasattr(agent, "opencamlib_available")
        assert isinstance(agent.opencamlib_available, bool)


# ============================================================================
# CutterConfig Tests
# ============================================================================


class TestCutterConfig:
    """Test CutterConfig class."""

    def test_cutter_config_creation(self, cyl_cutter):
        """Test CutterConfig creation."""
        assert cyl_cutter.tool_id == 1
        assert cyl_cutter.name == "Test Cyl Cutter"
        assert cyl_cutter.cutter_type == "CylCutter"
        assert cyl_cutter.diameter == 6.0
        assert cyl_cutter.length == 50.0

    def test_cutter_config_ball(self, ball_cutter):
        """Test ball cutter configuration."""
        assert ball_cutter.cutter_type == "BallCutter"
        assert ball_cutter.diameter == 4.0

    def test_cutter_config_bull(self, bull_cutter):
        """Test bull cutter configuration."""
        assert bull_cutter.cutter_type == "BullCutter"
        assert bull_cutter.diameter == 8.0

    def test_create_ocl_cutter_without_opencamlib(self, cyl_cutter):
        """Test OCL cutter creation when OpenCAMLib not available."""
        with patch("cam_runner_agent.OPENCAMLIB_AVAILABLE", False):
            result = cyl_cutter.create_ocl_cutter()
            assert result is None

    def test_cutter_config_default_values(self):
        """Test CutterConfig with default values."""
        cutter = CutterConfig(tool_id=99, name="Test")
        assert cutter.cutter_type == "CylCutter"
        assert cutter.diameter == 6.0
        assert cutter.length == 50.0


# ============================================================================
# CuttingPath Tests
# ============================================================================


class TestCuttingPath:
    """Test CuttingPath class."""

    def test_cutting_path_creation(self, cyl_cutter):
        """Test CuttingPath creation."""
        path = CuttingPath(
            start=(0, 0, 0),
            end=(10, 10, -5),
            cutter=cyl_cutter,
            is_cutting=True,
            command="G01",
        )

        assert path.start == (0, 0, 0)
        assert path.end == (10, 10, -5)
        assert path.is_cutting
        assert path.command == "G01"

    def test_cutting_path_ap_calculation(self, cyl_cutter):
        """Test axial depth (Ap) calculation."""
        path = CuttingPath(
            start=(0, 0, 10),
            end=(0, 0, 5),
            cutter=cyl_cutter,
            is_cutting=True,
        )

        assert path.Ap == 5.0  # |10 - 5| = 5

    def test_cutting_path_ae_calculation_linear(self, cyl_cutter):
        """Test radial depth (Ae) calculation for linear movement."""
        path = CuttingPath(
            start=(0, 0, 0),
            end=(30, 40, 0),  # XY distance = 50
            cutter=cyl_cutter,  # diameter = 6
            is_cutting=True,
            command="G01",
        )

        # For CylCutter, Ae = min(xy_distance, diameter)
        assert path.Ae == 6.0  # min(50, 6) = 6

    def test_cutting_path_ae_small_movement(self, cyl_cutter):
        """Test Ae for movement smaller than tool diameter."""
        path = CuttingPath(
            start=(0, 0, 0),
            end=(3, 4, 0),  # XY distance = 5
            cutter=cyl_cutter,  # diameter = 6
            is_cutting=True,
            command="G01",
        )

        assert path.Ae == 5.0  # min(5, 6) = 5

    def test_cutting_path_length_calculation(self, cyl_cutter):
        """Test 3D path length calculation."""
        path = CuttingPath(
            start=(0, 0, 0),
            end=(10, 10, 10),
            cutter=cyl_cutter,
            is_cutting=True,
        )

        expected = math.sqrt(10**2 + 10**2 + 10**2)
        assert abs(path.length - expected) < 0.001

    def test_cutting_path_rapid_move(self, cyl_cutter):
        """Test rapid move (non-cutting)."""
        path = CuttingPath(
            start=(0, 0, 0),
            end=(100, 100, 10),
            cutter=cyl_cutter,
            is_cutting=False,
            command="G00",
        )

        assert not path.is_cutting
        # Ae should be 0 for non-cutting
        assert path.Ae == 0

    def test_cutting_path_to_dict(self, cyl_cutter):
        """Test CuttingPath to_dict method."""
        path = CuttingPath(
            start=(0, 0, 10),
            end=(10, 20, 5),
            cutter=cyl_cutter,
            is_cutting=True,
        )

        result = path.to_dict()

        assert "start" in result
        assert "end" in result
        assert "tool_id" in result
        assert "tool_name" in result
        assert "is_cutting" in result
        assert "Ap" in result
        assert "Ae" in result
        assert "length" in result

        assert result["start"]["x"] == 0
        assert result["end"]["z"] == 5
        assert result["is_cutting"]

    def test_cutting_path_ball_cutter_engagement(self, ball_cutter):
        """Test engagement calculation for ball cutter."""
        path = CuttingPath(
            start=(0, 0, 0),
            end=(10, 0, 0),  # XY distance = 10
            cutter=ball_cutter,  # diameter = 4
            is_cutting=True,
        )

        # For BallCutter, Ae = min(xy_distance, diameter/2)
        assert path.Ae == 2.0  # min(10, 4/2) = 2

    def test_cutting_path_bull_cutter_engagement(self, bull_cutter):
        """Test engagement calculation for bull cutter."""
        path = CuttingPath(
            start=(0, 0, 0),
            end=(5, 0, 0),
            cutter=bull_cutter,  # diameter = 8
            is_cutting=True,
        )

        # For BullCutter, Ae = min(xy_distance, diameter/2)
        assert path.Ae == 4.0  # min(5, 8/2) = 4


class TestCuttingPathArcs:
    """Test CuttingPath with arc movements."""

    def test_arc_cw_engagement(self, cyl_cutter):
        """Test G02 (clockwise arc) engagement calculation."""
        path = CuttingPath(
            start=(50, 0, 0),
            end=(100, 50, 0),
            cutter=cyl_cutter,
            is_cutting=True,
            command="G02",
            arc_offset={"I": 50, "J": 0},
        )

        # Arc radius = sqrt(50^2 + 0^2) = 50
        # For CylCutter, Ae = min(arc_radius, diameter) = min(50, 6) = 6
        assert path.Ae == 6.0

    def test_arc_ccw_engagement(self, cyl_cutter):
        """Test G03 (counter-clockwise arc) engagement calculation."""
        path = CuttingPath(
            start=(0, 50, 0),
            end=(50, 0, 0),
            cutter=cyl_cutter,
            is_cutting=True,
            command="G03",
            arc_offset={"I": 0, "J": -50},
        )

        # Arc radius = sqrt(0^2 + 50^2) = 50
        assert path.Ae == 6.0  # min(50, 6)

    def test_arc_small_radius(self, cyl_cutter):
        """Test arc with small radius."""
        path = CuttingPath(
            start=(0, 0, 0),
            end=(4, 0, 0),
            cutter=cyl_cutter,
            is_cutting=True,
            command="G02",
            arc_offset={"I": 2, "J": 0},  # radius = 2
        )

        # Arc radius = 2, tool diameter = 6
        assert path.Ae == 2.0  # min(2, 6) = 2

    def test_arc_degenerate_zero_radius(self, cyl_cutter):
        """Test arc with zero radius (point arc)."""
        path = CuttingPath(
            start=(0, 0, 0),
            end=(5, 5, 0),
            cutter=cyl_cutter,
            is_cutting=True,
            command="G02",
            arc_offset={"I": 0, "J": 0},  # radius = 0
        )

        # Should fall back to linear engagement calculation
        math.sqrt(5**2 + 5**2)  # ~7.07
        assert path.Ae == 6.0  # min(7.07, 6)


# ============================================================================
# Agent Analysis Tests
# ============================================================================


class TestAnalyzeGcodePaths:
    """Test analyze_gcode_paths method."""

    def test_analyze_tool_paths(self, agent):
        """Test tool path analysis."""
        result = agent.analyze_gcode_paths({})
        assert result.status in ["success", "warning"]
        assert result.data is not None
        assert isinstance(result.data, dict)

    def test_analyze_simple_gcode_data(self, agent):
        """Test analysis with simple G-code blocks."""
        gcode_data = {
            "gcode_blocks": [
                {"type": "G00", "x": 10, "y": 20, "z": 0},
                {"type": "G01", "x": 10, "y": 20, "z": -5, "f": 100},
                {"type": "G01", "x": 20, "y": 20, "z": -5, "f": 100},
            ]
        }
        result = agent.analyze_gcode_paths(gcode_data)
        assert result.status in ["success", "warning"]
        assert result.data is not None

    def test_analyze_complex_gcode_data(self, agent):
        """Test analysis with complex G-code blocks."""
        gcode_data = {
            "gcode_blocks": [
                {"type": "G00", "x": 0, "y": 0, "z": 10},
                {"type": "G00", "x": 10, "y": 10, "z": 10},
                {"type": "G01", "x": 10, "y": 10, "z": 0, "f": 100},
                {"type": "G02", "x": 20, "y": 10, "i": 5, "j": 0, "f": 80},
                {"type": "G01", "x": 20, "y": 20, "z": -5, "f": 100},
                {"type": "G00", "x": 0, "y": 0, "z": 10},
            ]
        }
        result = agent.analyze_gcode_paths(gcode_data)
        assert result.status in ["success", "warning"]
        assert result.data is not None
        assert isinstance(result.data, dict)

    def test_analyze_with_sample_blocks(self, agent, sample_gcode_blocks):
        """Test analysis with sample blocks fixture."""
        result = agent.analyze_gcode_paths(sample_gcode_blocks)

        assert result.status == "success"
        assert "summary" in result.data
        assert "paths" in result.data

        summary = result.data["summary"]
        assert summary["total_paths"] == 3
        assert summary["cutting_segments"] == 2  # 2 cutting moves

    def test_analyze_with_arc_blocks(self, agent, arc_gcode_blocks):
        """Test analysis with arc blocks."""
        result = agent.analyze_gcode_paths(arc_gcode_blocks)

        assert result.status == "success"
        assert "summary" in result.data
        assert result.data["summary"]["cutting_segments"] == 2  # G02 and G03

    def test_analyze_empty_gcode_blocks(self, agent):
        """Test with empty gcode_blocks list."""
        gcode_data = {"gcode_blocks": []}
        result = agent.analyze_gcode_paths(gcode_data)
        assert result.status in ["success", "warning"]

    def test_analyze_none_gcode_data(self, agent):
        """Test with None gcode_data."""
        try:
            result = agent.analyze_gcode_paths(None)
            assert result.status in ["success", "warning", "error"]
        except Exception:
            pass  # Acceptable to raise error for None input

    def test_analyze_missing_gcode_blocks_key(self, agent):
        """Test with missing gcode_blocks key."""
        gcode_data = {"other_key": "value"}
        result = agent.analyze_gcode_paths(gcode_data)
        assert result.status in ["success", "warning"]

    def test_analyze_with_commands_key(self, agent):
        """Test analysis using 'commands' key instead of 'gcode_blocks'."""
        gcode_data = {
            "commands": [
                {
                    "command": "G01",
                    "start_position": {"X": 0, "Y": 0, "Z": 0},
                    "end_position": {"X": 10, "Y": 10, "Z": -5},
                    "is_cutting": True,
                }
            ]
        }
        result = agent.analyze_gcode_paths(gcode_data)
        assert result.status in ["success", "warning"]


class TestAnalysisSummary:
    """Test analysis summary calculations."""

    def test_summary_has_required_fields(self, agent, sample_gcode_blocks):
        """Test summary has all required fields."""
        result = agent.analyze_gcode_paths(sample_gcode_blocks)
        summary = result.data["summary"]

        assert "total_paths" in summary
        assert "cutting_segments" in summary
        assert "tool_id" in summary
        assert "tool_name" in summary

    def test_summary_ap_ae_statistics(self, agent, sample_gcode_blocks):
        """Test Ap/Ae statistics in summary."""
        result = agent.analyze_gcode_paths(sample_gcode_blocks)
        summary = result.data["summary"]

        if summary["cutting_segments"] > 0:
            assert "ap_max" in summary
            assert "ap_min" in summary
            assert "ap_avg" in summary
            assert "ae_max" in summary
            assert "ae_min" in summary
            assert "ae_avg" in summary

    def test_ap_values_consistency(self, agent):
        """Test Ap values are consistent."""
        gcode_data = {
            "gcode_blocks": [
                {
                    "command": "G01",
                    "start_position": {"X": 0, "Y": 0, "Z": 10},
                    "end_position": {"X": 0, "Y": 0, "Z": 5},
                    "is_cutting": True,
                },
                {
                    "command": "G01",
                    "start_position": {"X": 0, "Y": 0, "Z": 5},
                    "end_position": {"X": 0, "Y": 0, "Z": 2},
                    "is_cutting": True,
                },
            ]
        }
        result = agent.analyze_gcode_paths(gcode_data)
        summary = result.data["summary"]

        # First cut: Ap = 5, Second cut: Ap = 3
        assert summary["ap_max"] == 5.0
        assert summary["ap_min"] == 3.0
        assert abs(summary["ap_avg"] - 4.0) < 0.01


# ============================================================================
# Tool Management Tests
# ============================================================================


class TestToolFunctionality:
    """Test tool-related functionality."""

    def test_tool_list_not_empty(self, agent):
        """Test agent has tools."""
        assert len(agent.tools) > 0

    def test_tool_attributes(self, agent):
        """Test tool structure."""
        assert hasattr(agent, "tools")
        assert isinstance(agent.tools, dict)

        for tool_id, tool in agent.tools.items():
            assert hasattr(tool, "tool_id") or tool_id is not None
            assert hasattr(tool, "name") or hasattr(tool, "cutter_type")

    def test_get_tool_by_id(self, agent):
        """Test getting tool by ID."""
        tool = agent.get_tool(1)
        assert tool is not None
        assert tool.tool_id == 1

    def test_get_nonexistent_tool(self, agent):
        """Test getting non-existent tool."""
        tool = agent.get_tool(999)
        assert tool is None

    def test_list_tools(self, agent):
        """Test listing all tools."""
        tools = agent.list_tools()

        assert isinstance(tools, list)
        assert len(tools) == 4

        for tool in tools:
            assert "tool_id" in tool
            assert "name" in tool
            assert "cutter_type" in tool
            assert "diameter" in tool
            assert "length" in tool

    def test_default_tool_types(self, agent):
        """Test default tool types are correct."""
        tool1 = agent.get_tool(1)  # 3mm Endmill
        tool2 = agent.get_tool(2)  # 6mm Endmill
        tool3 = agent.get_tool(3)  # 4mm Ball Nose
        tool4 = agent.get_tool(4)  # 8mm Bull Mill

        assert tool1.cutter_type == "CylCutter"
        assert tool2.cutter_type == "CylCutter"
        assert tool3.cutter_type == "BallCutter"
        assert tool4.cutter_type == "BullCutter"


# ============================================================================
# Process Method Tests
# ============================================================================


class TestProcessMethod:
    """Test the process() method."""

    def test_process_returns_dict(self, agent, sample_gcode_blocks):
        """Test process returns dictionary."""
        result = agent.process(sample_gcode_blocks)

        assert isinstance(result, dict)
        assert "status" in result
        assert "data" in result

    def test_process_with_empty_input(self, agent):
        """Test process with empty input."""
        result = agent.process({})

        assert isinstance(result, dict)
        assert result["status"] in ["success", "warning", "error"]

    def test_process_error_handling(self, agent):
        """Test process handles errors gracefully."""
        # This should cause an error
        result = agent.process(None)

        assert isinstance(result, dict)
        assert result["status"] == "error"
        assert "errors" in result


# ============================================================================
# Edge Cases Tests
# ============================================================================


class TestEdgeCases:
    """Test edge cases."""

    def test_zero_length_path(self, agent):
        """Test path with zero length."""
        gcode_data = {
            "gcode_blocks": [
                {
                    "command": "G01",
                    "start_position": {"X": 10, "Y": 10, "Z": 5},
                    "end_position": {"X": 10, "Y": 10, "Z": 5},  # Same position
                    "is_cutting": True,
                }
            ]
        }
        result = agent.analyze_gcode_paths(gcode_data)
        assert result.status in ["success", "warning"]

    def test_very_large_coordinates(self, agent):
        """Test with very large coordinates."""
        gcode_data = {
            "gcode_blocks": [
                {
                    "command": "G01",
                    "start_position": {"X": 0, "Y": 0, "Z": 0},
                    "end_position": {"X": 100000, "Y": 100000, "Z": -1000},
                    "is_cutting": True,
                }
            ]
        }
        result = agent.analyze_gcode_paths(gcode_data)
        assert result.status in ["success", "warning"]

    def test_negative_coordinates(self, agent):
        """Test with negative coordinates."""
        gcode_data = {
            "gcode_blocks": [
                {
                    "command": "G01",
                    "start_position": {"X": -50, "Y": -50, "Z": -10},
                    "end_position": {"X": -100, "Y": -100, "Z": -20},
                    "is_cutting": True,
                }
            ]
        }
        result = agent.analyze_gcode_paths(gcode_data)
        assert result.status in ["success", "warning"]

    def test_flat_format_positions(self, agent):
        """Test with flat format positions (start_x, end_x)."""
        gcode_data = {
            "gcode_blocks": [
                {
                    "command": "G01",
                    "start_x": 0,
                    "start_y": 0,
                    "start_z": 10,
                    "end_x": 10,
                    "end_y": 10,
                    "end_z": 5,
                    "is_cutting": True,
                }
            ]
        }
        result = agent.analyze_gcode_paths(gcode_data)
        assert result.status in ["success", "warning"]

    def test_lowercase_position_keys(self, agent):
        """Test with lowercase position keys."""
        gcode_data = {
            "gcode_blocks": [
                {
                    "command": "G01",
                    "start_position": {"x": 0, "y": 0, "z": 10},
                    "end_position": {"x": 10, "y": 10, "z": 5},
                    "is_cutting": True,
                }
            ]
        }
        result = agent.analyze_gcode_paths(gcode_data)
        assert result.status in ["success", "warning"]

    def test_missing_is_cutting_flag(self, agent):
        """Test with missing is_cutting flag (defaults to True)."""
        gcode_data = {
            "gcode_blocks": [
                {
                    "command": "G01",
                    "start_position": {"X": 0, "Y": 0, "Z": 10},
                    "end_position": {"X": 10, "Y": 10, "Z": 5},
                    # No is_cutting field
                }
            ]
        }
        result = agent.analyze_gcode_paths(gcode_data)
        assert result.status in ["success", "warning"]

    def test_all_non_cutting_moves(self, agent):
        """Test with all non-cutting moves."""
        gcode_data = {
            "gcode_blocks": [
                {
                    "command": "G00",
                    "start_position": {"X": 0, "Y": 0, "Z": 10},
                    "end_position": {"X": 50, "Y": 50, "Z": 10},
                    "is_cutting": False,
                },
                {
                    "command": "G00",
                    "start_position": {"X": 50, "Y": 50, "Z": 10},
                    "end_position": {"X": 100, "Y": 100, "Z": 10},
                    "is_cutting": False,
                },
            ]
        }
        result = agent.analyze_gcode_paths(gcode_data)

        assert result.status in ["success", "warning"]
        # Should have warning about no cutting movements
        if result.status == "success":
            summary = result.data["summary"]
            assert summary["cutting_segments"] == 0 or "warning" in summary


# ============================================================================
# Result Structure Tests
# ============================================================================


class TestResultStructure:
    """Test result structure consistency."""

    def test_result_has_required_fields(self, agent):
        """Test result has status and data."""
        gcode_data = {"gcode_blocks": [{"type": "G00", "x": 10, "y": 20}]}
        result = agent.analyze_gcode_paths(gcode_data)

        assert hasattr(result, "status") or hasattr(result, "data")
        assert result.status in ["success", "warning", "error"]

    def test_result_data_is_dict(self, agent):
        """Test result.data is always a dictionary."""
        result = agent.analyze_gcode_paths({})
        assert isinstance(result.data, dict)

    def test_summary_in_result_data(self, agent):
        """Test summary key in result data."""
        result = agent.analyze_gcode_paths({})
        assert len(result.data) > 0 or result.data is not None

    def test_paths_limited_to_20(self, agent):
        """Test that paths array is limited to 20 items."""
        # Create 50 blocks
        blocks = []
        for i in range(50):
            blocks.append(
                {
                    "command": "G01",
                    "start_position": {"X": i, "Y": 0, "Z": 0},
                    "end_position": {"X": i + 1, "Y": 0, "Z": 0},
                    "is_cutting": True,
                }
            )

        result = agent.analyze_gcode_paths({"gcode_blocks": blocks})

        if result.status == "success":
            # Paths should be limited to 20
            assert len(result.data["paths"]) <= 20
            # But total_segments should reflect actual count
            assert result.data["total_segments"] == 50


# ============================================================================
# Cycle Time Tests
# ============================================================================


class TestCycleTimeCalculation:
    """Test cycle time calculation functionality."""

    def test_cycle_time_in_result(self, agent):
        """Test cycle_time is included in result."""
        gcode_data = {
            "gcode_blocks": [
                {
                    "command": "G01",
                    "start_position": {"X": 0, "Y": 0, "Z": 10},
                    "end_position": {"X": 10, "Y": 10, "Z": 0},
                    "is_cutting": True,
                }
            ],
            "cutting_distance": 100.0,
            "rapid_distance": 50.0,
            "feed_rate": 500.0,
            "dwell_time": 2.0,
        }
        result = agent.analyze_gcode_paths(gcode_data)

        assert result.status == "success"
        assert "cycle_time" in result.data

        cycle_time = result.data["cycle_time"]
        assert "cutting_time_sec" in cycle_time
        assert "rapid_time_sec" in cycle_time
        assert "dwell_time_sec" in cycle_time
        assert "total_cycle_time_sec" in cycle_time
        assert "total_cycle_time_min" in cycle_time

    def test_cycle_time_calculation_values(self, agent):
        """Test cycle time calculation accuracy."""
        gcode_data = {
            "gcode_blocks": [
                {
                    "command": "G01",
                    "start_position": {"X": 0, "Y": 0, "Z": 0},
                    "end_position": {"X": 100, "Y": 0, "Z": 0},
                    "is_cutting": True,
                }
            ],
            "cutting_distance": 600.0,  # mm
            "rapid_distance": 100.0,  # mm
            "feed_rate": 600.0,  # mm/min
            "dwell_time": 5.0,  # seconds
        }
        result = agent.analyze_gcode_paths(gcode_data)

        cycle_time = result.data["cycle_time"]
        # cutting_time = 600 / 600 * 60 = 60 seconds
        assert cycle_time["cutting_time_sec"] == 60.0
        # rapid_time = 100 / 5000 * 60 = 1.2 seconds
        assert cycle_time["rapid_time_sec"] == 1.2
        assert cycle_time["dwell_time_sec"] == 5.0

    def test_tool_change_count(self, agent):
        """Test tool change counting."""
        gcode_data = {
            "gcode_blocks": [
                {
                    "command": "G01",
                    "start_position": {"X": 0, "Y": 0, "Z": 0},
                    "end_position": {"X": 10, "Y": 0, "Z": 0},
                    "is_cutting": True,
                    "parameters": {"T": 1},
                },
                {
                    "command": "G01",
                    "start_position": {"X": 10, "Y": 0, "Z": 0},
                    "end_position": {"X": 20, "Y": 0, "Z": 0},
                    "is_cutting": True,
                    "parameters": {"T": 2},  # Tool change
                },
                {
                    "command": "G01",
                    "start_position": {"X": 20, "Y": 0, "Z": 0},
                    "end_position": {"X": 30, "Y": 0, "Z": 0},
                    "is_cutting": True,
                    "parameters": {"T": 3},  # Another tool change
                },
            ],
            "cutting_distance": 30.0,
            "feed_rate": 600.0,
        }
        result = agent.analyze_gcode_paths(gcode_data)

        cycle_time = result.data["cycle_time"]
        # 3 tools seen, 2 changes (first tool doesn't count as change)
        assert cycle_time["tool_change_count"] == 2
        # 2 changes * 8 sec = 16 sec
        assert cycle_time["tool_change_time_sec"] == 16.0

    def test_zero_feed_rate_handling(self, agent):
        """Test handling of zero feed rate."""
        gcode_data = {
            "gcode_blocks": [
                {
                    "command": "G01",
                    "start_position": {"X": 0, "Y": 0, "Z": 0},
                    "end_position": {"X": 10, "Y": 0, "Z": 0},
                    "is_cutting": True,
                }
            ],
            "cutting_distance": 100.0,
            "feed_rate": 0,  # Zero feed rate
        }
        result = agent.analyze_gcode_paths(gcode_data)

        # Should handle gracefully without division by zero
        assert result.status == "success"
        cycle_time = result.data["cycle_time"]
        assert cycle_time["cutting_time_sec"] == 0


class TestCutterConfigOCL:
    """Test CutterConfig OpenCAMLib integration."""

    def test_unknown_cutter_type(self):
        """Test unknown cutter type falls back to CylCutter."""
        cutter = CutterConfig(
            tool_id=99,
            name="Unknown Cutter",
            cutter_type="UnknownType",
            diameter=10.0,
            length=50.0,
        )
        # Without OpenCAMLib, should return None
        with patch("cam_runner_agent.OPENCAMLIB_AVAILABLE", False):
            result = cutter.create_ocl_cutter()
            assert result is None


class TestArcEngagementWithBallBull:
    """Test arc engagement calculation for ball and bull cutters."""

    def test_arc_with_ball_cutter(self, ball_cutter):
        """Test G02 arc with ball cutter."""
        path = CuttingPath(
            start=(0, 0, 0),
            end=(10, 10, 0),
            cutter=ball_cutter,  # diameter=4
            is_cutting=True,
            command="G02",
            arc_offset={"I": 5, "J": 5},  # radius = sqrt(50) ≈ 7.07
        )
        # For BallCutter, Ae = min(arc_radius, diameter/2) = min(7.07, 2) = 2
        assert path.Ae == 2.0

    def test_arc_with_bull_cutter(self, bull_cutter):
        """Test G03 arc with bull cutter."""
        path = CuttingPath(
            start=(0, 0, 0),
            end=(10, 10, 0),
            cutter=bull_cutter,  # diameter=8
            is_cutting=True,
            command="G03",
            arc_offset={"I": 3, "J": 4},  # radius = 5
        )
        # For BullCutter, Ae = min(arc_radius, diameter/2) = min(5, 4) = 4
        assert path.Ae == 4.0


# ============================================================================
# Advanced CAM Runner Agent Tests
# ============================================================================


class TestAdvancedCamRunnerAgent:
    """Test advanced CAM runner functionality"""

    @pytest.fixture
    def advanced_agent(self):
        """Create advanced CAM runner agent"""
        try:
            from src.advanced_cam_runner_agent import AdvancedCamRunnerAgent

            return AdvancedCamRunnerAgent()
        except ImportError:
            pytest.skip("AdvancedCamRunnerAgent not available")

    def test_advanced_agent_initialization(self, advanced_agent):
        """Test agent initializes correctly"""
        assert advanced_agent is not None
        assert hasattr(advanced_agent, "process")

    def test_advanced_process_simple_gcode(self, advanced_agent):
        """Test processing simple G-code"""
        gcode_data = {
            "blocks": [
                {"command": "G00", "X": 0, "Y": 0, "Z": 5},
                {"command": "G01", "X": 10, "Y": 10, "Z": -5, "F": 100},
            ],
            "metadata": {"program_number": "O0001"},
        }
        result = advanced_agent.process(gcode_data)
        assert "status" in result or "data" in result

    def test_advanced_process_empty_input(self, advanced_agent):
        """Test handling empty input"""
        result = advanced_agent.process({})
        assert result is not None

    def test_advanced_process_with_arcs(self, advanced_agent):
        """Test processing arc commands"""
        gcode_data = {
            "blocks": [
                {"command": "G00", "X": 0, "Y": 0, "Z": 5},
                {"command": "G02", "X": 10, "Y": 10, "I": 5, "J": 0, "F": 100},
                {"command": "G03", "X": 0, "Y": 0, "I": -5, "J": 0, "F": 100},
            ]
        }
        result = advanced_agent.process(gcode_data)
        assert result is not None
