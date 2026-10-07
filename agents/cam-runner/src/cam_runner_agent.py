"""CAM Runner Agent - Calculate cutting parameters using OpenCAMLib."""

from typing import Any, Dict, List, Tuple, Optional
import sys
from pathlib import Path
import numpy as np

# Add shared library to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

from core import BaseAgent, AnalysisResult
from utils import setup_logger

try:
    import opencamlib as ocl

    OPENCAMLIB_AVAILABLE = True
except ImportError:
    OPENCAMLIB_AVAILABLE = False

logger = setup_logger(__name__)


class CutterConfig:
    """Configuration for OpenCAMLib cutting tools."""

    def __init__(
        self,
        tool_id: int,
        name: str,
        cutter_type: str = "CylCutter",
        diameter: float = 6.0,
        length: float = 50.0,
    ):
        self.tool_id = tool_id
        self.name = name
        self.cutter_type = cutter_type  # CylCutter, BallCutter, BullCutter
        self.diameter = diameter
        self.length = length

    def create_ocl_cutter(self) -> Optional[Any]:
        """Create an OpenCAMLib cutter object."""
        if not OPENCAMLIB_AVAILABLE:
            return None

        try:
            if self.cutter_type == "CylCutter":
                return ocl.CylCutter(self.diameter, self.length)
            elif self.cutter_type == "BallCutter":
                return ocl.BallCutter(self.diameter, self.length)
            elif self.cutter_type == "BullCutter":
                # BullCutter(diameter, corner_radius, length)
                return ocl.BullCutter(self.diameter, self.diameter / 4, self.length)
            else:
                logger.warning(f"Unknown cutter type: {self.cutter_type}, using CylCutter")
                return ocl.CylCutter(self.diameter, self.length)
        except Exception as e:
            logger.error(f"Error creating cutter: {e}")
            return None


class CuttingPath:
    """Represents a tool path with cutting analysis using OpenCAMLib."""

    def __init__(
        self,
        start: Tuple[float, float, float],
        end: Tuple[float, float, float],
        cutter: CutterConfig,
        is_cutting: bool = True,
        command: str = "G01",
        arc_offset: Optional[Dict[str, float]] = None,
    ):
        self.start = start  # (x, y, z)
        self.end = end  # (x, y, z)
        self.cutter = cutter
        self.is_cutting = is_cutting
        self.command = command  # G01, G02, G03, etc.
        self.arc_offset = arc_offset or {}  # I, J, K for arcs
        self._analyze_cutting_engagement()

    def _analyze_cutting_engagement(self):
        """Analyze cutting engagement using tool geometry."""
        # Axial depth (Z-axis movement)
        self.Ap = abs(self.end[2] - self.start[2])

        # Radial depth (XY plane movement)
        if self.command in ["G02", "G03"]:
            # Arc movement - calculate engagement based on arc radius
            self.Ae = self._calculate_arc_engagement()
        else:
            # Linear movement - engagement is XY distance
            self.Ae = self._calculate_linear_engagement()

        # Total path length (3D)
        dx = self.end[0] - self.start[0]
        dy = self.end[1] - self.start[1]
        dz = self.end[2] - self.start[2]
        self.length = (dx**2 + dy**2 + dz**2) ** 0.5

    def _calculate_linear_engagement(self) -> float:
        """Calculate engagement for linear movement (G01, G00)."""
        dx = self.end[0] - self.start[0]
        dy = self.end[1] - self.start[1]
        xy_distance = (dx**2 + dy**2) ** 0.5

        if not self.is_cutting or xy_distance == 0:
            return 0

        # For linear movement, engagement is limited by tool diameter
        if self.cutter.cutter_type == "BallCutter":
            return min(xy_distance, self.cutter.diameter / 2)
        elif self.cutter.cutter_type == "BullCutter":
            return min(xy_distance, self.cutter.diameter / 2)
        else:  # CylCutter
            return min(xy_distance, self.cutter.diameter)

    def _calculate_arc_engagement(self) -> float:
        """Calculate engagement for arc movement (G02, G03).

        For arcs, Ae depends on:
        1. Arc radius (from center offset I, J)
        2. Tool diameter
        3. Arc sweep angle
        """
        if not self.is_cutting:
            return 0

        # Get arc center offset
        i = self.arc_offset.get("I", 0)
        j = self.arc_offset.get("J", 0)

        # Calculate arc center position
        # arc_center_x = self.start[0] + i  # Reserved for future use
        # arc_center_y = self.start[1] + j  # Reserved for future use

        # Calculate arc radius
        arc_radius = (i**2 + j**2) ** 0.5

        if arc_radius == 0:
            # Degenerate arc (point), treat as linear
            return self._calculate_linear_engagement()

        # For arc movement, Ae is affected by:
        # 1. How deep the tool plunges into the arc
        # 2. Tool diameter
        # In simplified CAM analysis, we use the arc radius as a measure
        # of radial engagement

        if self.cutter.cutter_type == "BallCutter":
            # Ball cutter engagement in arc
            return min(arc_radius, self.cutter.diameter / 2)
        elif self.cutter.cutter_type == "BullCutter":
            return min(arc_radius, self.cutter.diameter / 2)
        else:  # CylCutter
            # For flat endmill in arc, radial engagement is min(arc_radius, tool_diameter)
            return min(arc_radius, self.cutter.diameter)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start": {"x": self.start[0], "y": self.start[1], "z": self.start[2]},
            "end": {"x": self.end[0], "y": self.end[1], "z": self.end[2]},
            "tool_id": self.cutter.tool_id,
            "tool_name": self.cutter.name,
            "is_cutting": self.is_cutting,
            "Ap": round(self.Ap, 4),  # Axial depth of cut
            "Ae": round(self.Ae, 4),  # Radial depth of cut
            "length": round(self.length, 4),
        }


