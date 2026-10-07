"""CAM JSON to ISO 14649 XML converter."""

import re
import xml.etree.ElementTree as ET
from typing import Any

import xmltodict

from ..parsers.xml_parser import get_nested_value
from ..parsers.cam_nx import pick_nx_ops
from ..parsers.cam_powermill import pick_powermill_ops

DEFAULT_SCHEMA_VERSION = "v31"
_ELEM_ID_SAFE = re.compile(r"[^0-9A-Za-z_\-]")

# ISO 14649 path to ISO 13399 component name mapping
ISO14649_TO_13399: dict[str, str] = {
    "MachiningWorkingstep.its_operation.MachiningOperation.its_tool.MachiningTool.MillingMachineCuttingTool.effective_cutting_diameter": "effective_cutting_diameter",
    "MachiningWorkingstep.its_operation.MachiningOperation.its_tool.MachiningTool.MillingMachineCuttingTool.MillingCuttingTool.edge_radius": "corner_radius",
    "MachiningWorkingstep.its_operation.MachiningOperation.its_tool.MachiningTool.MillingMachineCuttingTool.its_cutting_edges.CuttingComponent.tool_functional_length": "functional_length",
    "MachiningWorkingstep.its_operation.MachiningOperation.its_tool.MachiningTool.MillingMachineCuttingTool.overall_assembly_length": "overhang_length",
    "MachiningWorkingstep.its_operation.MachiningOperation.its_tool.MachiningTool.MillingMachineCuttingTool.MillingCuttingTool.number_of_effective_teeth": "number_of_teeth",
}


