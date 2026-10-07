"""Tests for gcode-parser agent."""

import pytest
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gcode_parser_agent import GcodeParserAgent


@pytest.fixture
def agent():
    return GcodeParserAgent()


@pytest.fixture
def sample_gcode():
    return """
    G90
    G00 X10 Y20
    G01 Z-5 F100
    M05
    """


@pytest.fixture
def complex_gcode():
    """Complex G-code with multiple movements and parameters."""
    return """
; Header comment
(Program start)
G90 ; Absolute positioning
G21 ; Metric units
M03 S12000 ; Spindle ON
G00 X0 Y0 Z10 ; Rapid to start
G00 X50 Y50 ; Rapid XY move
G01 Z-5 F500 ; Plunge
G01 X100 Y50 F1000 ; Linear cut
G02 X150 Y100 I50 J0 F800 ; Arc CW
G03 X100 Y150 I0 J50 F800 ; Arc CCW
G01 Z10 F500 ; Retract
G00 X0 Y0 ; Return to origin
M05 ; Spindle OFF
M30 ; Program end
"""


@pytest.fixture
def ncode_gcode():
    """G-code with N-number line identifiers."""
    return """
N10 G90
N20 G00 X10 Y20
N30 G01 Z-5 F100
N40 M05
"""


class TestAgentInitialization:
    """Test agent initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initialization."""
        assert agent.name == "gcode-parser"

    def test_agent_with_config(self):
        """Test agent initialization with custom config."""
        config = {"custom_setting": True}
        agent = GcodeParserAgent(config=config)
        assert agent.name == "gcode-parser"
        assert agent.config == config

    def test_agent_with_empty_config(self):
        """Test agent initialization with empty config."""
        agent = GcodeParserAgent(config={})
        assert agent.name == "gcode-parser"
        assert agent.config == {}

    def test_agent_default_config(self):
        """Test agent initialization with None config."""
        agent = GcodeParserAgent(config=None)
        assert agent.config == {}


class TestBasicGcodeAnalysis:
    """Test basic G-code analysis."""

    def test_analyze_gcode(self, agent, sample_gcode):
        """Test G-code analysis."""
        result = agent.analyze_gcode(sample_gcode, "test.nc")
        assert result.status == "success"
        assert result.data["filename"] == "test.nc"

    def test_analyze_gcode_filename(self, agent, sample_gcode):
        """Test that filename is correctly stored."""
        result = agent.analyze_gcode(sample_gcode, "custom_file.nc")
        assert result.data["filename"] == "custom_file.nc"

    def test_analyze_gcode_default_filename(self, agent, sample_gcode):
        """Test default filename when not specified."""
        result = agent.analyze_gcode(sample_gcode)
        assert result.data["filename"] == "gcode"

    def test_analyze_empty_gcode(self, agent):
        """Test analysis of empty G-code."""
        result = agent.analyze_gcode("", "empty.nc")
        assert result.status == "success"
        assert result.data["total_commands"] == 0

    def test_analyze_comments_only(self, agent):
        """Test analysis of G-code with only comments."""
        gcode = """
; This is a comment
(Another comment)
; More comments
"""
        result = agent.analyze_gcode(gcode, "comments.nc")
        assert result.status == "success"
        assert result.data["total_commands"] == 0


class TestMotionCommands:
    """Test motion command parsing (G00, G01, G02, G03)."""

    def test_rapid_motion_g00(self, agent):
        """Test G00 rapid motion command."""
        gcode = """
G90
G00 X100 Y50 Z10
"""
        result = agent.analyze_gcode(gcode, "rapid.nc")
        assert result.status == "success"
        assert result.data["rapid_distance"] > 0

    def test_linear_motion_g01(self, agent):
        """Test G01 linear interpolation command."""
        gcode = """
G90
G00 X0 Y0 Z0
G01 X50 Y50 Z-5 F1000
"""
        result = agent.analyze_gcode(gcode, "linear.nc")
        assert result.status == "success"
        assert result.data["cutting_distance"] > 0

    def test_arc_cw_g02(self, agent):
        """Test G02 clockwise arc command."""
        gcode = """
G90
G00 X0 Y0 Z0
G01 X50 Y0 F1000
G02 X100 Y50 I50 J0 F500
"""
        result = agent.analyze_gcode(gcode, "arc_cw.nc")
        assert result.status == "success"
        # G02 should count as cutting
        assert result.data["cutting_distance"] > 0

    def test_arc_ccw_g03(self, agent):
        """Test G03 counter-clockwise arc command."""
        gcode = """
G90
G00 X0 Y0 Z0
G01 X50 Y0 F1000
G03 X100 Y50 I0 J50 F500
"""
        result = agent.analyze_gcode(gcode, "arc_ccw.nc")
        assert result.status == "success"
        assert result.data["cutting_distance"] > 0

    def test_mixed_motion_commands(self, agent, complex_gcode):
        """Test mixed G00, G01, G02, G03 commands."""
        result = agent.analyze_gcode(complex_gcode, "mixed.nc")
        assert result.status == "success"
        assert result.data["rapid_distance"] > 0
        assert result.data["cutting_distance"] > 0
        assert result.data["total_distance"] > result.data["rapid_distance"]


