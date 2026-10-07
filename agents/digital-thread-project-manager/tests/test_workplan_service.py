"""Tests for WorkplanService."""

import json
from pathlib import Path

import pytest

from src.services.workplan_service import WorkplanService


SAMPLES_DIR = (
    Path(__file__).parent.parent.parent.parent / "samples" / "digital-thread-project-manager"
)


class TestWorkplanServiceInit:
    """Test WorkplanService initialization."""

    def test_init_default(self):
        """Default initialization should use NX."""
        service = WorkplanService()
        assert service.cam_type == "nx"

    def test_init_custom_type(self):
        """Should accept custom CAM type."""
        service = WorkplanService(cam_type="powermill")
        assert service.cam_type == "powermill"

    def test_converter_initialized(self):
        """CamConverter should be initialized."""
        service = WorkplanService()
        assert service.converter is not None


class TestLoadMapping:
    """Test load_mapping method."""

    @pytest.fixture
    def service(self):
        return WorkplanService()

    def test_load_valid_mapping(self, service, tmp_path):
        """Should load valid JSON mapping."""
        mapping = {"key1": "value1", "key2": "value2"}
        mapping_path = tmp_path / "mapping.json"
        mapping_path.write_text(json.dumps(mapping))

        result = service.load_mapping(mapping_path)

        assert result == mapping

    def test_load_mapping_path_object(self, service, tmp_path):
        """Should accept Path object."""
        mapping = {"key": "value"}
        mapping_path = tmp_path / "mapping.json"
        mapping_path.write_text(json.dumps(mapping))

        result = service.load_mapping(Path(mapping_path))

        assert result == mapping

    def test_load_mapping_not_found(self, service):
        """Should raise error for missing file."""
        with pytest.raises(FileNotFoundError):
            service.load_mapping("/nonexistent/mapping.json")


class TestLoadCamJson:
    """Test load_cam_json method."""

    @pytest.fixture
    def service(self):
        return WorkplanService()

    def test_load_valid_json(self, service, tmp_path):
        """Should load valid CAM JSON."""
        cam_data = {"operations": [{"id": "1"}, {"id": "2"}]}
        cam_path = tmp_path / "cam.json"
        cam_path.write_text(json.dumps(cam_data))

        result = service.load_cam_json(cam_path)

        assert result == cam_data

    def test_load_json_array(self, service, tmp_path):
        """Should load JSON array."""
        cam_data = [{"op": "1"}, {"op": "2"}]
        cam_path = tmp_path / "cam.json"
        cam_path.write_text(json.dumps(cam_data))

        result = service.load_cam_json(cam_path)

        assert result == cam_data


class TestConvertCamToWorkingsteps:
    """Test convert_cam_to_workingsteps method."""

    @pytest.fixture
    def service(self):
        return WorkplanService(cam_type="nx")

    @pytest.fixture
    def cam_json(self):
        return {
            "values": [
                {"Object Information": {"Object name": "OP-001"}},
                {"Object Information": {"Object name": "OP-002"}},
                {"Object Information": {"Object name": "OP-003"}},
            ]
        }

    @pytest.fixture
    def mapping(self):
        return {
            "Object Information.Object name": "MachiningWorkingstep.its_id",
        }

    def test_returns_list(self, service, cam_json, mapping):
        """Should return list of XML strings."""
        result = service.convert_cam_to_workingsteps(cam_json, mapping)

        assert isinstance(result, list)
        assert len(result) == 3

    def test_each_is_xml(self, service, cam_json, mapping):
        """Each result should be XML string."""
        result = service.convert_cam_to_workingsteps(cam_json, mapping)

        for xml in result:
            assert isinstance(xml, str)
            assert "<its_elements" in xml

    def test_empty_cam_json(self, service, mapping):
        """Should handle empty CAM JSON."""
        result = service.convert_cam_to_workingsteps({"values": []}, mapping)

        assert result == []

    def test_single_operation(self, service, mapping):
        """Should handle single operation."""
        cam_json = {"values": [{"Object Information": {"Object name": "SINGLE"}}]}

        result = service.convert_cam_to_workingsteps(cam_json, mapping)

        assert len(result) == 1


