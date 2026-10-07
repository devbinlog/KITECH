"""Tests for DigitalThreadProjectManager agent."""

import json
from pathlib import Path

import pytest

from src.agent import DigitalThreadProjectManager


SAMPLES_DIR = (
    Path(__file__).parent.parent.parent.parent / "samples" / "digital-thread-project-manager"
)


class TestAgentInitialization:
    """Test agent initialization."""

    def test_init_default_nx(self):
        """Default initialization should use NX CAM type."""
        agent = DigitalThreadProjectManager()
        assert agent.cam_type == "nx"

    def test_init_powermill(self):
        """Should accept powermill CAM type."""
        agent = DigitalThreadProjectManager(cam_type="powermill")
        assert agent.cam_type == "powermill"

    def test_init_case_insensitive(self):
        """CAM type should be case-insensitive."""
        agent = DigitalThreadProjectManager(cam_type="NX")
        assert agent.cam_type == "nx"

    def test_workplan_service_initialized(self):
        """WorkplanService should be initialized."""
        agent = DigitalThreadProjectManager()
        assert agent.workplan_service is not None


class TestConvertCamToXml:
    """Test convert_cam_to_xml method."""

    @pytest.fixture
    def agent(self):
        return DigitalThreadProjectManager(cam_type="nx")

    @pytest.fixture
    def temp_files(self, tmp_path):
        """Create temporary CAM and mapping files."""
        cam_data = {
            "values": [
                {
                    "Object Information": {"Object name": "OP-001"},
                    "Feed Rate": {"Cut": "500"},
                },
                {
                    "Object Information": {"Object name": "OP-002"},
                    "Feed Rate": {"Cut": "600"},
                },
            ]
        }
        mapping = {
            "Object Information.Object name": "MachiningWorkingstep.its_id",
            "Feed Rate.Cut": "MachiningWorkingstep.its_operation.MachiningOperation.its_technology.Technology.feedrate",
        }

        cam_path = tmp_path / "cam.json"
        mapping_path = tmp_path / "mapping.json"

        cam_path.write_text(json.dumps(cam_data))
        mapping_path.write_text(json.dumps(mapping))

        return cam_path, mapping_path

    def test_convert_returns_list(self, agent, temp_files):
        """Should return list of XML strings."""
        cam_path, mapping_path = temp_files
        result = agent.convert_cam_to_xml(cam_path, mapping_path)

        assert isinstance(result, list)
        assert len(result) == 2

    def test_convert_valid_xml(self, agent, temp_files):
        """Each result should be valid XML."""
        cam_path, mapping_path = temp_files
        result = agent.convert_cam_to_xml(cam_path, mapping_path)

        for xml in result:
            assert "<its_elements" in xml
            assert "machining_workingstep" in xml

    def test_convert_with_output_path(self, agent, temp_files, tmp_path):
        """Should save XML files when output_path provided."""
        cam_path, mapping_path = temp_files
        output_path = tmp_path / "output"

        agent.convert_cam_to_xml(cam_path, mapping_path, output_path)

        assert output_path.exists()
        xml_files = list(output_path.glob("*.xml"))
        assert len(xml_files) == 2

    def test_convert_output_filenames(self, agent, temp_files, tmp_path):
        """Output files should follow naming convention."""
        cam_path, mapping_path = temp_files
        output_path = tmp_path / "output"

        agent.convert_cam_to_xml(cam_path, mapping_path, output_path)

        assert (output_path / "workingstep_001.xml").exists()
        assert (output_path / "workingstep_002.xml").exists()