class CAMRunnerAgent(BaseAgent):
    """Agent for calculating cutting parameters using OpenCAMLib."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the CAM runner agent.

        Args:
            config: Configuration dictionary with tool definitions
        """
        super().__init__(name="cam-runner", config=config or {})
        self.tools: Dict[int, CutterConfig] = {}
        self._load_default_tools()
        self.opencamlib_available = OPENCAMLIB_AVAILABLE

        if not self.opencamlib_available:
            logger.warning("OpenCAMLib not available, using simplified cutting calculations")

    def _load_default_tools(self):
        """Load default tool library."""
        # Default tools - configurable via pyproject.toml or config files
        self.tools = {
            1: CutterConfig(
                tool_id=1,
                name="3mm Endmill",
                cutter_type="CylCutter",
                diameter=3.0,
                length=50.0,
            ),
            2: CutterConfig(
                tool_id=2,
                name="6mm Endmill",
                cutter_type="CylCutter",
                diameter=6.0,
                length=50.0,
            ),
            3: CutterConfig(
                tool_id=3,
                name="4mm Ball Nose",
                cutter_type="BallCutter",
                diameter=4.0,
                length=50.0,
            ),
            4: CutterConfig(
                tool_id=4,
                name="8mm Bull Mill",
                cutter_type="BullCutter",
                diameter=8.0,
                length=50.0,
            ),
        }

    def process(self, input_data: Any) -> Dict[str, Any]:
        """Process tool path data using OpenCAMLib analysis.

        Args:
            input_data: Tool path data or G-code result

        Returns:
            Analysis result
        """
        try:
            result = self.analyze_gcode_paths(input_data)
            return result.to_dict()
        except Exception as e:
            logger.error(f"Error processing tool paths: {e}")
            return AnalysisResult(
                status="error",
                message=f"Failed to process tool paths: {str(e)}",
                errors=[str(e)],
            ).to_dict()

    def analyze_gcode_paths(
        self,
        gcode_data: Dict[str, Any],
        rapid_feed_rate: float = 5000.0,  # mm/min, typical rapid traverse speed
        tool_change_time: float = 8.0,  # seconds per tool change
    ) -> AnalysisResult:
        """Analyze G-code paths and calculate cutting parameters using OpenCAMLib.

        Args:
            gcode_data: G-code analysis result with gcode_blocks
            rapid_feed_rate: Rapid traverse feed rate in mm/min (default: 5000)
            tool_change_time: Average time for tool change in seconds (default: 8)

        Returns:
            Analysis result with cutting parameters and cycle time
        """
        try:
            if not isinstance(gcode_data, dict):
                raise ValueError("Invalid input: expected dictionary")

            # Extract G-code blocks from the gcode_data
            gcode_blocks = gcode_data.get("gcode_blocks", [])
            if not gcode_blocks:
                gcode_blocks = gcode_data.get("commands", [])

            # Extract timing-related data from gcode_data
            cutting_distance = gcode_data.get("cutting_distance", 0)
            rapid_distance = gcode_data.get("rapid_distance", 0)
            feed_rate = gcode_data.get("feed_rate", 1000)  # mm/min
            dwell_time = gcode_data.get("dwell_time", 0)  # seconds

            # Count tool changes (look for T commands or M06)
            tool_change_count = 0
            seen_tools = set()
            for block in gcode_blocks:
                if isinstance(block, dict):
                    params = block.get("parameters", {})
                    if "T" in params:
                        tool_num = params["T"]
                        if tool_num not in seen_tools:
                            if seen_tools:  # Not the first tool
                                tool_change_count += 1
                            seen_tools.add(tool_num)

            # Use default tool
            cutter = self.tools.get(2)  # 6mm endmill by default

            # Convert blocks to cutting paths
            cutting_paths = []
            for block in gcode_blocks:
                if isinstance(block, dict):
                    # Extract start and end positions
                    # Support both flat (start_x, start_y, start_z) and nested (start_position) formats
                    if "start_position" in block:
                        start_pos = block["start_position"]
                        start = (
                            start_pos.get("X", start_pos.get("x", 0)),
                            start_pos.get("Y", start_pos.get("y", 0)),
                            start_pos.get("Z", start_pos.get("z", 0)),
                        )
                    else:
                        start = (
                            block.get("start_x", 0),
                            block.get("start_y", 0),
                            block.get("start_z", 0),
                        )

                    if "end_position" in block:
                        end_pos = block["end_position"]
                        end = (
                            end_pos.get("X", end_pos.get("x", 0)),
                            end_pos.get("Y", end_pos.get("y", 0)),
                            end_pos.get("Z", end_pos.get("z", 0)),
                        )
                    else:
                        end = (
                            block.get("end_x", 0),
                            block.get("end_y", 0),
                            block.get("end_z", 0),
                        )

                    is_cutting = block.get("is_cutting", True)
                    command = block.get("command", "G01")

                    # Extract arc offset (I, J, K) for G02/G03 commands
                    arc_offset = {}
                    if command in ["G02", "G03"]:
                        parameters = block.get("parameters", {})
                        if "I" in parameters:
                            arc_offset["I"] = parameters["I"]
                        if "J" in parameters:
                            arc_offset["J"] = parameters["J"]
                        if "K" in parameters:
                            arc_offset["K"] = parameters["K"]

                    path = CuttingPath(start, end, cutter, is_cutting, command, arc_offset)
                    cutting_paths.append(path)

            # Analyze cutting parameters
            if not cutting_paths:
                return AnalysisResult(
                    status="warning",
                    message="No valid cutting paths found",
                    data={
                        "summary": {
                            "total_paths": 0,
                            "cutting_segments": 0,
                            "tool_id": cutter.tool_id,
                            "tool_name": cutter.name,
                            "warning": "No G-code blocks provided",
                        },
                        "cutting_paths": 0,
                    },
                )

            cutting_segments = [p for p in cutting_paths if p.is_cutting]

            # Calculate cycle time components
            # Cutting time: distance / feed_rate (mm / mm/min = min, convert to seconds)
            cutting_time_sec = (cutting_distance / feed_rate * 60) if feed_rate > 0 else 0

            # Rapid time: rapid_distance / rapid_feed_rate
            rapid_time_sec = (rapid_distance / rapid_feed_rate * 60) if rapid_feed_rate > 0 else 0

            # Tool change time
            tool_change_total_sec = tool_change_count * tool_change_time

            # Total cycle time
            total_cycle_time_sec = (
                cutting_time_sec + rapid_time_sec + dwell_time + tool_change_total_sec
            )

            # Build cycle time breakdown
            cycle_time = {
                "cutting_time_sec": round(cutting_time_sec, 2),
                "rapid_time_sec": round(rapid_time_sec, 2),
                "dwell_time_sec": round(dwell_time, 2),
                "tool_change_time_sec": round(tool_change_total_sec, 2),
                "total_cycle_time_sec": round(total_cycle_time_sec, 2),
                "total_cycle_time_min": round(total_cycle_time_sec / 60, 2),
                "tool_change_count": tool_change_count,
                "feed_rate_used": feed_rate,
                "rapid_feed_rate_used": rapid_feed_rate,
            }

            if cutting_segments:
                ap_values = [p.Ap for p in cutting_segments]
                ae_values = [p.Ae for p in cutting_segments]

                summary = {
                    "total_paths": len(cutting_paths),
                    "cutting_segments": len(cutting_segments),
                    "tool_id": cutter.tool_id,
                    "tool_name": cutter.name,
                    "cutter_type": cutter.cutter_type,
                    "cutter_diameter": cutter.diameter,
                    "ap_max": round(max(ap_values), 4),
                    "ap_min": round(min(ap_values), 4),
                    "ap_avg": round(np.mean(ap_values), 4),
                    "ap_total": round(sum(ap_values), 4),
                    "ae_max": round(max(ae_values), 4),
                    "ae_min": round(min(ae_values), 4),
                    "ae_avg": round(np.mean(ae_values), 4),
                    "ae_total": round(sum(ae_values), 4),
                    "cutting_distance": round(cutting_distance, 2),
                    "rapid_distance": round(rapid_distance, 2),
                }
            else:
                summary = {
                    "total_paths": len(cutting_paths),
                    "cutting_segments": 0,
                    "tool_id": cutter.tool_id,
                    "tool_name": cutter.name,
                    "cutting_distance": round(cutting_distance, 2),
                    "rapid_distance": round(rapid_distance, 2),
                    "warning": "No cutting movements found",
                }

            return AnalysisResult(
                status="success",
                message="Successfully analyzed cutting paths with cycle time calculation",
                data={
                    "summary": summary,
                    "cycle_time": cycle_time,
                    "paths": [p.to_dict() for p in cutting_paths[:20]],
                    "total_segments": len(cutting_paths),
                },
            )

        except Exception as e:
            logger.error(f"Error analyzing paths: {e}")
            return AnalysisResult(
                status="error",
                message=f"Failed to analyze paths: {str(e)}",
                errors=[str(e)],
            )

    def get_tool(self, tool_id: int) -> Optional[CutterConfig]:
        """Get a tool by ID.

        Args:
            tool_id: Tool ID

        Returns:
            CutterConfig or None
        """
        return self.tools.get(tool_id)

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools.

        Returns:
            List of tool dictionaries
        """
        return [
            {
                "tool_id": tool.tool_id,
                "name": tool.name,
                "cutter_type": tool.cutter_type,
                "diameter": tool.diameter,
                "length": tool.length,
            }
            for tool in self.tools.values()
        ]
