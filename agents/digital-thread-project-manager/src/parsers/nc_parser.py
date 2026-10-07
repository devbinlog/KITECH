"""NC file parser - Tool sequence extraction and splitting."""

import re
from dataclasses import dataclass, field


@dataclass
class NCSegment:
    """Single tool operation segment from NC file."""

    tool_number: str
    lines: list[str] = field(default_factory=list)
    o_number: str | None = None


class NCSplitter:
    """Split NC file by tool changes (T/M6 commands)."""

    TOOL_PATTERN = re.compile(r"(T0*\d{1,3}\s*M0?6)|(M0?6\s*T0*\d{1,3})", re.IGNORECASE)
    O_NUMBER_PATTERN = re.compile(r"^(O|:)(\d+)", re.IGNORECASE)
    N_NUMBER_PATTERN = re.compile(r"^N(\d+)")

    def __init__(self, content: str):
        self.lines = content.splitlines()
        self.preamble: list[str] = []
        self.segments: list[NCSegment] = []
        self.base_o_number: str | None = None

    def parse(self) -> "NCSplitter":
        """Parse NC file and split by tool changes."""
        current: list[str] = []
        tool_found = False
        current_tool = ""

        for line in self.lines:
            stripped = line.strip()
            if not stripped or stripped == "%":
                continue

            # Extract O-number from preamble
            if not tool_found and self.base_o_number is None:
                match = self.O_NUMBER_PATTERN.match(stripped)
                if match:
                    self.base_o_number = stripped
                    continue

            # Check for tool change
            tool_match = self.TOOL_PATTERN.search(stripped)
            if tool_match:
                if current and tool_found:
                    self.segments.append(NCSegment(tool_number=current_tool, lines=current))
                current = [line]
                current_tool = self._extract_tool_number(tool_match.group())
                tool_found = True
            else:
                if tool_found:
                    current.append(line)
                else:
                    self.preamble.append(line)

        if current:
            self.segments.append(NCSegment(tool_number=current_tool, lines=current))

        return self

    def _extract_tool_number(self, text: str) -> str:
        """Extract tool number from T-code."""
        match = re.search(r"T0*(\d{1,3})", text, re.IGNORECASE)
        return f"T{int(match.group(1))}" if match else "T0"

    def get_tool_sequence(self) -> list[str]:
        """Return list of tool numbers in order."""
        return [seg.tool_number for seg in self.segments]

    def renumber_lines(
        self,
        lines: list[str],
        start: int = 10,
        step: int = 10,
        width: int = 4,
        padding: bool = True,
    ) -> list[str]:
        """Renumber N-codes in lines."""
        result = []
        n = start

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Remove existing N-number
            if stripped.startswith("N"):
                match = re.match(r"^N\d+\s*(.*)", stripped)
                content = match.group(1) if match else stripped[1:]
            else:
                content = stripped

            # Generate new N-number
            n_str = f"N{n:0{width}d}" if padding else f"N{n}"
            result.append(f"{n_str} {content}\n")
            n += step

        return result

    def assemble_segment(self, index: int) -> list[str]:
        """
        Assemble the full NC code for a segment index.
        Includes %, generated O-number, preamble, segment lines, M30, and %.
        """
        segment = self.segments[index]
        full: list[str] = []

        # Start with %
        full.append("%\n")

        # Generate new O-number based on base_o_number
        if self.base_o_number:
            match = self.O_NUMBER_PATTERN.match(self.base_o_number)
            if match:
                prefix = match.group(1)
                base_num = int(match.group(2))
                new_num = base_num + 1000 + index
                full.append(f"{prefix}{new_num}\n")

        # Add preamble
        for line in self.preamble:
            full.append(f"{line.rstrip()}\n")

        # Add segment lines
        for line in segment.lines:
            full.append(f"{line.rstrip()}\n")

        # Ensure termination
        last_line = full[-1].strip() if full else ""
        if not re.search(r"M(?:30|02|2)(?!\d)", last_line):
            full.append("M30\n")

        # End with %
        full.append("%\n")

        return full