class TestDistanceCalculations:
    """Test distance calculations."""

    def test_xy_distance(self, agent):
        """Test XY plane distance calculation."""
        gcode = """
G90
G00 X0 Y0 Z0
G01 X30 Y40 F1000
"""
        result = agent.analyze_gcode(gcode, "xy.nc")
        assert result.status == "success"
        # Should be sqrt(30^2 + 40^2) = 50mm for cutting
        assert abs(result.data["cutting_distance"] - 50.0) < 0.1

    def test_z_distance(self, agent):
        """Test Z axis distance calculation."""
        gcode = """
G90
G00 X0 Y0 Z0
G01 Z-10 F100
"""
        result = agent.analyze_gcode(gcode, "z.nc")
        assert result.status == "success"
        assert abs(result.data["cutting_distance"] - 10.0) < 0.1

    def test_3d_distance(self, agent):
        """Test 3D distance calculation."""
        gcode = """
G90
G00 X0 Y0 Z0
G01 X10 Y10 Z10 F1000
"""
        result = agent.analyze_gcode(gcode, "3d.nc")
        assert result.status == "success"
        # sqrt(10^2 + 10^2 + 10^2) = sqrt(300) ≈ 17.32
        expected = (10**2 + 10**2 + 10**2) ** 0.5
        assert abs(result.data["cutting_distance"] - expected) < 0.1

    def test_no_movement(self, agent):
        """Test when there's no actual movement."""
        gcode = """
G90
G00 X10 Y10 Z10
G01 X10 Y10 Z10 F1000
"""
        result = agent.analyze_gcode(gcode, "no_move.nc")
        assert result.status == "success"
        # Second command has no movement, so only 1 command (first G00) recorded
        assert result.data["total_commands"] == 1


class TestSpindleAndFeedRate:
    """Test spindle speed and feed rate extraction."""

    def test_spindle_speed(self, agent):
        """Test spindle speed extraction."""
        gcode = """
G90
M03 S12000
G00 X10 Y10
G01 Z-5 F500
"""
        result = agent.analyze_gcode(gcode, "spindle.nc")
        assert result.status == "success"
        assert result.data["spindle_speed"] == 12000

    def test_feed_rate(self, agent):
        """Test feed rate extraction."""
        gcode = """
G90
G00 X10 Y10
G01 Z-5 F750
"""
        result = agent.analyze_gcode(gcode, "feed.nc")
        assert result.status == "success"
        assert result.data["feed_rate"] == 750

    def test_feed_rate_change(self, agent):
        """Test feed rate changes during program."""
        gcode = """
G90
G00 X0 Y0 Z10
G01 Z-5 F500
G01 X50 Y50 F1000
G01 Z10 F800
"""
        result = agent.analyze_gcode(gcode, "feed_change.nc")
        assert result.status == "success"
        # Should capture the last feed rate
        assert result.data["feed_rate"] == 800


class TestNNumberLines:
    """Test N-number (line number) parsing."""

    def test_n_number_extraction(self, agent, ncode_gcode):
        """Test N-number extraction from lines."""
        result = agent.analyze_gcode(ncode_gcode, "ncode.nc")
        assert result.status == "success"
        blocks = result.data.get("gcode_blocks", [])
        # Check if N-numbers are captured
        for block in blocks:
            if block.get("n_number") is not None:
                assert isinstance(block["n_number"], int)

    def test_mixed_n_number(self, agent):
        """Test G-code with some N-numbers and some without."""
        gcode = """
N10 G90
G00 X10 Y10
N30 G01 Z-5 F100
G01 X20 Y20 F200
"""
        result = agent.analyze_gcode(gcode, "mixed_n.nc")
        assert result.status == "success"


