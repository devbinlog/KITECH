"""Workplan service - Business logic for CAM to XML conversion."""

import json
from pathlib import Path
from typing import Any

import xmltodict

from ..converters.cam_converter import CamConverter


class WorkplanService:
    """Service for managing workplan and CAM-to-XML conversion."""

    def __init__(self, cam_type: str = "nx"):
        self.converter = CamConverter(cam_type)
        self.cam_type = cam_type

    def load_mapping(self, mapping_path: str | Path) -> dict[str, str]:
        """Load CAM to ISO 14649 mapping config."""
        with open(mapping_path) as f:
            return json.load(f)

    def load_cam_json(self, cam_path: str | Path) -> Any:
        """Load CAM JSON file."""
        with open(cam_path) as f:
            return json.load(f)

    def convert_cam_to_workingsteps(
        self,
        cam_json: Any,
        mapping: dict[str, str],
    ) -> list[str]:
        """Convert CAM JSON to list of workingstep XMLs."""
        ops = self.converter.pick_ops(cam_json)
        return [self.converter.create_workingstep_xml(op, mapping, i) for i, op in enumerate(ops)]

    def apply_cam_to_dtasset(
        self,
        dtasset_xml: str,
        cam_json: Any,
        mapping: dict[str, str],
        target_element_id: str | None = None,
    ) -> str:
        """
        Apply CAM operations into existing dt_asset XML's main_workplan.

        Returns updated dt_asset XML string.
        """
        doc = xmltodict.parse(dtasset_xml)
        dt_asset = doc.get("dt_asset", doc)

        # Find project element
        elems = dt_asset.get("dt_elements")
        if not isinstance(elems, list):
            elems = [elems] if elems else []

        project_elem = None
        for elem in elems:
            if isinstance(elem, dict):
                xsi_type = elem.get("@xsi:type", "")
                elem_id = elem.get("element_id", "")
                if xsi_type == "dt_project" or (target_element_id and elem_id == target_element_id):
                    project_elem = elem
                    break

        if not project_elem:
            raise ValueError("No dt_project element found in dt_asset")

        # Get or create main_workplan
        workplan = project_elem.setdefault("main_workplan", {})
        workplan.setdefault("its_id", "main_workplan")

        # Convert CAM to workingsteps and append
        ws_xmls = self.convert_cam_to_workingsteps(cam_json, mapping)
        existing_elements = workplan.get("its_elements", [])
        if not isinstance(existing_elements, list):
            existing_elements = [existing_elements] if existing_elements else []

        for ws_xml in ws_xmls:
            ws_dict = xmltodict.parse(ws_xml)
            ws_elem = ws_dict.get("its_elements", {})
            existing_elements.append(ws_elem)

        workplan["its_elements"] = existing_elements

        return xmltodict.unparse(doc, pretty=True)

    def extract_tools_from_cam(
        self,
        cam_json: Any,
        mapping: dict[str, str],
        global_asset_id: str,
        base_asset_id: str,
    ) -> list[str]:
        """
        Extract ISO 13399 cutting tool XMLs from CAM operations.

        Returns list of dt_asset XML strings for each unique tool.
        """
        ops = self.converter.pick_ops(cam_json)
        tools: dict[str, str] = {}  # element_id -> xml

        for i, op in enumerate(ops):
            elem_id = CamConverter.derive_tool_element_id(op, mapping, f"tool-{i + 1:03d}")
            if elem_id in tools:
                continue

            values = CamConverter.extract_13399_values(op, mapping)
            xml = CamConverter.build_tool_13399_xml(
                global_asset_id=global_asset_id,
                asset_id=f"{base_asset_id}_{elem_id}",
                element_id=elem_id,
                display_name=elem_id,
                values=values,
            )
            tools[elem_id] = xml

        return list(tools.values())
