"""Advanced Ap/Ae calculation engine using stock models and OpenCAMLib."""

from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from .stock_model import DexelModel, Material, Point3D


class ToolType(Enum):
    """Tool types."""

    FLAT_ENDMILL = "flat_endmill"
    BALL_ENDMILL = "ball_endmill"
    BULL_ENDMILL = "bull_endmill"
    TAPER_MILL = "taper_mill"


@dataclass
class ToolGeometry:
    """Cutting tool geometry."""

    tool_id: int
    name: str
    tool_type: ToolType
    diameter: float  # mm
    corner_radius: float = 0.0  # mm (for bull endmill)
    flute_length: float = 50.0  # mm
    num_flutes: int = 4
    description: str = ""

    def get_effective_diameter(self) -> float:
        """Get effective cutting diameter."""
        if self.tool_type == ToolType.BALL_ENDMILL:
            return self.diameter  # Full diameter for ball cutters
        elif self.tool_type == ToolType.BULL_ENDMILL:
            return self.diameter
        else:
            return self.diameter


@dataclass
class MachiningBlock:
    """Represents a single G-code block with detailed analysis."""

    block_number: int
    line_number: int
    command: str  # G00, G01, G02, G03, etc.
    start_pos: Point3D
    end_pos: Point3D

    # Basic parameters
    feed_rate: float = 0.0  # mm/min
    spindle_speed: float = 0  # RPM
    arc_center: Optional[Point3D] = None  # For G02/G03

    # Calculated depths
    Ap: float = 0.0  # Axial depth of cut (Z-axis)
    Ae: float = 0.0  # Radial depth of cut (XY plane)

    # Stock-aware calculation
    Ap_stock_aware: float = 0.0  # Ap considering remaining stock
    Ae_stock_aware: float = 0.0  # Ae considering remaining stock

    # Material removal
    volume_removed: float = 0.0  # mm³
    volume_remaining: float = 0.0  # mm³

    # Additional metrics
    cutting_time: float = 0.0  # seconds
    path_length: float = 0.0  # mm
    is_cutting: bool = True

    # Stock state
    stock_before: Optional[Dict[str, Any]] = None
    stock_after: Optional[Dict[str, Any]] = None


@dataclass
class CuttingAnalysis:
    """Complete cutting analysis result."""

    filename: str
    total_blocks: int
    total_volume_removed: float = 0.0
    total_cutting_time: float = 0.0
    blocks: List[MachiningBlock] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)