class TestGcodeBlocks:
    """Test G-code block generation."""

    def test_block_structure(self, agent, sample_gcode):
        """Test that blocks have correct structure."""
        result = agent.analyze_gcode(sample_gcode, "blocks.nc")
        assert result.status == "success"
        blocks = result.data.get("gcode_blocks", [])

        if blocks:
            block = blocks[0]
            assert "block_number" in block
            assert "line_number" in block
            assert "command" in block
            assert "start_position" in block
            assert "end_position" in block
            assert "Ap" in block  # Axial depth
            assert "Ae" in block  # Radial depth
            assert "distance" in block
            assert "is_cutting" in block

    def test_block_positions(self, agent):
        """Test that block positions are tracked correctly."""
        gcode = """
G90
G00 X10 Y20 Z5
G01 X30 Y40 Z-5 F1000
"""
        result = agent.analyze_gcode(gcode, "positions.nc")
        assert result.status == "success"
        blocks = result.data.get("gcode_blocks", [])

        if len(blocks) >= 2:
            # First block ends at X10 Y20 Z5
            assert blocks[0]["end_position"]["X"] == 10
            assert blocks[0]["end_position"]["Y"] == 20

            # Second block starts at first block's end
            assert blocks[1]["start_position"]["X"] == 10
            assert blocks[1]["start_position"]["Y"] == 20

    def test_ap_ae_calculation(self, agent):
        """Test Ap (axial depth) and Ae (radial depth) calculations."""
        gcode = """
G90
G00 X0 Y0 Z10
G01 Z-5 F500
G01 X30 Y40 F1000
"""
        result = agent.analyze_gcode(gcode, "ap_ae.nc")
        assert result.status == "success"
        blocks = result.data.get("gcode_blocks", [])

        # Find Z plunge block
        z_block = None
        xy_block = None
        for block in blocks:
            if block["command"] == "G01":
                if block["end_position"]["Z"] == -5 and block["start_position"]["Z"] == 10:
                    z_block = block
                elif block["end_position"]["X"] == 30:
                    xy_block = block

        if z_block:
            # Ap should be 15 (from Z10 to Z-5)
            assert abs(z_block["Ap"] - 15) < 0.1

        if xy_block:
            # Ae should be 50 (sqrt(30^2 + 40^2))
            assert abs(xy_block["Ae"] - 50) < 0.1

    def test_is_cutting_flag(self, agent):
        """Test is_cutting flag for different commands."""
        gcode = """
G90
G00 X10 Y10 Z10
G01 X20 Y20 F1000
G02 X30 Y30 I5 J0 F800
G03 X40 Y40 I0 J5 F800
"""
        result = agent.analyze_gcode(gcode, "cutting.nc")
        assert result.status == "success"
        blocks = result.data.get("gcode_blocks", [])

        for block in blocks:
            if block["command"] == "G00":
                assert not block["is_cutting"]
            elif block["command"] in ["G01", "G02", "G03"]:
                assert block["is_cutting"]


class TestProcessMethod:
    """Test the process() method."""

    def test_process_string_input(self, agent, sample_gcode):
        """Test process with string input."""
        result = agent.process(sample_gcode)
        assert result["status"] == "success"
        assert result["data"]["filename"] == "inline_gcode"

    def test_process_file_input(self, agent, sample_gcode):
        """Test process with file path input."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".nc", delete=False, encoding="utf-8"
        ) as f:
            f.write(sample_gcode)
            temp_path = f.name

        try:
            result = agent.process(temp_path)
            assert result["status"] == "success"
            assert (
                temp_path.split("\\")[-1] in result["data"]["filename"]
                or temp_path.split("/")[-1] in result["data"]["filename"]
            )
        finally:
            os.unlink(temp_path)

    def test_process_nonexistent_file(self, agent):
        """Test process with non-existent file path."""
        result = agent.process("/nonexistent/path/file.nc")
        # Should treat it as G-code text since file doesn't exist
        assert result["status"] == "success"
        assert result["data"]["filename"] == "inline_gcode"


class TestFileEncodings:
    """Test file encoding handling."""

    def test_utf8_encoding(self, agent):
        """Test UTF-8 encoded file."""
        gcode = "G90\nG00 X10 Y10 ; UTF-8 comment: äöü\n"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".nc", delete=False, encoding="utf-8"
        ) as f:
            f.write(gcode)
            temp_path = f.name

        try:
            result = agent.process(temp_path)
            assert result["status"] == "success"
        finally:
            os.unlink(temp_path)

    def test_cp1252_encoding(self, agent):
        """Test CP1252 (Windows) encoded file."""
        gcode = "G90\nG00 X10 Y10\n"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".nc", delete=False, encoding="cp1252"
        ) as f:
            f.write(gcode)
            temp_path = f.name

        try:
            result = agent.process(temp_path)
            assert result["status"] == "success"
        finally:
            os.unlink(temp_path)


class TestModalGCodes:
    """Test modal G-code behavior (coordinates without explicit G code)."""

    def test_modal_g00(self, agent):
        """Test implicit G00 modal continuation."""
        gcode = """
G90
G00 X10 Y10
X20 Y20
X30 Y30
"""
        result = agent.analyze_gcode(gcode, "modal_g00.nc")
        assert result.status == "success"
        # All movements should be rapid (modal G00)
        assert result.data["cutting_distance"] == 0
        assert result.data["rapid_distance"] > 0

    def test_modal_g01(self, agent):
        """Test implicit G01 modal continuation."""
        gcode = """
