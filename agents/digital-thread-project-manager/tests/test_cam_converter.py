"""Tests for CAM converter."""

import json
from pathlib import Path

import pytest

from src.converters.cam_converter import CamConverter
from src.parsers.cam_nx import pick_nx_ops
from src.parsers.cam_powermill import pick_powermill_ops


SAMPLES_DIR = (
    Path(__file__).parent.parent.parent.parent / "samples" / "digital-thread-project-manager"
)


class TestCamParsers:
    """Test CAM JSON parsers."""

    def test_pick_nx_ops_with_values(self):
        """NX JSON with values array should extract operations."""
        cam_json = {"key": {"some": "metadata"}, "values": [{"op": "1"}, {"op": "2"}, {"op": "3"}]}
        ops = pick_nx_ops(cam_json)
        assert len(ops) == 3
        assert ops[0]["op"] == "1"

    def test_pick_nx_ops_fallback_list(self):
        """Direct list should be returned as-is."""
        cam_json = [{"op": "1"}, {"op": "2"}]
        ops = pick_nx_ops(cam_json)
        assert len(ops) == 2

    def test_pick_powermill_ops_single(self):
        """PowerMill single op should wrap in list."""
        cam_json = {"operation": {"name": "roughing"}}
        ops = pick_powermill_ops(cam_json)
        assert len(ops) == 1
        assert ops[0]["name"] == "roughing"


class TestCamConverter:
    """Test CAM to XML conversion."""

    @pytest.fixture
    def converter(self):
        return CamConverter(cam_type="nx")

    @pytest.fixture
    def simple_mapping(self):
        return {
            "Object Information.Object name": "MachiningWorkingstep.its_id",
            "Feed Rate.Cut": "MachiningWorkingstep.its_operation.MachiningOperation.its_technology.Technology.feedrate",
        }

    def test_create_workingstep_xml_minimal(self, converter, simple_mapping):
        """Should create valid XML with minimal CAM data."""
        cam_op = {
            "Object Information": {"Object name": "OP-001"},
            "Feed Rate": {"Cut": "500"},
        }
        xml = converter.create_workingstep_xml(cam_op, simple_mapping, 0)

        assert "<its_elements" in xml
        assert "machining_workingstep" in xml
        assert "<its_id>" in xml or "its_id" in xml

    def test_required_fields_ensured(self, converter, simple_mapping):
        """Should add required fields even with empty CAM data."""
        cam_op = {}
        xml = converter.create_workingstep_xml(cam_op, simple_mapping, 0)

        assert "<its_secplane>" in xml
        assert "<its_feature>" in xml
        assert "its_operation" in xml  # May have xsi:type attribute

    def test_build_tool_13399_xml(self):
        """Should build ISO 13399 tool XML."""
        xml = CamConverter.build_tool_13399_xml(
            global_asset_id="http://example.com/tool/001",
            asset_id="tool_001",
            element_id="endmill_10mm",
            display_name="10mm Endmill",
            values={
                "effective_cutting_diameter": "10.0",
                "number_of_teeth": "4",
            },
        )

        assert "dt_cutting_tool_13399" in xml
        assert "effective_cutting_diameter" in xml
        assert "number_of_teeth" in xml


@pytest.mark.skipif(
    not (SAMPLES_DIR / "json" / "nx" / "NX_json.json").exists(), reason="Sample files not found"
)
class TestWithSampleData:
    """Integration tests with sample data files."""

    @pytest.fixture
    def nx_cam_json(self):
        with open(SAMPLES_DIR / "json" / "nx" / "NX_json.json") as f:
            return json.load(f)

    @pytest.fixture
    def nx_mapping(self):
        with open(SAMPLES_DIR / "json" / "nx" / "mapping_config_NX.json") as f:
            return json.load(f)

    def test_convert_nx_sample(self, nx_cam_json, nx_mapping):
        """Should convert NX sample file to workingstep XMLs."""
        converter = CamConverter(cam_type="nx")
        ops = converter.pick_ops(nx_cam_json)

        assert len(ops) > 0

        xml = converter.create_workingstep_xml(ops[0], nx_mapping, 0)
        assert "<its_elements" in xml
        assert "machining_workingstep" in xml

    def test_extract_tools_from_nx(self, nx_cam_json, nx_mapping):
        """Should extract tool values from NX CAM."""
        converter = CamConverter(cam_type="nx")
        ops = converter.pick_ops(nx_cam_json)

        if ops:
            values = CamConverter.extract_13399_values(ops[0], nx_mapping)
            # Should extract at least some tool values
            # (depends on mapping content)
            assert isinstance(values, dict)