class TestApplyCamToDtasset:
    """Test apply_cam_to_dtasset method."""

    @pytest.fixture
    def service(self):
        return WorkplanService(cam_type="nx")

    @pytest.fixture
    def dtasset_xml(self):
        """Minimal dt_asset XML with project element."""
        return """<?xml version="1.0" ?>
<dt_asset xmlns="http://digital-thread.re/dt_asset"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <asset_global_id>http://example.com/asset</asset_global_id>
    <id>test-asset</id>
    <dt_elements xsi:type="dt_project">
        <element_id>project-001</element_id>
    </dt_elements>
</dt_asset>"""

    @pytest.fixture
    def cam_json(self):
        return {"values": [{"Object Information": {"Object name": "OP-001"}}]}

    @pytest.fixture
    def mapping(self):
        return {"Object Information.Object name": "MachiningWorkingstep.its_id"}

    def test_returns_xml_string(self, service, dtasset_xml, cam_json, mapping):
        """Should return XML string."""
        result = service.apply_cam_to_dtasset(dtasset_xml, cam_json, mapping)

        assert isinstance(result, str)
        assert "<?xml" in result

    def test_adds_workplan(self, service, dtasset_xml, cam_json, mapping):
        """Should add main_workplan to project."""
        result = service.apply_cam_to_dtasset(dtasset_xml, cam_json, mapping)

        assert "main_workplan" in result

    def test_preserves_original_content(self, service, dtasset_xml, cam_json, mapping):
        """Should preserve original dt_asset content."""
        result = service.apply_cam_to_dtasset(dtasset_xml, cam_json, mapping)

        assert "test-asset" in result
        assert "project-001" in result


class TestExtractToolsFromCam:
    """Test extract_tools_from_cam method."""

    @pytest.fixture
    def service(self):
        return WorkplanService(cam_type="nx")

    @pytest.fixture
    def cam_json_with_tools(self):
        return {
            "values": [
                {
                    "Tool Information": {
                        "Tool Name": "TOOL_A",
                        "Diameter": "10.0",
                    }
                },
                {
                    "Tool Information": {
                        "Tool Name": "TOOL_A",  # Duplicate
                        "Diameter": "10.0",
                    }
                },
                {
                    "Tool Information": {
                        "Tool Name": "TOOL_B",
                        "Diameter": "6.0",
                    }
                },
            ]
        }

    @pytest.fixture
    def tool_mapping(self):
        return {
            "Tool Information.Tool Name": "MachiningWorkingstep.its_operation.MachiningOperation.its_tool.MachiningTool.its_id",
            "Tool Information.Diameter": "MachiningWorkingstep.its_operation.MachiningOperation.its_tool.MachiningTool.MillingMachineCuttingTool.effective_cutting_diameter",
        }

    def test_returns_list(self, service, cam_json_with_tools, tool_mapping):
        """Should return list of tool XMLs."""
        result = service.extract_tools_from_cam(
            cam_json_with_tools,
            tool_mapping,
            global_asset_id="http://example.com",
            base_asset_id="tool",
        )

        assert isinstance(result, list)

    def test_deduplicates_tools(self, service, cam_json_with_tools, tool_mapping):
        """Should deduplicate tools by element_id."""
        result = service.extract_tools_from_cam(
            cam_json_with_tools,
            tool_mapping,
            global_asset_id="http://example.com",
            base_asset_id="tool",
        )

        # 3 ops but only 2 unique tools
        assert len(result) == 2

    def test_tool_xml_format(self, service, cam_json_with_tools, tool_mapping):
        """Tool XMLs should be valid dt_asset format."""
        result = service.extract_tools_from_cam(
            cam_json_with_tools,
            tool_mapping,
            global_asset_id="http://example.com",
            base_asset_id="tool",
        )

        for xml in result:
            assert "dt_cutting_tool_13399" in xml
            assert "<dt_asset" in xml


@pytest.mark.skipif(
    not (SAMPLES_DIR / "json" / "nx" / "NX_json.json").exists(), reason="Sample files not found"
)
class TestWithRealSamples:
    """Integration tests with real sample files."""

    @pytest.fixture
    def service(self):
        return WorkplanService(cam_type="nx")

    def test_load_real_cam_json(self, service):
        """Load real NX CAM JSON file."""
        cam_path = SAMPLES_DIR / "json" / "nx" / "NX_json.json"
        result = service.load_cam_json(cam_path)

        assert result is not None

    def test_load_real_mapping(self, service):
        """Load real mapping config."""
        mapping_path = SAMPLES_DIR / "json" / "nx" / "mapping_config_NX.json"
        result = service.load_mapping(mapping_path)

        assert isinstance(result, dict)
        assert len(result) > 0

    def test_full_conversion(self, service):
        """Full conversion workflow."""
        cam_json = service.load_cam_json(SAMPLES_DIR / "json" / "nx" / "NX_json.json")
        mapping = service.load_mapping(SAMPLES_DIR / "json" / "nx" / "mapping_config_NX.json")

        result = service.convert_cam_to_workingsteps(cam_json, mapping)

        assert len(result) > 0
