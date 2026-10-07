"""Advanced CAM Runner Agent with Dexel/Octree stock models and OpenCAMLib integration."""

from typing import Any, Dict, List, Optional
import sys
from pathlib import Path
import numpy as np

# Add shared library to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

from core import BaseAgent, AnalysisResult
from utils import setup_logger
from models import (
    ApAeCalculationEngine,
    CuttingAnalysis,
    ToolGeometry,
    ToolType,
    DexelModel,
    Material,
    DexelOpenCAMLibAnalyzer,
    OpenCAMLibStockAnalyzer,
)

logger = setup_logger(__name__)


class AdvancedCAMRunnerAgent(BaseAgent):
    """
    Advanced CAM Runner Agent with integrated stock modeling and OpenCAMLib.

    Features:
    - Dexel/Octree stock material models
    - Block-level Ap/Ae calculation with stock awareness
    - OpenCAMLib tool geometry integration
    - Material removal volume tracking
    - Tool wear estimation
    """

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the advanced CAM runner agent.

        Args:
            config: Configuration dictionary
        """
        super().__init__(name="advanced-cam-runner", config=config or {})

        self.calculation_engine = ApAeCalculationEngine()
        self.stock_model: Optional[DexelModel] = None
        self.dexel_analyzer: Optional[DexelOpenCAMLibAnalyzer] = None
        self.stock_analyzer: Optional[OpenCAMLibStockAnalyzer] = None

        # Load default stock configuration
        self._initialize_default_stock()
        self._register_tools()

    def _initialize_default_stock(self):
        """Initialize default stock model (Dexel)."""
        try:
            # Default stock: 100×100×50mm aluminum
            self.stock_model = DexelModel(
                x_min=0,
                x_max=100,
                y_min=0,
                y_max=100,
                z_min=0,
                z_max=50,
                resolution=1.0,
                material=Material(
                    density=2.7,
                    hardness=95,
                    name="Aluminum 6061",
                ),
            )
            logger.info("Initialized default Dexel stock model")
        except Exception as e:
            logger.warning(f"Failed to initialize stock model: {e}")

    def _register_tools(self):
        """Register standard cutting tools."""
        tools = [
            ToolGeometry(
                tool_id=1,
                name="3mm Flat Endmill",
                tool_type=ToolType.FLAT_ENDMILL,
                diameter=3.0,
                flute_length=50.0,
                num_flutes=4,
            ),
            ToolGeometry(
                tool_id=2,
                name="6mm Flat Endmill",
                tool_type=ToolType.FLAT_ENDMILL,
                diameter=6.0,
                flute_length=50.0,
                num_flutes=4,
            ),
            ToolGeometry(
                tool_id=3,
                name="4mm Ball Endmill",
                tool_type=ToolType.BALL_ENDMILL,
                diameter=4.0,
                flute_length=50.0,
                num_flutes=2,
            ),
            ToolGeometry(
                tool_id=4,
                name="8mm Bull Endmill",
                tool_type=ToolType.BULL_ENDMILL,
                diameter=8.0,
                corner_radius=2.0,
                flute_length=50.0,
                num_flutes=4,
            ),
        ]

        for tool in tools:
            self.calculation_engine.register_tool(tool)
            logger.debug(f"Registered tool: {tool.name}")

    def process(self, input_data: Any) -> Dict[str, Any]:
        """Process G-code data with advanced analysis.

        Args:
            input_data: G-code analysis result

        Returns:
            Analysis result with block-level Ap/Ae
        """
        try:
            result = self.analyze_gcode_with_stock_model(input_data)
            return result.to_dict() if hasattr(result, "to_dict") else result
        except Exception as e:
            logger.error(f"Error in advanced CAM analysis: {e}")
            return AnalysisResult(
                status="error",
                message=f"Failed advanced analysis: {str(e)}",
                errors=[str(e)],
            ).to_dict()

    def analyze_gcode_with_stock_model(
        self,
        gcode_data: Dict[str, Any],
        tool_id: int = 2,
        use_dexel_analysis: bool = True,
    ) -> Dict[str, Any]:
        """Analyze G-code with stock model integration.

        Args:
            gcode_data: G-code analysis result
            tool_id: Tool ID to use
            use_dexel_analysis: Use Dexel-based analysis

        Returns:
            Advanced analysis result
        """
        try:
            # Extract blocks from G-code data
            gcode_blocks = gcode_data.get("gcode_blocks", [])
            if not gcode_blocks:
                return {
                    "status": "warning",
                    "message": "No G-code blocks found",
                    "data": {},
                }

            # Get tool
            tool = self.calculation_engine.tools.get(tool_id)
            if not tool:
                tool = list(self.calculation_engine.tools.values())[0]
                logger.info(f"Tool {tool_id} not found, using {tool.name}")

            # Perform analysis
            if use_dexel_analysis and self.stock_model:
                return self._analyze_with_dexel(gcode_blocks, tool)
            else:
                return self._analyze_standard(gcode_blocks, tool)

        except Exception as e:
            logger.error(f"Error analyzing G-code: {e}")
            return {
                "status": "error",
                "message": str(e),
                "data": {},
            }

    def _analyze_standard(
        self,
        blocks: List[Dict[str, Any]],
        tool: ToolGeometry,
    ) -> Dict[str, Any]:
        """Standard analysis without stock model.

        Args:
            blocks: G-code blocks
            tool: Cutting tool

        Returns:
            Analysis result
        """
        analysis = self.calculation_engine.analyze_gcode_blocks(blocks, tool.tool_id)

        return {
            "status": "success",
            "message": "Standard Ap/Ae analysis completed",
            "analysis_type": "standard",
            "data": {
                "filename": analysis.filename,
                "total_blocks": analysis.total_blocks,
                "summary": analysis.summary,
                "blocks": [
                    {
                        "block_number": b.block_number,
                        "line_number": b.line_number,
                        "command": b.command,
                        "Ap": round(b.Ap, 4),
                        "Ae": round(b.Ae, 4),
                        "volume_removed": round(b.volume_removed, 4),
                        "cutting_time": round(b.cutting_time, 2),
                        "feed_rate": b.feed_rate,
                        "is_cutting": b.is_cutting,
                    }
                    for b in analysis.blocks
                ],
                "statistics": self._calculate_statistics(analysis),
            },
        }

    def _analyze_with_dexel(
        self,
        blocks: List[Dict[str, Any]],
        tool: ToolGeometry,
    ) -> Dict[str, Any]:
        """Analysis with Dexel stock model.

        Args:
            blocks: G-code blocks
            tool: Cutting tool

        Returns:
            Advanced analysis result
        """
        # Create Dexel analyzer
        analyzer = DexelOpenCAMLibAnalyzer(self.stock_model, tool)

        # Analyze blocks
        analyzed_blocks = analyzer.analyze_full_toolpath(blocks)

        # Get material machinability for dynamic feed rate adjustment
        material = self.stock_model.material if self.stock_model else None
        machinability = 1.0  # Default machinability factor
        if material:
            # Try to get machinability from material object or dict
            if hasattr(material, "machinability"):
                machinability = material.machinability / 8.0  # Normalize to Aluminum 6061 (8.0)
            elif isinstance(material, dict) and "machinability" in material:
                machinability = material.get("machinability", 8.0) / 8.0

        # Calculate overall statistics
        cutting_blocks = [b for b in analyzed_blocks if b.get("is_cutting", False)]

        total_volume = 0.0
        total_time = 0.0

        # Calculate volume and time for each block (with material-aware adjustments)
        for block in analyzed_blocks:
            Ap = block.get("Ap_stock_aware", block.get("Ap", 0))
            Ae = block.get("Ae_stock_aware", block.get("Ae", 0))

            # Calculate volume (Ap × Ae × path_length)
            dx = block.get("end_position", {}).get("X", 0) - block.get("start_position", {}).get(
                "X", 0
            )
            dy = block.get("end_position", {}).get("Y", 0) - block.get("start_position", {}).get(
                "Y", 0
            )
            dz = block.get("end_position", {}).get("Z", 0) - block.get("start_position", {}).get(
                "Z", 0
            )
            path_length = (dx**2 + dy**2 + dz**2) ** 0.5

            volume = Ap * Ae * path_length
            block["volume_removed"] = round(volume, 4)  # Store in block
            total_volume += volume

            # Calculate cutting time with material-adjusted feed rate
            base_feed_rate = block.get("feed_rate", 300)  # Default 300 mm/min
            if base_feed_rate > 0 and block.get("is_cutting", False):
                # Adjust feed rate based on machinability
                # Lower machinability = slower cutting = longer time
                adjusted_feed_rate = base_feed_rate * machinability

                # Calculate actual path length (3D including Z)
                block["cutting_time"] = round(
                    path_length / adjusted_feed_rate * 60, 2
                )  # Convert to seconds
                block["material_adjusted_feed_rate"] = round(adjusted_feed_rate, 2)
                total_time += block["cutting_time"]
            else:
                block["cutting_time"] = 0.0
                block["material_adjusted_feed_rate"] = 0.0

        # Stock wear analysis
        wear_analyzer = OpenCAMLibStockAnalyzer(tool)
        wear_pct, wear_status = wear_analyzer.estimate_tool_wear(total_volume)

        return {
            "status": "success",
            "message": "Dexel-based Ap/Ae analysis with stock model completed",
            "analysis_type": "dexel_stock_aware",
            "data": {
                "total_blocks": len(analyzed_blocks),
                "cutting_blocks": len(cutting_blocks),
                "total_volume_removed": round(total_volume, 2),
                "total_cutting_time": round(total_time, 2),
                "tool": {
                    "tool_id": tool.tool_id,
                    "name": tool.name,
                    "type": tool.tool_type.value,
                    "diameter": tool.diameter,
                },
                "stock_model": self.stock_model.to_dict(),
                "wear_analysis": {
                    "wear_percentage": round(wear_pct, 2),
                    "wear_status": wear_status,
                },
                "blocks": [
                    {
                        "n_number": b.get("n_number"),
                        "block_number": b.get("block_number"),
                        "line_number": b.get("line_number"),
                        "command": b.get("command"),
                        "start_x": b.get("start_position", {}).get("X", 0),
                        "start_y": b.get("start_position", {}).get("Y", 0),
                        "start_z": b.get("start_position", {}).get("Z", 0),
                        "end_x": b.get("end_position", {}).get("X", 0),
                        "end_y": b.get("end_position", {}).get("Y", 0),
                        "end_z": b.get("end_position", {}).get("Z", 0),
                        "Ap": round(b.get("Ap", 0), 4),
                        "Ae": round(b.get("Ae", 0), 4),
                        "Ap_stock_aware": round(b.get("Ap_stock_aware", 0), 4),
                        "Ae_stock_aware": round(b.get("Ae_stock_aware", 0), 4),
                        "engagement_ratio": round(b.get("engagement_ratio", 0), 4),
                        "volume_removed": b.get("volume_removed", 0),  # Add volume_removed
                        "cutting_time": b.get("cutting_time", 0),  # Add cutting_time
                        "feed_rate": b.get("feed_rate", 0),
                        "material_adjusted_feed_rate": b.get("material_adjusted_feed_rate", 0),
                        "is_cutting": b.get("is_cutting", False),
                    }
                    for b in analyzed_blocks
                ],
                "statistics": self._calculate_dexel_statistics(analyzed_blocks),
            },
        }

    def _calculate_statistics(self, analysis: CuttingAnalysis) -> Dict[str, Any]:
        """Calculate statistics from analysis."""
        cutting_blocks = [b for b in analysis.blocks if b.is_cutting]

        if not cutting_blocks:
            return {"error": "No cutting blocks"}

        ap_values = [b.Ap for b in cutting_blocks]
        ae_values = [b.Ae for b in cutting_blocks]

        return {
            "cutting_blocks_count": len(cutting_blocks),
            "Ap": {
                "min": round(min(ap_values), 4),
                "max": round(max(ap_values), 4),
                "avg": round(np.mean(ap_values), 4),
                "std": round(np.std(ap_values), 4),
            },
            "Ae": {
                "min": round(min(ae_values), 4),
                "max": round(max(ae_values), 4),
                "avg": round(np.mean(ae_values), 4),
                "std": round(np.std(ae_values), 4),
            },
        }

    def _calculate_dexel_statistics(
        self,
        blocks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Calculate statistics from Dexel analysis."""
        cutting_blocks = [b for b in blocks if b.get("is_cutting", False)]

        if not cutting_blocks:
            return {"error": "No cutting blocks"}

        ap_values = [b.get("Ap_stock_aware", 0) for b in cutting_blocks]
        ae_values = [b.get("Ae_stock_aware", 0) for b in cutting_blocks]
        engagement = [b.get("engagement_ratio", 0) for b in cutting_blocks]

        return {
            "cutting_blocks_count": len(cutting_blocks),
            "Ap_stock_aware": {
                "min": round(min(ap_values) if ap_values else 0, 4),
                "max": round(max(ap_values) if ap_values else 0, 4),
                "avg": round(np.mean(ap_values) if ap_values else 0, 4),
            },
            "Ae_stock_aware": {
                "min": round(min(ae_values) if ae_values else 0, 4),
                "max": round(max(ae_values) if ae_values else 0, 4),
                "avg": round(np.mean(ae_values) if ae_values else 0, 4),
            },
            "engagement_ratio": {
                "avg": round(np.mean(engagement) if engagement else 0, 4),
                "max": round(max(engagement) if engagement else 0, 4),
            },
        }

    def set_stock_bounds(
        self,
        x_min: float,
        x_max: float,
        y_min: float,
        y_max: float,
        z_min: float,
        z_max: float,
        resolution: float = 1.0,
    ):
        """Configure stock model bounds.

        Args:
            x_min, x_max: X bounds
            y_min, y_max: Y bounds
            z_min, z_max: Z bounds
            resolution: Grid resolution
        """
        try:
            self.stock_model = DexelModel(
                x_min,
                x_max,
                y_min,
                y_max,
                z_min,
                z_max,
                resolution=resolution,
                material=self.stock_model.material if self.stock_model else Material(),
            )
            logger.info(f"Updated stock bounds: {x_min}-{x_max}, {y_min}-{y_max}, {z_min}-{z_max}")
        except Exception as e:
            logger.error(f"Error setting stock bounds: {e}")

    def set_stock_material(
        self,
        material_name: str,
        density: float = 2.7,
        hardness: float = 95,
        machinability: float = 8.0,
    ):
        """Configure stock material.

        Args:
            material_name: Material name
            density: Material density
            hardness: Material hardness (HV)
            machinability: Machinability index (8.0 = Aluminum 6061)
        """
        try:
            material = Material(
                name=material_name, density=density, hardness=hardness, machinability=machinability
            )
            if self.stock_model:
                self.stock_model.material = material
            logger.info(f"Updated material: {material_name} (Machinability: {machinability})")
        except Exception as e:
            logger.error(f"Error setting material: {e}")

    def get_analysis_report(self, analysis: Dict[str, Any]) -> str:
        """Generate text report from analysis.

        Args:
            analysis: Analysis result

        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 60)
        report.append("ADVANCED CAM ANALYSIS REPORT")
        report.append("=" * 60)

        data = analysis.get("data", {})
        report.append(f"\nAnalysis Type: {analysis.get('analysis_type', 'unknown')}")
        report.append(f"Total Blocks: {data.get('total_blocks', 'N/A')}")
        report.append(f"Cutting Blocks: {data.get('cutting_blocks', 'N/A')}")

        if "summary" in data:
            report.append(f"\nSummary: {data['summary']}")

        if "statistics" in data:
            stats = data["statistics"]
            report.append("\nApaxial Depth (Ap):")
            report.append(f"  Min: {stats.get('Ap', {}).get('min', 'N/A')}")
            report.append(f"  Max: {stats.get('Ap', {}).get('max', 'N/A')}")
            report.append(f"  Avg: {stats.get('Ap', {}).get('avg', 'N/A')}")

            report.append("\nRadial Depth (Ae):")
            report.append(f"  Min: {stats.get('Ae', {}).get('min', 'N/A')}")
            report.append(f"  Max: {stats.get('Ae', {}).get('max', 'N/A')}")
            report.append(f"  Avg: {stats.get('Ae', {}).get('avg', 'N/A')}")

        report.append("\n" + "=" * 60)

        return "\n".join(report)
