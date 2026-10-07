"""Tests for NC file parser."""

from src.parsers.nc_parser import NCSplitter


class TestNCSplitter:
    """Test NC file splitting by tool change."""

    def test_split_simple_nc(self):
        """Should split NC by T/M6 commands."""
        nc_content = """
%
O0001
G21 G90
T1 M6
G0 X0 Y0
G1 Z-5 F100
T2 M6
G0 X10 Y10
G1 Z-10 F200
M30
%
"""
        splitter = NCSplitter(nc_content).parse()

        assert len(splitter.segments) == 2
        assert splitter.segments[0].tool_number == "T1"
        assert splitter.segments[1].tool_number == "T2"
        assert splitter.base_o_number == "O0001"

    def test_assemble_segment(self):
        """Should assemble full NC segment with preamble, O-number, %, and M30."""
        nc_content = """
%
O0001
G21 G90
T1 M6
G0 X0 Y0
T2 M6
G0 X10 Y10
M30
%
"""
        splitter = NCSplitter(nc_content).parse()
        full_lines = splitter.assemble_segment(0)
        
        text = "".join(full_lines)
        assert text.startswith("%\n")
        assert "O1001\n" in text
        assert "G21" in text
        assert "T1 M6" in text
        assert "G0 X0 Y0" in text
        assert text.endswith("%\n")
        assert "M30\n%\n" in text

    def test_preamble_extraction(self):
        """Should extract preamble before first tool change."""
        nc_content = """
O1234
G21 G90 G54
G28 G91 Z0
T5 M6
S1000 M3
G0 X0 Y0
"""
        splitter = NCSplitter(nc_content).parse()

        assert splitter.base_o_number == "O1234"
        assert any("G21" in line for line in splitter.preamble)
        assert len(splitter.segments) == 1
        assert splitter.segments[0].tool_number == "T5"

    def test_get_tool_sequence(self):
        """Should return tool numbers in order."""
        nc_content = """
T3 M6
G0 X0
T1 M6
G0 X10
T5 M6
G0 X20
"""
        splitter = NCSplitter(nc_content).parse()

        assert splitter.get_tool_sequence() == ["T3", "T1", "T5"]

    def test_alternative_m6_format(self):
        """Should handle M6 T1 format."""
        nc_content = """
M6 T2
G0 X0
M06 T10
G0 X10
"""
        splitter = NCSplitter(nc_content).parse()

        assert len(splitter.segments) == 2
        assert splitter.segments[0].tool_number == "T2"
        assert splitter.segments[1].tool_number == "T10"

    def test_renumber_lines(self):
        """Should renumber N-codes."""
        splitter = NCSplitter("")
        lines = ["G0 X0", "G1 Y10 F100", "G0 Z5"]

        renumbered = splitter.renumber_lines(lines, start=10, step=5)

        assert renumbered[0].startswith("N0010")
        assert renumbered[1].startswith("N0015")
        assert renumbered[2].startswith("N0020")

    def test_empty_nc(self):
        """Should handle empty NC file."""
        splitter = NCSplitter("").parse()

        assert len(splitter.segments) == 0
        assert splitter.base_o_number is None