class CamConverter:
    """Convert CAM JSON to ISO 14649 workingstep XML."""

    def __init__(self, cam_type: str = "nx"):
        self.cam_type = cam_type.lower()

    def pick_ops(self, cam_json: Any) -> list[dict[str, Any]]:
        """Extract operations from CAM JSON based on type."""
        if self.cam_type == "nx":
            return pick_nx_ops(cam_json)
        elif self.cam_type in ("powermill", "pmill", "power_mill"):
            return pick_powermill_ops(cam_json)
        return cam_json if isinstance(cam_json, list) else [cam_json]

    def create_workingstep_xml(
        self,
        cam_op: dict[str, Any],
        mapping: dict[str, str],
        index: int = 0,
    ) -> str:
        """Convert single CAM operation to its_elements XML."""
        nested = self._build_nested_structure(cam_op, mapping)
        self._ensure_required_fields(nested, index)

        root = ET.Element(
            "its_elements",
            {
                "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                "xsi:type": "machining_workingstep",
            },
        )
        self._dict_to_xml(root, nested)
        return ET.tostring(root, encoding="unicode", method="xml")

    def _build_nested_structure(
        self,
        cam_op: dict[str, Any],
        mapping: dict[str, str],
    ) -> dict[str, Any]:
        """Build nested dict structure from CAM JSON using mapping."""
        nested: dict[str, Any] = {
            "its_id": {},
            "its_secplane": {},
            "its_feature": {},
            "its_operation": {},
            "its_effect": {},
        }

        for json_key, path in mapping.items():
            parts = path.split(".")
            parent = nested

            for i, part in enumerate(parts):
                if not part or part[0].isupper():
                    continue

                is_leaf = i == len(parts) - 1
                if is_leaf:
                    value = get_nested_value(cam_op, json_key.split("."))
                    if value is not None:
                        parent[part] = value
                else:
                    if part not in parent or not isinstance(parent[part], dict):
                        parent[part] = {}
                    parent = parent[part]

        return nested

    def _ensure_required_fields(self, ws: dict[str, Any], idx: int = 0) -> None:
        """Ensure minimum required fields for schema validation."""
        # its_id
        if not ws.get("its_id"):
            ws["its_id"] = f"ws-{idx + 1:03d}"

        # its_secplane with minimal structure
        sec = ws.setdefault("its_secplane", {})
        sec.setdefault("name", f"secplane-{idx + 1:03d}")
        pos = sec.setdefault("position", {})
        pos.setdefault("name", f"pos-{idx + 1:03d}")
        loc = pos.setdefault("location", {})
        loc.setdefault("name", "origin")
        loc.setdefault("coordinates", ["0.0", "0.0", "0.0"])

        # its_feature
        feat = ws.setdefault("its_feature", {})
        feat.setdefault("its_id", "auto_feature")
        feat.setdefault("its_workpiece", {"its_id": "default_workpiece"})

        # its_operation
        op = ws.setdefault("its_operation", {})
        op.setdefault("@xsi:type", "machining_operation")

        # its_technology (milling)
        tech = op.setdefault("its_technology", {})
        tech.setdefault("feedrate_reference", "tcp")
        tech.setdefault("synchronize_spindle_with_feed", False)
        tech.setdefault("inhibit_feedrate_override", False)
        tech.setdefault("inhibit_spindle_override", False)

        # its_machine_functions
        mf = op.setdefault("its_machine_functions", {})
        mf.setdefault("@xsi:type", "milling_machine_functions")
        mf.setdefault("coolant", False)
        mf.setdefault("through_spindle_coolant", False)
        mf.setdefault("chip_removal", False)

        # its_tool
        tool = op.setdefault("its_tool", {})
        tool.setdefault("@xsi:type", "machining_tool")
        tool.setdefault("its_id", "temp")

    def _dict_to_xml(self, parent: ET.Element, data: dict) -> None:
        """Convert dict to XML elements recursively."""
        for key, value in data.items():
            attrs = {}
            if isinstance(value, dict):
                attr_keys = [k for k in value.keys() if k.startswith("@")]
                for attr_key in attr_keys:
                    attrs[attr_key[1:]] = value.pop(attr_key)

            if isinstance(value, list):
                for item in value:
                    self._dict_to_xml(parent, {key: item})
                continue

            if isinstance(value, dict):
                child = ET.SubElement(parent, key, attrs)
                self._dict_to_xml(child, value)
            else:
                child = ET.SubElement(parent, key, attrs)
                child.text = str(value) if value is not None else ""

    @staticmethod
    def build_tool_13399_xml(
        *,
        global_asset_id: str,
        asset_id: str,
        element_id: str,
        display_name: str,
        values: dict[str, Any],
    ) -> str:
        """Build ISO 13399 cutting tool dt_asset XML."""
        num_blocks = []
        for key in (
            "effective_cutting_diameter",
            "corner_radius",
            "functional_length",
            "overhang_length",
            "number_of_teeth",
        ):
            val = values.get(key)
            if val is not None and val != "":
                num_blocks.append({"value_name": key, "value_component": str(val)})

        root = {
            "dt_asset": {
                "@xmlns": "http://digital-thread.re/dt_asset",
                "@xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                "@schemaVersion": DEFAULT_SCHEMA_VERSION,
                "asset_global_id": global_asset_id,
                "id": asset_id,
                "asset_kind": "instance",
                "dt_elements": {
                    "@xsi:type": "dt_cutting_tool_13399",
                    "element_id": element_id,
                    "category": "CuttingTool",
                    "display_name": display_name or element_id,
                    "numerical_value": (
                        [
                            {
                                "value_name": nb["value_name"],
                                "value_component": nb["value_component"],
                            }
                            for nb in num_blocks
                        ]
                        if num_blocks
                        else None
                    ),
                },
            },
        }

        if not root["dt_asset"]["dt_elements"]["numerical_value"]:
            root["dt_asset"]["dt_elements"].pop("numerical_value", None)

        return xmltodict.unparse(root, pretty=True, attr_prefix="@")

    @staticmethod
    def extract_13399_values(
        cam_op: dict[str, Any],
        cam_to_14649_map: dict[str, str],
    ) -> dict[str, Any]:
        """Extract ISO 13399 tool values from CAM operation using mapping."""
        # Build CAM key to 13399 component map
        cam_to_13399: dict[str, str] = {}
        for cam_key, path_14649 in cam_to_14649_map.items():
            comp = ISO14649_TO_13399.get(path_14649)
            if comp:
                cam_to_13399[cam_key] = comp

        # Extract values
        out: dict[str, Any] = {}
        for cam_key, comp in cam_to_13399.items():
            v = get_nested_value(cam_op, cam_key.split("."))
            if v is not None and v != "":
                out[comp] = v
        return out

    @staticmethod
    def derive_tool_element_id(
        cam_op: dict[str, Any],
        mapping: dict[str, str],
        fallback: str = "tool-001",
    ) -> str:
        """Derive tool element_id from CAM operation using mapping."""
        for cam_key, path in mapping.items():
            if path.endswith("MachiningTool.its_id"):
                raw = get_nested_value(cam_op, cam_key.split("."))
                if raw:
                    val = str(raw).strip().replace(" ", "_")
                    return _ELEM_ID_SAFE.sub("_", val) if val else fallback
        return fallback
