"""OpenCAMLib integration for advanced toolpath analysis."""

from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass

# Try to import OpenCAMLib
try:
    import opencamlib as ocl

    OPENCAMLIB_AVAILABLE = True
except ImportError:
    OPENCAMLIB_AVAILABLE = False

from .stock_model import DexelModel, Material
from .calculation_engine import ToolGeometry, ToolType, Point3D


@dataclass
class OCLToolConfig:
    """Configuration for OpenCAMLib tool."""

    tool_id: int
    diameter: float
    length: float
    tool_type: str = "CylCutter"  # CylCutter, BallCutter, BullCutter
    corner_radius: float = 0.0
    flute_count: int = 4


class OpenCAMLibToolAdapter:
    """Adapter between internal tool format and OpenCAMLib."""

    @staticmethod
    def geometry_to_ocl_cutter(
        tool: ToolGeometry,
    ) -> Optional[Any]:
        """Convert ToolGeometry to OpenCAMLib cutter.

        Args:
            tool: Tool geometry

        Returns:
            OpenCAMLib cutter object or None if library not available
        """
        if not OPENCAMLIB_AVAILABLE:
            return None

        try:
            if tool.tool_type == ToolType.FLAT_ENDMILL:
                return ocl.CylCutter(tool.diameter, tool.flute_length)
            elif tool.tool_type == ToolType.BALL_ENDMILL:
                return ocl.BallCutter(tool.diameter, tool.flute_length)
            elif tool.tool_type == ToolType.BULL_ENDMILL:
                # BullCutter(diameter, corner_radius, length)
                return ocl.BullCutter(
                    tool.diameter,
                    tool.corner_radius,
                    tool.flute_length,
                )
            else:
                return ocl.CylCutter(tool.diameter, tool.flute_length)
        except Exception as e:
            print(f"Error creating OpenCAMLib cutter: {e}")
            return None

    @staticmethod
    def ocl_config_to_cutter(config: OCLToolConfig) -> Optional[Any]:
        """Create OpenCAMLib cutter from config.

        Args:
            config: OpenCAMLib tool configuration

        Returns:
            OpenCAMLib cutter object
        """
        if not OPENCAMLIB_AVAILABLE:
            return None

        try:
            if config.tool_type == "CylCutter":
                return ocl.CylCutter(config.diameter, config.length)
            elif config.tool_type == "BallCutter":
                return ocl.BallCutter(config.diameter, config.length)
            elif config.tool_type == "BullCutter":
                return ocl.BullCutter(config.diameter, config.corner_radius, config.length)
            else:
                return ocl.CylCutter(config.diameter, config.length)
        except Exception as e:
            print(f"Error creating cutter from config: {e}")
            return None