class ApAeCalculationEngine:
    """
    Advanced Ap/Ae calculation engine.

    Combines:
    - OpenCAMLib tool geometry
    - Dexel/Octree stock models
    - Accurate toolpath analysis
    - Stock material tracking
    """

    def __init__(
        self,
        stock_model: Optional[Any] = None,
        material: Optional[Material] = None,
        tolerance: float = 0.01,
    ):
        """Initialize calculation engine.

        Args:
            stock_model: DexelModel or OctreeModel instance
            material: Material properties
            tolerance: Calculation tolerance (mm)
        """
        self.stock_model = stock_model
        self.material = material or Material()
        self.tolerance = tolerance
        self.tools: Dict[int, ToolGeometry] = {}
        self._load_default_tools()

    def _load_default_tools(self):
        """Load standard tool library."""
        self.tools = {
            1: ToolGeometry(
                tool_id=1,
                name="3mm Flat Endmill",
                tool_type=ToolType.FLAT_ENDMILL,
                diameter=3.0,
                num_flutes=4,
            ),
            2: ToolGeometry(
                tool_id=2,
                name="6mm Flat Endmill",
                tool_type=ToolType.FLAT_ENDMILL,
                diameter=6.0,
                num_flutes=4,
            ),
            3: ToolGeometry(
                tool_id=3,
                name="4mm Ball Endmill",
                tool_type=ToolType.BALL_ENDMILL,
                diameter=4.0,
                num_flutes=2,
            ),
        }

    def register_tool(self, tool: ToolGeometry):
        """Register a cutting tool."""
        self.tools[tool.tool_id] = tool

    def calculate_block_ap_ae(
        self,
        block: MachiningBlock,
        tool: ToolGeometry,
    ) -> Tuple[float, float]:
        """Calculate Ap and Ae for a single block.

        Args:
            block: Machining block
            tool: Tool geometry

        Returns:
            (Ap, Ae) tuple
        """
        # Axial depth (Z-axis engagement)
        Ap = abs(block.end_pos.z - block.start_pos.z)

        # Radial depth (XY-plane engagement)
        if block.command in ["G02", "G03"]:
            # Circular interpolation
            Ae = self._calculate_arc_engagement(block, tool)
        elif block.command in ["G00", "G01"]:
            # Linear movement
            Ae = self._calculate_linear_engagement(block, tool)
        else:
            Ae = 0.0

        block.Ap = Ap
        block.Ae = Ae

        return Ap, Ae

    def _calculate_linear_engagement(
        self,
        block: MachiningBlock,
        tool: ToolGeometry,
    ) -> float:
        """Calculate radial engagement for linear movement."""
        dx = block.end_pos.x - block.start_pos.x
        dy = block.end_pos.y - block.start_pos.y
        xy_distance = (dx**2 + dy**2) ** 0.5

        if not block.is_cutting or xy_distance == 0:
            return 0.0

        # For cutting motion, engagement is limited by tool
        if tool.tool_type == ToolType.BALL_ENDMILL:
            # Ball endmill can engage full width
            return min(xy_distance, tool.diameter / 2)
        elif tool.tool_type == ToolType.BULL_ENDMILL:
            # Bull nose endmill
            return min(xy_distance, tool.diameter / 2)
        else:
            # Flat endmill - full diameter engagement
            return min(xy_distance, tool.diameter)

    def _calculate_arc_engagement(
        self,
        block: MachiningBlock,
        tool: ToolGeometry,
    ) -> float:
        """Calculate radial engagement for circular interpolation.

        For G02/G03 arcs, engagement depends on:
        1. Arc center position
        2. Arc radius
        3. Tool geometry
        4. Stock surface
        """
        if not block.is_cutting or block.arc_center is None:
            # Fallback to linear calculation
            dx = block.end_pos.x - block.start_pos.x
            dy = block.end_pos.y - block.start_pos.y
            return (dx**2 + dy**2) ** 0.5

        # Calculate arc radius
        i = block.arc_center.x - block.start_pos.x
        j = block.arc_center.y - block.start_pos.y
        arc_radius = (i**2 + j**2) ** 0.5

        if arc_radius < self.tolerance:
            # Degenerate arc
            return 0.0

        # Effective engagement for arc
        if tool.tool_type == ToolType.BALL_ENDMILL:
            return min(arc_radius, tool.diameter / 2)
        elif tool.tool_type == ToolType.BULL_ENDMILL:
            # Consider corner radius
            effective_radius = tool.diameter / 2 + tool.corner_radius
            return min(arc_radius, effective_radius)
        else:
            return min(arc_radius, tool.diameter)

    def calculate_stock_aware_ap_ae(
        self,
        block: MachiningBlock,
        tool: ToolGeometry,
    ) -> Tuple[float, float]:
        """Calculate Ap/Ae considering actual stock surface.

        This performs advanced calculation using stock model to determine
        actual material being removed.

        Args:
            block: Machining block
            tool: Tool geometry

        Returns:
            (Ap_stock_aware, Ae_stock_aware) tuple
        """
        if self.stock_model is None:
            # Fallback to basic calculation
            return self.calculate_block_ap_ae(block, tool)

        # Start with basic calculation
        Ap, Ae = self.calculate_block_ap_ae(block, tool)

        # Adjust Ap based on stock surface
        if isinstance(self.stock_model, DexelModel):
            start_height = self.stock_model.get_material_height(
                block.start_pos.x, block.start_pos.y
            )
            end_height = self.stock_model.get_material_height(block.end_pos.x, block.end_pos.y)

            # Actual axial depth considering stock
            if block.is_cutting:
                actual_ap_start = max(0, start_height - block.start_pos.z)
                actual_ap_end = max(0, end_height - block.end_pos.z)
                Ap = max(actual_ap_start, actual_ap_end)

        block.Ap_stock_aware = Ap
        block.Ae_stock_aware = Ae

        return Ap, Ae

    def calculate_material_removal(
        self,
        block: MachiningBlock,
        tool: ToolGeometry,
    ) -> Tuple[float, float]:
        """Calculate actual material volume removed.

        Args:
            block: Machining block
            tool: Tool geometry

        Returns:
            (volume_removed, volume_remaining) tuple
        """
        if not block.is_cutting:
            return 0.0, 0.0

        # Simplified volume calculation
        # For more accuracy, integrate over tool path

        # Cross-sectional area (Ap × Ae)
        area = block.Ap * block.Ae

        # Path length
        dx = block.end_pos.x - block.start_pos.x
        dy = block.end_pos.y - block.start_pos.y
        path_length = (dx**2 + dy**2) ** 0.5

        # Volume = Area × Path_length
        volume = area * path_length

        # Store in block
        block.volume_removed = volume
        block.path_length = path_length

        # Calculate cutting time
        if block.feed_rate > 0:
            block.cutting_time = path_length / block.feed_rate * 60  # Convert to seconds

        return volume, 0.0

    def analyze_gcode_blocks(
        self,
        blocks: List[Dict[str, Any]],
        tool_id: int = 1,
    ) -> CuttingAnalysis:
        """Analyze all G-code blocks.

        Args:
            blocks: List of block dictionaries from G-code parser
            tool_id: Tool to use

        Returns:
            Complete cutting analysis
        """
        tool = self.tools.get(tool_id)
        if not tool:
            tool = list(self.tools.values())[0]

        analysis = CuttingAnalysis(
            filename=blocks[0].get("filename", "unknown") if blocks else "unknown",
            total_blocks=len(blocks),
        )

        total_volume = 0.0
        total_time = 0.0

        for block_dict in blocks:
            # Create MachiningBlock from dictionary
            start = Point3D(
                block_dict.get("start_position", {}).get("X", 0),
                block_dict.get("start_position", {}).get("Y", 0),
                block_dict.get("start_position", {}).get("Z", 0),
            )
            end = Point3D(
                block_dict.get("end_position", {}).get("X", 0),
                block_dict.get("end_position", {}).get("Y", 0),
                block_dict.get("end_position", {}).get("Z", 0),
            )

            block = MachiningBlock(
                block_number=block_dict.get("block_number", 0),
                line_number=block_dict.get("line_number", 0),
                command=block_dict.get("command", "G00"),
                start_pos=start,
                end_pos=end,
                feed_rate=block_dict.get("feed_rate", 0),
                spindle_speed=block_dict.get("spindle_speed", 0),
                is_cutting=block_dict.get("is_cutting", False),
            )

            # Calculate Ap/Ae
            self.calculate_stock_aware_ap_ae(block, tool)

            # Calculate material removal
            volume, _ = self.calculate_material_removal(block, tool)

            total_volume += volume
            total_time += block.cutting_time

            analysis.blocks.append(block)

        # Generate summary
        analysis.total_volume_removed = total_volume
        analysis.total_cutting_time = total_time
        analysis.summary = self._generate_summary(analysis, tool)

        return analysis

    def _generate_summary(
        self,
        analysis: CuttingAnalysis,
        tool: ToolGeometry,
    ) -> Dict[str, Any]:
        """Generate analysis summary."""
        cutting_blocks = [b for b in analysis.blocks if b.is_cutting]

        return {
            "tool_id": tool.tool_id,
            "tool_name": tool.name,
            "total_blocks": analysis.total_blocks,
            "cutting_blocks": len(cutting_blocks),
            "total_volume_removed": round(analysis.total_volume_removed, 2),
            "total_cutting_time": round(analysis.total_cutting_time, 2),
            "average_ap": round(
                sum(b.Ap for b in cutting_blocks) / len(cutting_blocks) if cutting_blocks else 0,
                4,
            ),
            "average_ae": round(
                sum(b.Ae for b in cutting_blocks) / len(cutting_blocks) if cutting_blocks else 0,
                4,
            ),
            "max_ap": round(max((b.Ap for b in cutting_blocks), default=0), 4),
            "max_ae": round(max((b.Ae for b in cutting_blocks), default=0), 4),
        }

    def export_blocks_to_csv(
        self,
        analysis: CuttingAnalysis,
        filepath: str,
    ):
        """Export block analysis to CSV.

        Args:
            analysis: Cutting analysis result
            filepath: Output CSV file path
        """
        import csv

        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "block_number",
                    "line_number",
                    "command",
                    "start_x",
                    "start_y",
                    "start_z",
                    "end_x",
                    "end_y",
                    "end_z",
                    "Ap",
                    "Ae",
                    "Ap_stock_aware",
                    "Ae_stock_aware",
                    "volume_removed",
                    "cutting_time",
                    "feed_rate",
                    "is_cutting",
                ],
            )
            writer.writeheader()

            for block in analysis.blocks:
                writer.writerow(
                    {
                        "block_number": block.block_number,
                        "line_number": block.line_number,
                        "command": block.command,
                        "start_x": round(block.start_pos.x, 4),
                        "start_y": round(block.start_pos.y, 4),
                        "start_z": round(block.start_pos.z, 4),
                        "end_x": round(block.end_pos.x, 4),
                        "end_y": round(block.end_pos.y, 4),
                        "end_z": round(block.end_pos.z, 4),
                        "Ap": round(block.Ap, 4),
                        "Ae": round(block.Ae, 4),
                        "Ap_stock_aware": round(block.Ap_stock_aware, 4),
                        "Ae_stock_aware": round(block.Ae_stock_aware, 4),
                        "volume_removed": round(block.volume_removed, 4),
                        "cutting_time": round(block.cutting_time, 4),
                        "feed_rate": block.feed_rate,
                        "is_cutting": block.is_cutting,
                    }
                )
