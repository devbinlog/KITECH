"""Digital Thread Project Manager Agent - Main entry point."""

import logging
from pathlib import Path
from typing import Any

from .services.workplan_service import WorkplanService
from .parsers.nc_parser import NCSplitter
from .parsers.xml_parser import validate_xml

logger = logging.getLogger(__name__)


class DigitalThreadProjectManager:
    """
    Agent for managing Digital Thread projects.

    Converts CAM data to ISO 14649 compliant XML format.
    """

    def __init__(self, cam_type: str = "nx"):
        """
        Initialize agent.

        Args:
            cam_type: CAM system type ("nx", "powermill")
        """
        self.cam_type = cam_type.lower()
        self.workplan_service = WorkplanService(cam_type)

    def convert_cam_to_xml(
        self,
        cam_path: str | Path,
        mapping_path: str | Path,
        output_path: str | Path | None = None,
    ) -> list[str]:
        """
        Convert CAM JSON file to workingstep XMLs.

        Args:
            cam_path: Path to CAM JSON file
            mapping_path: Path to mapping config JSON
            output_path: Optional output directory for XML files

        Returns:
            List of workingstep XML strings
        """
        mapping = self.workplan_service.load_mapping(mapping_path)
        cam_json = self.workplan_service.load_cam_json(cam_path)

        ws_xmls = self.workplan_service.convert_cam_to_workingsteps(cam_json, mapping)

        if output_path:
            out_dir = Path(output_path)
            out_dir.mkdir(parents=True, exist_ok=True)
            for i, xml in enumerate(ws_xmls):
                (out_dir / f"workingstep_{i + 1:03d}.xml").write_text(xml)

        return ws_xmls

    def apply_cam_to_project(
        self,
        dtasset_path: str | Path,
        cam_path: str | Path,
        mapping_path: str | Path,
        output_path: str | Path | None = None,
    ) -> str:
        """
        Apply CAM data to existing dt_asset project XML.

        Args:
            dtasset_path: Path to dt_asset XML file
            cam_path: Path to CAM JSON file
            mapping_path: Path to mapping config JSON
            output_path: Optional output path for updated XML

        Returns:
            Updated dt_asset XML string
        """
        dtasset_xml = Path(dtasset_path).read_text()
        mapping = self.workplan_service.load_mapping(mapping_path)
        cam_json = self.workplan_service.load_cam_json(cam_path)

        result = self.workplan_service.apply_cam_to_dtasset(dtasset_xml, cam_json, mapping)

        if output_path:
            Path(output_path).write_text(result)

        return result

    def extract_tools(
        self,
        cam_path: str | Path,
        mapping_path: str | Path,
        global_asset_id: str = "http://example.com/asset",
        base_asset_id: str = "tool",
        output_path: str | Path | None = None,
    ) -> list[str]:
        """
        Extract ISO 13399 cutting tool XMLs from CAM file.

        Args:
            cam_path: Path to CAM JSON file
            mapping_path: Path to mapping config JSON
            global_asset_id: Global asset ID URL
            base_asset_id: Base asset ID prefix
            output_path: Optional output directory for XML files

        Returns:
            List of tool dt_asset XML strings
        """
        mapping = self.workplan_service.load_mapping(mapping_path)
        cam_json = self.workplan_service.load_cam_json(cam_path)

        tool_xmls = self.workplan_service.extract_tools_from_cam(
            cam_json, mapping, global_asset_id, base_asset_id
        )

        if output_path:
            out_dir = Path(output_path)
            out_dir.mkdir(parents=True, exist_ok=True)
            for i, xml in enumerate(tool_xmls):
                (out_dir / f"tool_{i + 1:03d}.xml").write_text(xml)

        return tool_xmls

    def split_nc_by_tool(
        self,
        nc_path: str | Path,
        output_path: str | Path | None = None,
    ) -> list[dict[str, Any]]:
        """
        Split NC file by tool changes.

        Args:
            nc_path: Path to NC file
            output_path: Optional output directory for split files

        Returns:
            List of dicts with tool_number and lines for each segment
        """
        content = Path(nc_path).read_text()
        splitter = NCSplitter(content).parse()

        result = []
        if output_path:
            out_dir = Path(output_path)
            out_dir.mkdir(parents=True, exist_ok=True)

        for i, seg in enumerate(splitter.segments):
            full_lines = [line.strip("\n") for line in splitter.assemble_segment(i)]
            result.append({"tool_number": seg.tool_number, "lines": full_lines})
            
            if output_path:
                out_file = out_dir / f"segment_{i + 1:03d}_{seg.tool_number}.nc"
                out_file.write_text("\n".join(full_lines) + "\n")

        return result

    def validate_dtasset(self, xml_path: str | Path) -> bool:
        """
        Validate dt_asset XML against schema.

        Args:
            xml_path: Path to XML file

        Returns:
            True if valid, False otherwise
        """
        content = Path(xml_path).read_text()
        return validate_xml(content)


def main():
    """CLI entry point for testing."""
    import sys

    if len(sys.argv) < 3:
        logger.error("Usage: python -m src.agent <cam_json> <mapping_json>")
        sys.exit(1)

    agent = DigitalThreadProjectManager()
    xmls = agent.convert_cam_to_xml(sys.argv[1], sys.argv[2])

    for i, xml in enumerate(xmls):
        logger.info("=== Workingstep %d ===", i + 1)
        logger.debug("%s", xml[:500] + "..." if len(xml) > 500 else xml)


if __name__ == "__main__":
    main()