G90
G00 X0 Y0 Z10
G01 X10 Y10 F1000
X20 Y20
X30 Y30
"""
        result = agent.analyze_gcode(gcode, "modal_g01.nc")
        assert result.status == "success"
        # After G01, coordinate-only lines should be cutting
        assert result.data["cutting_distance"] > 0


class TestErrorHandling:
    """Test error handling."""

    def test_invalid_gcode_graceful(self, agent):
        """Test that invalid G-code is handled gracefully."""
        gcode = """
INVALID CONTENT HERE
NOT G-CODE AT ALL
12345
"""
        result = agent.analyze_gcode(gcode, "invalid.nc")
        # Should not crash, might have 0 commands
        assert result.status == "success" or result.status == "error"

    @patch("gcode_parser_agent.gcodeparser", None)
    def test_missing_gcodeparser_library(self):
        """Test behavior when gcodeparser library is not available."""
        # Reload the agent with mocked None gcodeparser
        import gcode_parser_agent

        original_gcodeparser = gcode_parser_agent.gcodeparser
        gcode_parser_agent.gcodeparser = None

        try:
            agent = GcodeParserAgent()
            result = agent.analyze_gcode("G00 X10 Y10", "test.nc")
            assert result.status == "error"
            assert "not available" in result.message or "not installed" in result.message
        finally:
            gcode_parser_agent.gcodeparser = original_gcodeparser


class TestResultStructure:
    """Test result data structure."""

    def test_result_has_timestamp(self, agent, sample_gcode):
        """Test that result has timestamp."""
        result = agent.analyze_gcode(sample_gcode, "test.nc")
        result_dict = result.to_dict()
        assert "timestamp" in result_dict

    def test_result_to_dict(self, agent, sample_gcode):
        """Test result to_dict conversion."""
        result = agent.analyze_gcode(sample_gcode, "test.nc")
        result_dict = result.to_dict()

        assert "status" in result_dict
        assert "message" in result_dict
        assert "data" in result_dict
        assert "errors" in result_dict
        assert "warnings" in result_dict

    def test_process_returns_dict(self, agent, sample_gcode):
        """Test that process() returns a dictionary."""
        result = agent.process(sample_gcode)
        assert isinstance(result, dict)
        assert "status" in result
        assert "data" in result


class TestEdgeCases:
    """Test edge cases."""

    def test_very_large_coordinates(self, agent):
        """Test handling of very large coordinates."""
        gcode = """
G90
G00 X100000 Y100000 Z100000
G01 X-100000 Y-100000 Z-100000 F1000
"""
        result = agent.analyze_gcode(gcode, "large.nc")
        assert result.status == "success"
        assert result.data["total_distance"] > 0

    def test_very_small_coordinates(self, agent):
        """Test handling of very small (micro) coordinates."""
        gcode = """
G90
G00 X0.001 Y0.001 Z0.001
G01 X0.002 Y0.002 Z0.002 F100
"""
        result = agent.analyze_gcode(gcode, "micro.nc")
        assert result.status == "success"
        assert result.data["total_distance"] > 0

    def test_negative_coordinates(self, agent):
        """Test handling of negative coordinates."""
        gcode = """
G90
G00 X-50 Y-50 Z-10
G01 X-100 Y-100 Z-20 F500
"""
        result = agent.analyze_gcode(gcode, "negative.nc")
        assert result.status == "success"
        assert result.data["total_distance"] > 0

    def test_whitespace_handling(self, agent):
        """Test handling of various whitespace."""
        gcode = """
    G90
G00     X10    Y10
   G01 X20 Y20 F1000
"""
        result = agent.analyze_gcode(gcode, "whitespace.nc")
        assert result.status == "success"

    def test_mixed_case_commands(self, agent):
        """Test handling of mixed case G-codes."""
        gcode = """
g90
G00 x10 y10
g01 X20 Y20 f1000
"""
        result = agent.analyze_gcode(gcode, "mixed_case.nc")
        # May or may not be supported depending on parser
        # Just ensure it doesn't crash
        assert result.status in ["success", "error"]

    def test_inline_comments(self, agent):
        """Test handling of inline comments."""
        gcode = """
G90 ; Set absolute mode
G00 X10 Y10 (Rapid to position)
G01 X20 Y20 F1000 ; Linear move
"""
        result = agent.analyze_gcode(gcode, "inline.nc")
        assert result.status == "success"

    def test_multiple_commands_same_line(self, agent):
        """Test multiple commands on same line (if supported)."""
        gcode = """
G90 G00 X10 Y10
G01 Z-5 F100 M03 S1000
"""
        result = agent.analyze_gcode(gcode, "multi.nc")
        # Just ensure it doesn't crash
        assert result.status in ["success", "error"]