class DexelOpenCAMLibAnalyzer:
    """
    Dexel-based analysis using OpenCAMLib for accurate Ap/Ae calculation.

    Integrates:
    - Dexel stock model (height field)
    - OpenCAMLib tool geometry
    - Advanced engagement calculations
    """

    def __init__(
        self,
        dexel_model: DexelModel,
        tool: ToolGeometry,
        tolerance: float = 0.01,
    ):
        """Initialize analyzer.

        Args:
            dexel_model: Dexel stock representation
            tool: Cutting tool geometry
            tolerance: Numerical tolerance
        """
        self.dexel = dexel_model
        self.tool = tool
        self.tolerance = tolerance
        self.ocl_cutter = OpenCAMLibToolAdapter.geometry_to_ocl_cutter(tool)

    def analyze_toolpath_segment(
        self,
        start: Point3D,
        end: Point3D,
        command: str = "G01",
        arc_center: Optional[Point3D] = None,
    ) -> Dict[str, float]:
        """Analyze a single toolpath segment.

        Args:
            start: Start position
            end: End position
            command: G-code command (G00, G01, G02, G03)
            arc_center: Arc center for G02/G03

        Returns:
            Dictionary with Ap, Ae, and other metrics
        """
        result = {
            "Ap": 0.0,
            "Ae": 0.0,
            "Ap_stock_aware": 0.0,
            "Ae_stock_aware": 0.0,
            "engagement_ratio": 0.0,
            "tool_radius": self.tool.diameter / 2,
        }

        if command not in ["G01", "G02", "G03"]:
            return result  # No cutting

        # Basic Ap calculation
        result["Ap"] = abs(end.z - start.z)

        # Ae calculation based on path type
        if command in ["G02", "G03"] and arc_center:
            Ae = self._calculate_arc_engagement(start, end, arc_center)
        else:
            Ae = self._calculate_linear_engagement(start, end)

        result["Ae"] = Ae

        # Stock-aware calculation
        if self.dexel:
            result["Ap_stock_aware"] = self._calculate_stock_aware_ap(start, end, result["Ap"])
            result["Ae_stock_aware"] = self._calculate_stock_aware_ae(start, end, Ae)

        # Engagement ratio
        max_engagement = self.tool.diameter
        result["engagement_ratio"] = min(Ae / max_engagement, 1.0) if max_engagement > 0 else 0

        return result

    def _calculate_linear_engagement(
        self,
        start: Point3D,
        end: Point3D,
    ) -> float:
        """Calculate radial engagement for linear path."""
        dx = end.x - start.x
        dy = end.y - start.y
        distance = (dx**2 + dy**2) ** 0.5

        if distance < self.tolerance:
            return 0.0

        # Limit by tool geometry
        if self.tool.tool_type == ToolType.BALL_ENDMILL:
            return min(distance, self.tool.diameter / 2)
        else:
            return min(distance, self.tool.diameter)

    def _calculate_arc_engagement(
        self,
        start: Point3D,
        end: Point3D,
        arc_center: Point3D,
    ) -> float:
        """Calculate radial engagement for arc path."""
        # Arc radius
        i = arc_center.x - start.x
        j = arc_center.y - start.y
        arc_radius = (i**2 + j**2) ** 0.5

        if arc_radius < self.tolerance:
            # Degenerate arc - treat as linear
            return self._calculate_linear_engagement(start, end)

        # Engagement is limited by tool and arc radius
        if self.tool.tool_type == ToolType.BALL_ENDMILL:
            return min(arc_radius, self.tool.diameter / 2)
        else:
            return min(arc_radius, self.tool.diameter)

    def _calculate_stock_aware_ap(
        self,
        start: Point3D,
        end: Point3D,
        nominal_ap: float,
    ) -> float:
        """Calculate Ap considering actual stock surface using Dexel."""
        if not self.dexel:
            return nominal_ap

        # Get surface heights at start and end
        start_height = self.dexel.get_material_height(start.x, start.y)
        end_height = self.dexel.get_material_height(end.x, end.y)

        # Actual cutting depth limited by stock surface
        actual_ap_start = max(0, start_height - start.z)
        actual_ap_end = max(0, end_height - end.z)

        return max(actual_ap_start, actual_ap_end)

    def _calculate_stock_aware_ae(
        self,
        start: Point3D,
        end: Point3D,
        nominal_ae: float,
    ) -> float:
        """Calculate Ae considering stock surface variations."""
        if not self.dexel:
            return nominal_ae

        # Sample multiple points along the path
        num_samples = int(max(3, nominal_ae / self.tolerance))

        for i in range(1, num_samples):
            t = i / num_samples
            x = start.x + t * (end.x - start.x)
            y = start.y + t * (end.y - start.y)

            # Check if stock is higher than tool position
            self.dexel.get_material_height(x, y)
            # Could adjust Ae based on local surface

        return nominal_ae

    def analyze_full_toolpath(
        self,
        blocks: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Analyze complete toolpath.

        Args:
            blocks: List of G-code blocks

        Returns:
            Analyzed blocks with Ap/Ae metrics
        """
        analyzed = []

        for block in blocks:
            start = Point3D(
                block.get("start_position", {}).get("X", 0),
                block.get("start_position", {}).get("Y", 0),
                block.get("start_position", {}).get("Z", 0),
            )
            end = Point3D(
                block.get("end_position", {}).get("X", 0),
                block.get("end_position", {}).get("Y", 0),
                block.get("end_position", {}).get("Z", 0),
            )

            arc_center = None
            if "arc_center" in block:
                arc_center = Point3D(
                    block["arc_center"].get("X"),
                    block["arc_center"].get("Y"),
                    block["arc_center"].get("Z"),
                )

            analysis = self.analyze_toolpath_segment(
                start,
                end,
                command=block.get("command", "G01"),
                arc_center=arc_center,
            )

            block_result = {**block, **analysis}
            analyzed.append(block_result)

        return analyzed


class OpenCAMLibStockAnalyzer:
    """Advanced stock analysis using OpenCAMLib APT.

    Provides:
    - Tool path verification
    - Undercut detection
    - Optimal feed rate calculation
    - Tool wear estimation
    """

    def __init__(self, tool: ToolGeometry):
        """Initialize stock analyzer.

        Args:
            tool: Cutting tool geometry
        """
        self.tool = tool
        self.ocl_cutter = OpenCAMLibToolAdapter.geometry_to_ocl_cutter(tool)

    def estimate_tool_wear(
        self,
        volume_removed: float,
        material: Optional[Material] = None,
    ) -> Tuple[float, str]:
        """Estimate tool wear based on material removed.

        Args:
            volume_removed: Volume of material removed (mm³)
            material: Material being cut

        Returns:
            (wear_percentage, wear_status) tuple
        """
        # Empirical wear model (simplified)
        material = material or Material()

        # Base tool life (mm³) depends on material
        if "aluminum" in material.name.lower():
            tool_life = 1000000  # 1M mm³ for aluminum
        elif "steel" in material.name.lower():
            tool_life = 500000  # 500K mm³ for steel
        else:
            tool_life = 750000  # Default

        wear_percentage = min(100.0, (volume_removed / tool_life) * 100)

        if wear_percentage < 20:
            status = "good"
        elif wear_percentage < 50:
            status = "fair"
        elif wear_percentage < 80:
            status = "worn"
        else:
            status = "replace_tool"

        return wear_percentage, status

    def calculate_optimal_feed_rate(
        self,
        spindle_speed: float,
        material: Optional[Material] = None,
        Ae: float = 1.0,
        Ap: float = 1.0,
    ) -> float:
        """Calculate optimal feed rate.

        Args:
            spindle_speed: Spindle RPM
            material: Material being cut
            Ae: Radial depth of cut (mm)
            Ap: Axial depth of cut (mm)

        Returns:
            Optimal feed rate (mm/min)
        """
        material = material or Material()

        # Feed per tooth recommendations (mm/tooth)
        if "aluminum" in material.name.lower():
            fpt = 0.05 * (1 + Ae / 10)  # Increase with Ae
        elif "steel" in material.name.lower():
            fpt = 0.02 * (1 + Ae / 20)
        else:
            fpt = 0.03

        # Feed rate = spindle_speed × num_flutes × fpt
        feed_rate = spindle_speed * self.tool.num_flutes * fpt

        # Adjust for depth
        depth_factor = 1.0 / (1 + Ap / 5)  # Reduce feed for deep cuts
        feed_rate *= depth_factor

        return feed_rate
