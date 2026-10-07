"""Pytest configuration and fixtures for gcode-parser tests."""

import pytest
import sys
import tempfile
import os
from pathlib import Path

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gcode_parser_agent import GcodeParserAgent


@pytest.fixture
def agent():
    """Create a GcodeParserAgent instance."""
    return GcodeParserAgent()


@pytest.fixture
def sample_gcode():
    """Simple G-code sample for basic testing."""
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


@pytest.fixture
def temp_gcode_file(sample_gcode):
    """Create a temporary G-code file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".nc", delete=False, encoding="utf-8") as f:
        f.write(sample_gcode)
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)
