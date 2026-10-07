"""G-code Parser Agent - Parse and analyze G-code files."""

from typing import Any, Dict
import sys
from pathlib import Path

# Add shared library to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

from core import BaseAgent, AnalysisResult
from models import GCodeCommand, GCodeAnalysis
from utils import setup_logger

try:
    import gcodeparser
except ImportError:
    gcodeparser = None


logger = setup_logger(__name__)


class GcodeParserAgent(BaseAgent):
    """Agent for parsing and analyzing G-code files."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the G-code parser agent.

        Args:
            config: Configuration dictionary
        """
        super().__init__(name="gcode-parser", config=config or {})

        if gcodeparser is None:
            logger.warning("gcodeparser library not installed")

    def process(self, input_data: Any) -> Dict[str, Any]:
        """Process G-code input.

        Args:
            input_data: G-code text or file path

        Returns:
            Analysis result
        """
        try:
            # Check if input is a file path (not G-code content)
            # G-code content contains newlines, file paths don't
            is_file_path = (
                isinstance(input_data, str)
                and "\n" not in input_data
                and len(input_data) < 500  # File paths are short
            )

            if is_file_path:
                try:
                    path = Path(input_data)
                    if path.exists():
                        # Try UTF-8 first, then fallback to cp1252 (or other encodings)
                        try:
                            with open(input_data, "r", encoding="utf-8") as f:
                                gcode_text = f.read()
                        except UnicodeDecodeError:
                            with open(input_data, "r", encoding="cp1252") as f:
                                gcode_text = f.read()
                        filename = path.name
                    else:
                        # Path doesn't exist, treat as G-code content
                        gcode_text = input_data
                        filename = "inline_gcode"
                except OSError:
                    # Invalid path characters, treat as G-code content
                    gcode_text = input_data
                    filename = "inline_gcode"
            else:
                gcode_text = input_data
                filename = "inline_gcode"

            result = self.analyze_gcode(gcode_text, filename)
            return result.to_dict()

        except Exception as e:
            logger.error(f"Error processing G-code: {e}")
            return AnalysisResult(
                status="error",
                message=f"Failed to process G-code: {str(e)}",
                errors=[str(e)],
            ).to_dict()

    def analyze_gcode(self, gcode_text: str, filename: str = "gcode") -> AnalysisResult:
        """Analyze G-code text.

        Args:
            gcode_text: G-code content
            filename: Source filename

        Returns:
            Analysis result
        """
        try:
            if gcodeparser is None:
                return AnalysisResult(
                    status="error",
                    message="gcodeparser library not available",
                    errors=["gcodeparser is not installed"],
                )

            # First, do a pre-pass to extract coordinate-only lines
            # This handles lines like "X68 Y0" or "Z25" without explicit G codes
            raw_lines = gcode_text.split("\n")
            accumulated_pos = {"X": 0, "Y": 0, "Z": 0}  # Running position

            for raw_line in raw_lines:
                raw_line = raw_line.strip()
                if not raw_line or raw_line.startswith(";") or raw_line.startswith("("):
                    continue

                # Stop at first MOTION G command (G01, G02, G03)
                # These are the commands that need initial position
                if any(f"G0{code}" in raw_line for code in "123"):
                    break

                # Try to extract coordinates from N-lines before first motion command
                if raw_line.startswith("N"):
                    # Parse N line
                    parts = raw_line.split()
                    if len(parts) > 1:
                        try:
                            for part in parts[1:]:
                                if len(part) > 0 and part[0] in "XYZFSI":
                                    try:
                                        coord_val = float(part[1:])
                                        if part[0] in "XYZ":
                                            accumulated_pos[part[0]] = coord_val
                                    except ValueError:
                                        pass
                        except (ValueError, IndexError):
                            pass

            # Parse G-code using gcodeparser
            parsed_lines = list(gcodeparser.parse_gcode_lines(gcode_text))

            # Extract analysis data
            commands = []
            gcode_blocks = []  # New: block-level analysis

            # Map line index to raw line text for N-number extraction
            raw_lines = gcode_text.split("\n")

            total_distance = 0
            rapid_distance = 0
            cutting_distance = 0
            dwell_time = 0
            spindle_speed = 0
            feed_rate = 0

            # Track current position for Ap/Ae calculation
            # Use accumulated position from pre-pass
            current_pos = accumulated_pos.copy()

            block_num = 0
            current_g_code = "G00"  # Modal G command (default to G00)

            # Helper function to extract N-number from raw line
            def extract_n_number(line_text):
                """Extract N-number (program number) from G-code line."""
                line_text = line_text.strip()
                if line_text.startswith("N"):
                    try:
                        # Extract number after 'N'
                        parts = line_text.split()
                        n_str = parts[0][1:]  # Remove 'N' prefix
                        return int(n_str)
                    except (ValueError, IndexError):
                        pass
                return None

            for i, line in enumerate(parsed_lines):
                command = line.command
                params = line.params if line.params else {}
                original_line_number = (
                    line.line_index + 1
                )  # line_index is 0-based, convert to 1-based

                # Get raw line text for N-number extraction
                raw_line = raw_lines[line.line_index] if line.line_index < len(raw_lines) else ""
                n_number = extract_n_number(raw_line)

                # Extract G-code command - command is a tuple (type, code)
                g_code = None
                if isinstance(command, tuple) and command[0] == "G":
                    g_code = f"G{int(command[1]):02d}"
                    current_g_code = g_code  # Update modal G command
                elif isinstance(command, tuple) and command[0] == "M":
                    # Store M commands but don't create blocks yet
                    if "S" in params:
                        spindle_speed = params["S"]
                    if "F" in params:
                        feed_rate = params["F"]
                    continue
                elif "G" in params:
                    g_code = f"G{int(params['G']):02d}"
                    current_g_code = g_code
                elif len(params) > 0:
                    # Coordinate-only line (X, Y, Z without explicit G code)
                    # Use current modal G command
                    g_code = current_g_code
                else:
                    continue

                # Update spindle speed and feed rate
                if "S" in params:
                    spindle_speed = params["S"]
                if "F" in params:
                    feed_rate = params["F"]

                # Get target position (handle coordinate-only blocks)
                target_pos = {
                    "X": params.get("X", current_pos["X"]),
                    "Y": params.get("Y", current_pos["Y"]),
                    "Z": params.get("Z", current_pos["Z"]),
                }

                # Only create a block if there's actual movement
                has_movement = (
                    target_pos["X"] != current_pos["X"]
                    or target_pos["Y"] != current_pos["Y"]
                    or target_pos["Z"] != current_pos["Z"]
                )

                if has_movement:
                    block_num += 1

                    # Calculate Ap (axial depth - Z movement)
                    Ap = abs(target_pos["Z"] - current_pos["Z"])

                    # Calculate Ae (radial depth - XY movement)
                    dx = target_pos["X"] - current_pos["X"]
                    dy = target_pos["Y"] - current_pos["Y"]
                    Ae = (dx**2 + dy**2) ** 0.5 if (dx or dy) else 0

                    # Calculate total distance
                    dz = target_pos["Z"] - current_pos["Z"]
                    distance = (dx**2 + dy**2 + dz**2) ** 0.5

                    # Classify movement
                    is_cutting = g_code in ["G01", "G02", "G03"]
                    if g_code == "G00":
                        rapid_distance += distance
                    elif is_cutting:
                        cutting_distance += distance
                    elif g_code == "G04":
                        dwell_time += params.get("P", params.get("X", 0))

                    total_distance += distance

                    # Store command
                    commands.append(
                        GCodeCommand(
                            command=g_code,
                            parameters=params,
                            line_number=i,
                        )
                    )

                    # Store block-level data
                    gcode_blocks.append(
                        {
                            "block_number": block_num,
                            "n_number": n_number,  # Program number (N-code)
                            "line_number": original_line_number,
                            "original_line_number": original_line_number,
                            "command": g_code,
                            "parameters": {k: v for k, v in params.items()},
                            "start_position": current_pos.copy(),
                            "end_position": target_pos.copy(),
                            "Ap": round(Ap, 4),  # Axial depth of cut
                            "Ae": round(Ae, 4),  # Radial depth of cut
                            "distance": round(distance, 4),
                            "is_cutting": is_cutting,
                            "spindle_speed": spindle_speed,
                            "feed_rate": feed_rate,
                        }
                    )

                    # Update current position
                    current_pos = target_pos.copy()

            analysis = GCodeAnalysis(
                filename=filename,
                total_commands=len(commands),
                total_distance=total_distance,
                rapid_distance=rapid_distance,
                cutting_distance=cutting_distance,
                dwell_time=dwell_time,
                commands=commands,
                spindle_speed=spindle_speed,
                feed_rate=feed_rate,
            )

            return AnalysisResult(
                status="success",
                message=f"Successfully analyzed {filename}",
                data={
                    "filename": analysis.filename,
                    "total_commands": analysis.total_commands,
                    "total_distance": total_distance,
                    "rapid_distance": rapid_distance,
                    "cutting_distance": cutting_distance,
                    "dwell_time": dwell_time,
                    "spindle_speed": spindle_speed,
                    "feed_rate": feed_rate,
                    "gcode_blocks": gcode_blocks,  # New: block-level results
                },
            )

        except Exception as e:
            logger.error(f"Error analyzing G-code: {e}")
            return AnalysisResult(
                status="error",
                message=f"Failed to analyze G-code: {str(e)}",
                errors=[str(e)],
            )