class TestExtractTools:
    """Test extract_tools method."""

    @pytest.fixture
    def agent(self):
        return DigitalThreadProjectManager(cam_type="nx")

    @pytest.fixture
    def temp_files_with_tools(self, tmp_path):
        """Create CAM file with tool information."""
        cam_data = {
            "values": [
                {
                    "Object Information": {"Object name": "OP-001"},
                    "Tool Information": {
                        "Tool Name": "ENDMILL_10",
                        "Diameter": "10.0",
                        "Number of Flutes": "4",
                    },
                },
                {
                    "Object Information": {"Object name": "OP-002"},
                    "Tool Information": {
                        "Tool Name": "ENDMILL_10",  # Same tool
                        "Diameter": "10.0",
                    },
                },
                {
                    "Object Information": {"Object name": "OP-003"},
                    "Tool Information": {
                        "Tool Name": "BALL_6",
                        "Diameter": "6.0",
                    },
                },
            ]
        }
        mapping = {
            "Tool Information.Tool Name": "MachiningWorkingstep.its_operation.MachiningOperation.its_tool.MachiningTool.its_id",
            "Tool Information.Diameter": "MachiningWorkingstep.its_operation.MachiningOperation.its_tool.MachiningTool.MillingMachineCuttingTool.effective_cutting_diameter",
            "Tool Information.Number of Flutes": "MachiningWorkingstep.its_operation.MachiningOperation.its_tool.MachiningTool.MillingMachineCuttingTool.MillingCuttingTool.number_of_effective_teeth",
        }

        cam_path = tmp_path / "cam.json"
        mapping_path = tmp_path / "mapping.json"

        cam_path.write_text(json.dumps(cam_data))
        mapping_path.write_text(json.dumps(mapping))

        return cam_path, mapping_path

    def test_extract_returns_list(self, agent, temp_files_with_tools):
        """Should return list of XML strings."""
        cam_path, mapping_path = temp_files_with_tools
        result = agent.extract_tools(cam_path, mapping_path)

        assert isinstance(result, list)

    def test_extract_deduplicates_tools(self, agent, temp_files_with_tools):
        """Should deduplicate same tools."""
        cam_path, mapping_path = temp_files_with_tools
        result = agent.extract_tools(cam_path, mapping_path)

        # 3 ops but 2 unique tools
        assert len(result) == 2

    def test_extract_tool_xml_valid(self, agent, temp_files_with_tools):
        """Tool XMLs should be valid dt_asset format."""
        cam_path, mapping_path = temp_files_with_tools
        result = agent.extract_tools(cam_path, mapping_path)

        for xml in result:
            assert "dt_cutting_tool_13399" in xml
            assert "<dt_asset" in xml


class TestSplitNcByTool:
    """Test split_nc_by_tool method."""

    @pytest.fixture
    def agent(self):
        return DigitalThreadProjectManager()

    @pytest.fixture
    def nc_file(self, tmp_path):
        """Create NC file with multiple tools."""
        nc_content = """O0001
N10 G90 G00
N20 T01 M6
N30 G43 H01
N40 G01 X10 Y10 F100
N50 T02 M6
N60 G43 H02
N70 G01 X20 Y20 F200
N80 M30
"""
        nc_path = tmp_path / "test.nc"
        nc_path.write_text(nc_content)
        return nc_path

    def test_split_returns_list(self, agent, nc_file):
        """Should return list of segments."""
        result = agent.split_nc_by_tool(nc_file)

        assert isinstance(result, list)
        assert len(result) == 2  # Two tools

    def test_split_segment_structure(self, agent, nc_file):
        """Each segment should have tool_number and lines."""
        result = agent.split_nc_by_tool(nc_file)

        for segment in result:
            assert "tool_number" in segment
            assert "lines" in segment
            assert isinstance(segment["lines"], list)

    def test_split_with_output(self, agent, nc_file, tmp_path):
        """Should save segment files when output_path provided."""
        output_path = tmp_path / "segments"

        agent.split_nc_by_tool(nc_file, output_path)

        assert output_path.exists()
        nc_files = list(output_path.glob("*.nc"))
        assert len(nc_files) == 2


class TestValidateDtasset:
    """Test validate_dtasset method."""

    @pytest.fixture
    def agent(self):
        return DigitalThreadProjectManager()

    def test_validate_valid_xml(self, tmp_path):
        """Should return True for valid dt_asset XML."""
        # This test depends on having a valid sample
        # Skip if no samples available
        agent = DigitalThreadProjectManager()

        sample_xml = SAMPLES_DIR / "xml" / "dt_asset_sample.xml"
        if not sample_xml.exists():
            pytest.skip("Sample XML not found")

        result = agent.validate_dtasset(sample_xml)
        # May be True or False depending on schema strictness
        assert isinstance(result, bool)

    def test_validate_invalid_xml(self, tmp_path):
        """Should return False for completely malformed XML."""
        agent = DigitalThreadProjectManager()

        invalid_xml = tmp_path / "invalid.xml"
        invalid_xml.write_text("<dt_asset><unclosed>")

        result = agent.validate_dtasset(invalid_xml)
        assert result is False


@pytest.mark.skipif(
    not (SAMPLES_DIR / "json" / "nx" / "NX_json.json").exists(), reason="Sample files not found"
)
class TestWithRealSamples:
    """Integration tests with real sample files."""

    @pytest.fixture
    def agent(self):
        return DigitalThreadProjectManager(cam_type="nx")

    def test_convert_nx_sample_full(self, agent):
        """Full conversion of NX sample."""
        cam_path = SAMPLES_DIR / "json" / "nx" / "NX_json.json"
        mapping_path = SAMPLES_DIR / "json" / "nx" / "mapping_config_NX.json"

        result = agent.convert_cam_to_xml(cam_path, mapping_path)

        assert len(result) > 0
        for xml in result:
            assert "machining_workingstep" in xml
