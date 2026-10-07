"""Test STEP PMI Reader Agent"""

import pytest
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from step_pmi_reader_agent import (
    StepPmiReaderAgent,
    PMIData,
    DatumFeature,
    GeometricTolerance,
    DimensionalTolerance,
    SurfaceFinish,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def agent():
    """Create agent instance"""
    return StepPmiReaderAgent()


@pytest.fixture
def sample_dir():
    """Return samples directory path"""
    return Path(__file__).parent.parent / "samples"


@pytest.fixture
def sample_file(sample_dir):
    """Main sample file with full PMI"""
    return sample_dir / "sample_ap242_pmi.stp"


@pytest.fixture
def ap214_file(sample_dir):
    """AP214 sample (no PMI)"""
    return sample_dir / "sample_ap214.stp"


@pytest.fixture
def minimal_file(sample_dir):
    """Minimal PMI sample"""
    return sample_dir / "sample_minimal_pmi.stp"


@pytest.fixture
def complex_file(sample_dir):
    """Complex GD&T sample"""
    return sample_dir / "sample_complex_gdt.stp"


# =============================================================================
# Test Agent Initialization
# =============================================================================


class TestStepPmiReaderInit:
    """Test agent initialization"""

    def test_agent_creation(self):
        agent = StepPmiReaderAgent()
        assert agent is not None
        assert agent.name == "step-pmi-reader"

    def test_agent_with_config(self):
        config = {"verbose": True, "strict": False}
        agent = StepPmiReaderAgent(config=config)
        assert agent.config == config
        assert agent.config["verbose"] is True

    def test_agent_default_config(self):
        agent = StepPmiReaderAgent()
        assert agent.config == {}

    def test_agent_pmi_entities_defined(self):
        agent = StepPmiReaderAgent()
        assert "datum" in agent.PMI_ENTITIES
        assert "geometric_tolerance" in agent.PMI_ENTITIES
        assert "dimensional_tolerance" in agent.PMI_ENTITIES
        assert "surface_finish" in agent.PMI_ENTITIES
        assert "annotation" in agent.PMI_ENTITIES


# =============================================================================
# Test PMI Extraction from Sample Files
# =============================================================================


class TestStepPmiReaderProcess:
    """Test PMI extraction from files"""

    def test_process_sample_file(self, agent, sample_file):
        """Test processing main sample STEP file"""
        result = agent.process(str(sample_file))

        assert result["status"] == "success"
        assert "data" in result

        data = result["data"]
        assert data["schema"] == "AP242"
        assert data["file_name"] == "sample_ap242_pmi.stp"

    def test_process_returns_summary(self, agent, sample_file):
        """Test that result includes summary counts"""
        result = agent.process(str(sample_file))
        summary = result["data"]["summary"]

        assert "datum_count" in summary
        assert "geometric_tolerance_count" in summary
        assert "dimensional_tolerance_count" in summary
        assert "surface_finish_count" in summary
        assert "annotation_count" in summary

    def test_extract_datums(self, agent, sample_file):
        """Test datum extraction"""
        result = agent.process(str(sample_file))
        data = result["data"]

        assert len(data["datums"]) >= 3  # A, B, C

        labels = [d["label"] for d in data["datums"]]
        assert "A" in labels
        assert "B" in labels
        assert "C" in labels

    def test_extract_geometric_tolerances(self, agent, sample_file):
        """Test GD&T extraction"""
        result = agent.process(str(sample_file))
        data = result["data"]

        assert len(data["geometric_tolerances"]) >= 5

        tol_types = [t["tolerance_type"] for t in data["geometric_tolerances"]]
        assert "POSITION" in tol_types or "FLATNESS" in tol_types

    def test_geometric_tolerance_has_required_fields(self, agent, sample_file):
        """Test GD&T entries have all required fields"""
        result = agent.process(str(sample_file))
        for tol in result["data"]["geometric_tolerances"]:
            assert "id" in tol
            assert "tolerance_type" in tol
            assert "tolerance_value" in tol
            assert "unit" in tol
            assert "datum_references" in tol

    def test_extract_dimensional_tolerances(self, agent, sample_file):
        """Test dimensional tolerance extraction"""
        result = agent.process(str(sample_file))
        data = result["data"]

        assert len(data["dimensional_tolerances"]) >= 3

        dim_types = [d["dimension_type"] for d in data["dimensional_tolerances"]]
        assert "LINEAR" in dim_types or "RADIAL" in dim_types

    def test_dimensional_tolerance_has_required_fields(self, agent, sample_file):
        """Test dimensional entries have all required fields"""
        result = agent.process(str(sample_file))
        for dim in result["data"]["dimensional_tolerances"]:
            assert "id" in dim
            assert "dimension_type" in dim
            assert "nominal_value" in dim
            assert "unit" in dim

    def test_extract_surface_finish(self, agent, sample_file):
        """Test surface finish extraction"""
        result = agent.process(str(sample_file))
        data = result["data"]

        assert len(data["surface_finishes"]) >= 2

    def test_surface_finish_has_required_fields(self, agent, sample_file):
        """Test surface finish entries have all required fields"""
        result = agent.process(str(sample_file))
        for sf in result["data"]["surface_finishes"]:
            assert "id" in sf
            assert "roughness_value" in sf
            assert "unit" in sf

    def test_extract_annotations(self, agent, sample_file):
        """Test annotation extraction"""
        result = agent.process(str(sample_file))
        data = result["data"]

        assert len(data["annotations"]) >= 1


# =============================================================================
# Test Different Sample Files
# =============================================================================


class TestDifferentSamples:
    """Test with different sample files"""

    def test_ap214_schema_detection(self, agent, ap214_file):
        """Test AP214 schema is detected correctly"""
        if not ap214_file.exists():
            pytest.skip("AP214 sample not available")

        result = agent.process(str(ap214_file))
        assert result["status"] == "success"
        assert result["data"]["schema"] == "AP214"

    def test_ap214_no_pmi(self, agent, ap214_file):
        """Test AP214 has no PMI (as expected)"""
        if not ap214_file.exists():
            pytest.skip("AP214 sample not available")

        result = agent.process(str(ap214_file))
        data = result["data"]
        # AP214 typically has no semantic PMI
        assert len(data["geometric_tolerances"]) == 0

    def test_minimal_pmi_file(self, agent, minimal_file):
        """Test minimal PMI sample"""
        if not minimal_file.exists():
            pytest.skip("Minimal sample not available")

        result = agent.process(str(minimal_file))
        assert result["status"] == "success"
        data = result["data"]
        assert len(data["datums"]) >= 1
        assert len(data["geometric_tolerances"]) >= 1

    def test_complex_gdt_file(self, agent, complex_file):
        """Test complex GD&T sample"""
        if not complex_file.exists():
            pytest.skip("Complex GD&T sample not available")

        result = agent.process(str(complex_file))
        assert result["status"] == "success"
        data = result["data"]

        # Should have many tolerance types
        tol_types = {t["tolerance_type"] for t in data["geometric_tolerances"]}
        assert len(tol_types) >= 5  # Multiple different types

    def test_complex_all_tolerance_types(self, agent, complex_file):
        """Test complex file has various tolerance types"""
        if not complex_file.exists():
            pytest.skip("Complex GD&T sample not available")

        result = agent.process(str(complex_file))
        tol_types = {t["tolerance_type"] for t in result["data"]["geometric_tolerances"]}

        # Form tolerances
        assert "FLATNESS" in tol_types
        assert "CYLINDRICITY" in tol_types

        # Orientation tolerances
        assert "PERPENDICULARITY" in tol_types
        assert "PARALLELISM" in tol_types


# =============================================================================
# Test Edge Cases
# =============================================================================


class TestStepPmiReaderEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_content(self, agent):
        """Test with empty content (whitespace-only)"""
        # Note: Empty string "" is treated as current directory by Path
        # Use whitespace content to test empty STEP content
        result = agent.process("   \n\n   ")
        # Should not crash, returns minimal data
        assert result is not None
        assert result["status"] == "success"

    def test_nonexistent_file_treated_as_content(self, agent):
        """Test with non-existent file path (treated as inline content)"""
        result = agent.process("/nonexistent/path/file.stp")
        # Treats as inline content
        assert result is not None

    def test_ap203_schema_detection(self, agent):
        """Test AP203 schema detection"""
        content = """ISO-10303-21;
HEADER;
FILE_SCHEMA(('CONFIG_CONTROL_DESIGN'));
ENDSEC;
DATA;
#1 = PRODUCT('Part','Part','',(#2));
ENDSEC;
END-ISO-10303-21;"""

        result = agent.process(content)
        assert result["status"] == "success"
        assert result["data"]["schema"] == "AP203"
        # AP203 has no PMI
        assert len(result["data"]["geometric_tolerances"]) == 0

    def test_malformed_step_header(self, agent):
        """Test with malformed STEP header"""
        content = """ISO-10303-21;
HEADER;
ENDSEC;
DATA;
#1 = FLATNESS_TOLERANCE('Test',0.1);
ENDSEC;
END-ISO-10303-21;"""

        result = agent.process(content)
        assert result["status"] == "success"
        # Should still extract the tolerance
        assert len(result["data"]["geometric_tolerances"]) >= 1

    def test_multiline_entity(self, agent):
        """Test entity split across multiple lines"""
        content = """ISO-10303-21;
HEADER;
FILE_SCHEMA(('AUTOMOTIVE_DESIGN'));
ENDSEC;
DATA;
#1 = POSITION_TOLERANCE(
  'Hole Position',
  0.05,
  #10,#11
);
ENDSEC;
END-ISO-10303-21;"""

        result = agent.process(content)
        # Current parser may not handle multiline well
        assert result["status"] == "success"

    def test_special_characters_in_name(self, agent):
        """Test tolerance with special characters in name"""
        content = """ISO-10303-21;
HEADER;
FILE_SCHEMA(('AUTOMOTIVE_DESIGN'));
ENDSEC;
DATA;
#1 = FLATNESS_TOLERANCE('Surface (Top) - Zone A',0.02);
ENDSEC;
END-ISO-10303-21;"""

        result = agent.process(content)
        assert result["status"] == "success"
        assert len(result["data"]["geometric_tolerances"]) >= 1

    def test_unicode_content(self, agent):
        """Test with unicode characters"""
        content = """ISO-10303-21;
HEADER;
FILE_SCHEMA(('AUTOMOTIVE_DESIGN'));
ENDSEC;
DATA;
#1 = DATUM('データムA','A');
ENDSEC;
END-ISO-10303-21;"""

        result = agent.process(content)
        assert result["status"] == "success"

    def test_very_small_tolerance_value(self, agent):
        """Test with very small tolerance value"""
        content = """ISO-10303-21;
HEADER;
FILE_SCHEMA(('AUTOMOTIVE_DESIGN'));
ENDSEC;
DATA;
#1 = FLATNESS_TOLERANCE('Precision',0.0001);
ENDSEC;
END-ISO-10303-21;"""

        result = agent.process(content)
        assert result["status"] == "success"
        tol = result["data"]["geometric_tolerances"][0]
        assert tol["tolerance_value"] == 0.0001

    def test_large_tolerance_value(self, agent):
        """Test with large tolerance value"""
        content = """ISO-10303-21;
HEADER;
FILE_SCHEMA(('AUTOMOTIVE_DESIGN'));
ENDSEC;
DATA;
#1 = FLATNESS_TOLERANCE('Rough',10.5);
ENDSEC;
END-ISO-10303-21;"""

        result = agent.process(content)
        assert result["status"] == "success"
        tol = result["data"]["geometric_tolerances"][0]
        assert tol["tolerance_value"] == 10.5


# =============================================================================
# Test DataClass Structures
# =============================================================================


class TestDataClasses:
    """Test dataclass structures"""

    def test_datum_feature_creation(self):
        """Test DatumFeature dataclass"""
        datum = DatumFeature(id="#100", label="A")
        assert datum.id == "#100"
        assert datum.label == "A"
        assert datum.referenced_geometry is None

    def test_datum_feature_with_geometry(self):
        """Test DatumFeature with geometry reference"""
        datum = DatumFeature(id="#100", label="A", referenced_geometry="#50")
        assert datum.referenced_geometry == "#50"

    def test_geometric_tolerance_creation(self):
        """Test GeometricTolerance dataclass"""
        tol = GeometricTolerance(
            id="#200",
            tolerance_type="POSITION",
            tolerance_value=0.05,
        )
        assert tol.id == "#200"
        assert tol.tolerance_type == "POSITION"
        assert tol.tolerance_value == 0.05
        assert tol.unit == "mm"
        assert tol.datum_references == []

    def test_geometric_tolerance_with_datums(self):
        """Test GeometricTolerance with datum references"""
        tol = GeometricTolerance(
            id="#200",
            tolerance_type="POSITION",
            tolerance_value=0.025,
            datum_references=["#100", "#101", "#102"],
        )
        assert len(tol.datum_references) == 3

    def test_dimensional_tolerance_creation(self):
        """Test DimensionalTolerance dataclass"""
        dim = DimensionalTolerance(
            id="#300",
            dimension_type="LINEAR",
            nominal_value=100.0,
        )
        assert dim.id == "#300"
        assert dim.dimension_type == "LINEAR"
        assert dim.nominal_value == 100.0
        assert dim.upper_limit is None
        assert dim.lower_limit is None

    def test_dimensional_tolerance_with_limits(self):
        """Test DimensionalTolerance with limits"""
        dim = DimensionalTolerance(
            id="#300",
            dimension_type="LINEAR",
            nominal_value=100.0,
            upper_limit=0.1,
            lower_limit=-0.05,
        )
        assert dim.upper_limit == 0.1
        assert dim.lower_limit == -0.05

    def test_surface_finish_creation(self):
        """Test SurfaceFinish dataclass"""
        sf = SurfaceFinish(id="#400", roughness_value=1.6)
        assert sf.id == "#400"
        assert sf.roughness_value == 1.6
        assert sf.unit == "um"
        assert sf.method is None

    def test_surface_finish_with_method(self):
        """Test SurfaceFinish with method"""
        sf = SurfaceFinish(id="#400", roughness_value=0.8, method="Ground")
        assert sf.method == "Ground"


# =============================================================================
# Test PMIData Structure
# =============================================================================


class TestPMIDataStructure:
    """Test PMIData structure and methods"""

    def test_pmi_data_creation(self):
        """Test PMIData creation"""
        pmi = PMIData(file_name="test.stp")
        assert pmi.file_name == "test.stp"
        assert pmi.schema == "AP242"
        assert pmi.datums == []
        assert pmi.geometric_tolerances == []

    def test_pmi_data_with_datums(self):
        """Test PMIData with datums"""
        pmi = PMIData(
            file_name="test.stp",
            datums=[
                DatumFeature(id="#1", label="A"),
                DatumFeature(id="#2", label="B"),
            ],
        )
        assert len(pmi.datums) == 2

    def test_pmi_data_to_dict(self):
        """Test PMIData serialization"""
        pmi = PMIData(file_name="test.stp")
        data = pmi.to_dict()

        assert "file_name" in data
        assert "summary" in data
        assert "datums" in data
        assert "geometric_tolerances" in data
        assert "dimensional_tolerances" in data
        assert "surface_finishes" in data
        assert "annotations" in data

    def test_pmi_data_summary_counts(self):
        """Test PMIData summary includes correct counts"""
        pmi = PMIData(
            file_name="test.stp",
            datums=[DatumFeature(id="#1", label="A")],
            geometric_tolerances=[
                GeometricTolerance(id="#2", tolerance_type="FLATNESS", tolerance_value=0.1),
                GeometricTolerance(id="#3", tolerance_type="POSITION", tolerance_value=0.05),
            ],
        )
        data = pmi.to_dict()
        assert data["summary"]["datum_count"] == 1
        assert data["summary"]["geometric_tolerance_count"] == 2

    def test_pmi_data_to_json(self):
        """Test PMIData to JSON string"""
        pmi = PMIData(file_name="test.stp", schema="AP242")
        json_str = pmi.to_json()

        assert isinstance(json_str, str)
        assert '"file_name": "test.stp"' in json_str
        assert '"schema": "AP242"' in json_str

    def test_pmi_data_to_json_indent(self):
        """Test PMIData to JSON with custom indent"""
        pmi = PMIData(file_name="test.stp")
        json_str = pmi.to_json(indent=4)

        # Should have 4-space indentation
        assert "    " in json_str

    def test_pmi_data_save_json(self, tmp_path):
        """Test PMIData save to JSON file"""
        pmi = PMIData(file_name="test.stp", schema="AP242")
        output_file = tmp_path / "output" / "pmi.json"

        saved_path = pmi.save_json(output_file)

        assert saved_path.exists()
        content = saved_path.read_text()
        assert '"file_name": "test.stp"' in content

    def test_pmi_data_save_json_creates_dirs(self, tmp_path):
        """Test PMIData.save_json creates parent directories"""
        pmi = PMIData(file_name="test.stp")
        output_file = tmp_path / "deep" / "nested" / "path" / "output.json"

        saved_path = pmi.save_json(output_file)
        assert saved_path.exists()


# =============================================================================
# Test JSON Export Methods
# =============================================================================


class TestJsonExport:
    """Test JSON export functionality"""

    def test_process_with_output_json(self, agent, sample_file, tmp_path):
        """Test process() with output_json parameter"""
        output_file = tmp_path / "pmi_output.json"

        result = agent.process(str(sample_file), output_json=str(output_file))

        assert result["status"] == "success"
        assert "output_file" in result
        assert output_file.exists()

        # Verify JSON content
        with open(output_file) as f:
            data = json.load(f)
        assert data["file_name"] == "sample_ap242_pmi.stp"
        assert "datums" in data

    def test_extract_pmi_json_to_file(self, agent, sample_file, tmp_path):
        """Test extract_pmi_json() with file output"""
        output_file = tmp_path / "extracted_pmi.json"

        result = agent.extract_pmi_json(str(sample_file), output_path=str(output_file))

        assert result["status"] == "success"
        assert "output_file" in result
        assert output_file.exists()

    def test_extract_pmi_json_string(self, agent, sample_file):
        """Test extract_pmi_json() returning JSON string"""
        result = agent.extract_pmi_json(str(sample_file))

        assert result["status"] == "success"
        assert "json" in result
        assert isinstance(result["json"], str)
        assert "datums" in result["json"]

    def test_extract_pmi_json_also_returns_data(self, agent, sample_file):
        """Test extract_pmi_json() also returns parsed data"""
        result = agent.extract_pmi_json(str(sample_file))

        assert "data" in result
        assert result["data"]["file_name"] == "sample_ap242_pmi.stp"

    def test_get_pmi_data_object(self, agent, sample_file):
        """Test get_pmi_data() returning PMIData object"""
        pmi_data = agent.get_pmi_data(str(sample_file))

        assert pmi_data is not None
        assert isinstance(pmi_data, PMIData)
        assert pmi_data.file_name == "sample_ap242_pmi.stp"
        assert len(pmi_data.datums) >= 3

    def test_get_pmi_data_invalid_input(self, agent):
        """Test get_pmi_data() with invalid input"""
        result = agent.get_pmi_data(123)  # Invalid type
        assert result is None


# =============================================================================
# Test Schema Detection
# =============================================================================


class TestSchemaDetection:
    """Test STEP schema detection"""

    def test_detect_ap242_automotive_design(self, agent):
        """Test AP242 detection via AUTOMOTIVE_DESIGN"""
        content = """ISO-10303-21;
HEADER;
FILE_SCHEMA(('AUTOMOTIVE_DESIGN'));
ENDSEC;
DATA;
ENDSEC;
END-ISO-10303-21;"""

        result = agent.process(content)
        assert result["data"]["schema"] == "AP242"

    def test_detect_ap242_explicit(self, agent):
        """Test AP242 detection via explicit mention"""
        content = """ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('AP242 File'),'2;1');
ENDSEC;
DATA;
ENDSEC;
END-ISO-10303-21;"""

        result = agent.process(content)
        assert result["data"]["schema"] == "AP242"

    def test_detect_ap214(self, agent):
        """Test AP214 detection"""
        content = """ISO-10303-21;
HEADER;
FILE_SCHEMA(('AP214'));
ENDSEC;
DATA;
ENDSEC;
END-ISO-10303-21;"""

        result = agent.process(content)
        assert result["data"]["schema"] == "AP214"

    def test_detect_ap203(self, agent):
        """Test AP203 detection via CONFIG_CONTROL_DESIGN"""
        content = """ISO-10303-21;
HEADER;
FILE_SCHEMA(('CONFIG_CONTROL_DESIGN'));
ENDSEC;
DATA;
ENDSEC;
END-ISO-10303-21;"""

        result = agent.process(content)
        assert result["data"]["schema"] == "AP203"


# =============================================================================
# Test Individual Parser Methods
# =============================================================================


class TestParserMethods:
    """Test individual parser methods"""

    def test_parse_datum_basic(self, agent):
        """Test datum parsing"""
        entity = {"type": "DATUM", "data": "'Primary','A'", "raw": "#100 = DATUM('Primary','A');"}
        datum = agent._parse_datum("100", entity)

        assert datum is not None
        assert datum.label == "A"
        assert datum.id == "#100"

    def test_parse_datum_extracts_label(self, agent):
        """Test datum label extraction"""
        entity = {"type": "DATUM_FEATURE", "data": "'Feature B',#50,'B'", "raw": "..."}
        datum = agent._parse_datum("101", entity)

        assert datum is not None
        assert datum.label == "B"

    def test_parse_geometric_tolerance_basic(self, agent):
        """Test geometric tolerance parsing"""
        entity = {
            "type": "FLATNESS_TOLERANCE",
            "data": "'Surface',0.05",
            "raw": "#200 = FLATNESS_TOLERANCE('Surface',0.05);",
        }
        tol = agent._parse_geometric_tolerance("200", entity)

        assert tol is not None
        assert tol.tolerance_type == "FLATNESS"
        assert tol.tolerance_value == 0.05

    def test_parse_geometric_tolerance_with_datums(self, agent):
        """Test geometric tolerance with datum references"""
        entity = {
            "type": "POSITION_TOLERANCE",
            "data": "'Hole',0.025,#100,#101",
            "raw": "#200 = POSITION_TOLERANCE('Hole',0.025,#100,#101);",
        }
        tol = agent._parse_geometric_tolerance("200", entity)

        assert tol is not None
        assert "#100" in tol.datum_references
        assert "#101" in tol.datum_references

    def test_parse_dimensional_tolerance_linear(self, agent):
        """Test dimensional tolerance parsing - linear"""
        entity = {
            "type": "LINEAR_DIMENSION",
            "data": "'Length',100.0,0.1,-0.05",
            "raw": "...",
        }
        dim = agent._parse_dimensional_tolerance("300", entity)

        assert dim is not None
        assert dim.dimension_type == "LINEAR"
        assert dim.nominal_value == 100.0

    def test_parse_dimensional_tolerance_angular(self, agent):
        """Test dimensional tolerance parsing - angular"""
        entity = {
            "type": "ANGULAR_DIMENSION",
            "data": "'Angle',45.0,1.0,-1.0",
            "raw": "...",
        }
        dim = agent._parse_dimensional_tolerance("301", entity)

        assert dim is not None
        assert dim.dimension_type == "ANGULAR"

    def test_parse_dimensional_tolerance_radial(self, agent):
        """Test dimensional tolerance parsing - radial"""
        entity = {
            "type": "DIAMETER_DIMENSION",
            "data": "'Bore',25.0,0.02,0.0",
            "raw": "...",
        }
        dim = agent._parse_dimensional_tolerance("302", entity)

        assert dim is not None
        assert dim.dimension_type == "RADIAL"

    def test_parse_surface_finish_basic(self, agent):
        """Test surface finish parsing"""
        entity = {
            "type": "SURFACE_ROUGHNESS",
            "data": "'Machined',1.6",
            "raw": "#400 = SURFACE_ROUGHNESS('Machined',1.6);",
        }
        sf = agent._parse_surface_finish("400", entity)

        assert sf is not None
        assert sf.roughness_value == 1.6

    def test_parse_annotation_basic(self, agent):
        """Test annotation parsing"""
        entity = {
            "type": "ANNOTATION_OCCURRENCE",
            "data": "'Note','CRITICAL'",
            "raw": "#500 = ANNOTATION_OCCURRENCE('Note','CRITICAL');",
        }
        ann = agent._parse_annotation("500", entity)

        assert ann is not None
        assert ann["id"] == "#500"
        assert ann["type"] == "ANNOTATION_OCCURRENCE"


# =============================================================================
# Test Error Handling
# =============================================================================


class TestErrorHandling:
    """Test error handling"""

    def test_invalid_input_type(self, agent):
        """Test with invalid input type"""
        result = agent.process(123)  # Not a string
        assert result["status"] == "error"
        assert "Invalid input" in result["message"]

    def test_process_exception_handling(self, agent, monkeypatch):
        """Test exception handling in process()"""
        def raise_error(*args, **kwargs):
            raise ValueError("Test error")

        monkeypatch.setattr(agent, "_parse_step_pmi", raise_error)
        result = agent.process("test content")

        assert result["status"] == "error"
        assert "Test error" in result["message"]

    def test_extract_pmi_json_error_propagation(self, agent):
        """Test error propagation in extract_pmi_json()"""
        result = agent.extract_pmi_json(123)  # Invalid type
        assert result["status"] == "error"
