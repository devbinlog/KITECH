"""
STEP AP242 PMI Reader Agent

Extracts PMI (Product Manufacturing Information) from STEP AP242 files.
Supports:
- Geometric Tolerances (GD&T)
- Dimensional Tolerances
- Datum Features
- Surface Finish
- Annotations
"""

import re
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


@dataclass
class DatumFeature:
    """Datum feature definition"""

    id: str
    label: str  # A, B, C, etc.
    referenced_geometry: Optional[str] = None


@dataclass
class GeometricTolerance:
    """Geometric tolerance (GD&T)"""

    id: str
    tolerance_type: str  # POSITION, FLATNESS, PERPENDICULARITY, etc.
    tolerance_value: float
    unit: str = "mm"
    datum_references: List[str] = field(default_factory=list)
    modified_geometry: Optional[str] = None


@dataclass
class DimensionalTolerance:
    """Dimensional tolerance"""

    id: str
    dimension_type: str  # LINEAR, ANGULAR, RADIAL
    nominal_value: float
    upper_limit: Optional[float] = None
    lower_limit: Optional[float] = None
    unit: str = "mm"


@dataclass
class SurfaceFinish:
    """Surface finish specification"""

    id: str
    roughness_value: float  # Ra value
    unit: str = "um"
    method: Optional[str] = None  # Machined, Ground, etc.


@dataclass
class PMIData:
    """Complete PMI data from STEP file"""

    file_name: str
    schema: str = "AP242"
    datums: List[DatumFeature] = field(default_factory=list)
    geometric_tolerances: List[GeometricTolerance] = field(default_factory=list)
    dimensional_tolerances: List[DimensionalTolerance] = field(default_factory=list)
    surface_finishes: List[SurfaceFinish] = field(default_factory=list)
    annotations: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_name": self.file_name,
            "schema": self.schema,
            "summary": {
                "datum_count": len(self.datums),
                "geometric_tolerance_count": len(self.geometric_tolerances),
                "dimensional_tolerance_count": len(self.dimensional_tolerances),
                "surface_finish_count": len(self.surface_finishes),
                "annotation_count": len(self.annotations),
            },
            "datums": [asdict(d) for d in self.datums],
            "geometric_tolerances": [asdict(t) for t in self.geometric_tolerances],
            "dimensional_tolerances": [asdict(t) for t in self.dimensional_tolerances],
            "surface_finishes": [asdict(s) for s in self.surface_finishes],
            "annotations": self.annotations,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert PMI data to JSON string"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def save_json(self, output_path: Union[str, Path], indent: int = 2) -> Path:
        """Save PMI data to JSON file"""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json(indent), encoding="utf-8")
        return path


class StepPmiReaderAgent:
    """
    Agent for reading PMI data from STEP AP242 files.

    STEP AP242 supports semantic PMI with machine-readable tolerance data.
    This agent extracts:
    - Datum features (A, B, C, ...)
    - Geometric tolerances (position, flatness, perpendicularity, etc.)
    - Dimensional tolerances (linear, angular, radial)
    - Surface finish specifications
    - Annotations and notes
    """

    # STEP entity patterns for PMI
    PMI_ENTITIES = {
        "datum": [
            "DATUM",
            "DATUM_FEATURE",
            "DATUM_REFERENCE",
            "DATUM_TARGET",
        ],
        "geometric_tolerance": [
            "GEOMETRIC_TOLERANCE",
            "GEOMETRIC_TOLERANCE_WITH_DATUM_REFERENCE",
            "POSITION_TOLERANCE",
            "FLATNESS_TOLERANCE",
            "PERPENDICULARITY_TOLERANCE",
            "PARALLELISM_TOLERANCE",
            "CONCENTRICITY_TOLERANCE",
            "SYMMETRY_TOLERANCE",
            "CYLINDRICITY_TOLERANCE",
            "CIRCULARITY_TOLERANCE",
            "STRAIGHTNESS_TOLERANCE",
            "SURFACE_PROFILE_TOLERANCE",
            "LINE_PROFILE_TOLERANCE",
            "ANGULARITY_TOLERANCE",
            "RUNOUT_TOLERANCE",
            "TOTAL_RUNOUT_TOLERANCE",
        ],
        "dimensional_tolerance": [
            "DIMENSIONAL_SIZE",
            "DIMENSIONAL_LOCATION",
            "DIMENSIONAL_SIZE_WITH_PATH",
            "ANGULAR_DIMENSION",
            "LINEAR_DIMENSION",
            "RADIAL_DIMENSION",
            "DIAMETER_DIMENSION",
            "PLUS_MINUS_TOLERANCE",
            "TOLERANCE_VALUE",
        ],
        "surface_finish": [
            "SURFACE_TEXTURE_PARAMETER",
            "SURFACE_ROUGHNESS",
            "MACHINING_ALLOWANCE",
        ],
        "annotation": [
            "ANNOTATION_OCCURRENCE",
            "ANNOTATION_PLANE",
            "DRAUGHTING_ANNOTATION_OCCURRENCE",
            "DRAUGHTING_CALLOUT",
            "LEADER_CURVE",
            "DIMENSION_CALLOUT",
        ],
    }

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "step-pmi-reader"
        logger.info("StepPmiReaderAgent initialized")

    def process(
        self, input_data: Any, output_json: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        """
        Process STEP file and extract PMI data.

        Args:
            input_data: Path to STEP file or STEP content string
            output_json: Optional path to save PMI data as JSON file

        Returns:
            Dictionary with PMI data
        """
        try:
            logger.info("Processing STEP file for PMI extraction...")

            # Get file content
            if isinstance(input_data, str):
                if Path(input_data).exists():
                    file_path = Path(input_data)
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    file_name = file_path.name
                else:
                    content = input_data
                    file_name = "inline_step"
            else:
                return {"status": "error", "message": "Invalid input type"}

            # Parse STEP content
            pmi_data = self._parse_step_pmi(content, file_name)

            logger.info(
                f"PMI extraction complete: "
                f"{len(pmi_data.datums)} datums, "
                f"{len(pmi_data.geometric_tolerances)} GD&T, "
                f"{len(pmi_data.dimensional_tolerances)} dimensions"
            )

            result = {
                "status": "success",
                "message": f"Extracted PMI from {file_name}",
                "data": pmi_data.to_dict(),
            }

            # Save to JSON file if output path provided
            if output_json:
                saved_path = pmi_data.save_json(output_json)
                result["output_file"] = str(saved_path)
                logger.info(f"PMI data saved to {saved_path}")

            return result

        except Exception as e:
            logger.error(f"PMI extraction failed: {e}")
            return {"status": "error", "message": str(e)}

    def extract_pmi_json(
        self, input_data: Any, output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract PMI data and return as JSON string or save to file.

        Args:
            input_data: Path to STEP file or STEP content string
            output_path: Optional path to save JSON file (if None, returns JSON string)

        Returns:
            Dictionary with status and JSON data/file path
        """
        result = self.process(input_data)

        if result["status"] != "success":
            return result

        pmi_dict = result["data"]

        if output_path:
            # Save to file
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(pmi_dict, indent=2, ensure_ascii=False), encoding="utf-8")
            return {
                "status": "success",
                "message": f"PMI saved to {path}",
                "output_file": str(path),
            }
        else:
            # Return JSON string
            return {
                "status": "success",
                "json": json.dumps(pmi_dict, indent=2, ensure_ascii=False),
                "data": pmi_dict,
            }

    def get_pmi_data(self, input_data: Any) -> Optional[PMIData]:
        """
        Extract and return PMIData object directly (for programmatic use).

        Args:
            input_data: Path to STEP file or STEP content string

        Returns:
            PMIData object or None on error
        """
        try:
            if isinstance(input_data, str):
                if Path(input_data).exists():
                    file_path = Path(input_data)
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    file_name = file_path.name
                else:
                    content = input_data
                    file_name = "inline_step"
            else:
                return None

            return self._parse_step_pmi(content, file_name)
        except Exception as e:
            logger.error(f"Failed to get PMI data: {e}")
            return None

    def _parse_step_pmi(self, content: str, file_name: str) -> PMIData:
        """Parse STEP content and extract PMI entities"""

        pmi_data = PMIData(file_name=file_name)

        # Detect schema
        if "AP242" in content or "AUTOMOTIVE_DESIGN" in content:
            pmi_data.schema = "AP242"
        elif "AP214" in content:
            pmi_data.schema = "AP214"
        elif "AP203" in content or "CONFIG_CONTROL_DESIGN" in content:
            pmi_data.schema = "AP203"

        # Extract entities line by line
        lines = content.split("\n")
        entity_pattern = re.compile(r"^#(\d+)\s*=\s*([A-Z_]+)\s*\((.*)\)\s*;", re.IGNORECASE)

        entities = {}
        for line in lines:
            line = line.strip()
            match = entity_pattern.match(line)
            if match:
                entity_id = match.group(1)
                entity_type = match.group(2).upper()
                entity_data = match.group(3)
                entities[entity_id] = {"type": entity_type, "data": entity_data, "raw": line}

        # Extract datums
        for entity_id, entity in entities.items():
            if entity["type"] in self.PMI_ENTITIES["datum"]:
                datum = self._parse_datum(entity_id, entity)
                if datum:
                    pmi_data.datums.append(datum)

        # Extract geometric tolerances
        for entity_id, entity in entities.items():
            if entity["type"] in self.PMI_ENTITIES["geometric_tolerance"]:
                tol = self._parse_geometric_tolerance(entity_id, entity)
                if tol:
                    pmi_data.geometric_tolerances.append(tol)

        # Extract dimensional tolerances
        for entity_id, entity in entities.items():
            if entity["type"] in self.PMI_ENTITIES["dimensional_tolerance"]:
                dim = self._parse_dimensional_tolerance(entity_id, entity)
                if dim:
                    pmi_data.dimensional_tolerances.append(dim)

        # Extract surface finish
        for entity_id, entity in entities.items():
            if entity["type"] in self.PMI_ENTITIES["surface_finish"]:
                sf = self._parse_surface_finish(entity_id, entity)
                if sf:
                    pmi_data.surface_finishes.append(sf)

        # Extract annotations
        for entity_id, entity in entities.items():
            if entity["type"] in self.PMI_ENTITIES["annotation"]:
                ann = self._parse_annotation(entity_id, entity)
                if ann:
                    pmi_data.annotations.append(ann)

        return pmi_data

    def _parse_datum(self, entity_id: str, entity: Dict) -> Optional[DatumFeature]:
        """Parse datum feature entity"""
        try:
            data = entity["data"]
            # Extract label (usually single letter like 'A', 'B', 'C')
            label_match = re.search(r"'([A-Z])'", data)
            label = label_match.group(1) if label_match else f"D{entity_id}"

            return DatumFeature(id=f"#{entity_id}", label=label)
        except Exception:
            return None

    def _parse_geometric_tolerance(
        self, entity_id: str, entity: Dict
    ) -> Optional[GeometricTolerance]:
        """Parse geometric tolerance entity"""
        try:
            data = entity["data"]
            entity_type = entity["type"]

            # Determine tolerance type from entity name
            tol_type = entity_type.replace("_TOLERANCE", "").replace("GEOMETRIC_", "")

            # Extract tolerance value
            value_match = re.search(r"(\d+\.?\d*)", data)
            value = float(value_match.group(1)) if value_match else 0.0

            # Extract datum references
            datum_refs = re.findall(r"#(\d+)", data)

            return GeometricTolerance(
                id=f"#{entity_id}",
                tolerance_type=tol_type,
                tolerance_value=value,
                datum_references=[f"#{ref}" for ref in datum_refs[:3]],  # Max 3 datums
            )
        except Exception:
            return None

    def _parse_dimensional_tolerance(
        self, entity_id: str, entity: Dict
    ) -> Optional[DimensionalTolerance]:
        """Parse dimensional tolerance entity"""
        try:
            data = entity["data"]
            entity_type = entity["type"]

            # Determine dimension type
            if "ANGULAR" in entity_type:
                dim_type = "ANGULAR"
            elif "RADIAL" in entity_type or "DIAMETER" in entity_type:
                dim_type = "RADIAL"
            else:
                dim_type = "LINEAR"

            # Extract values
            values = re.findall(r"(\d+\.?\d*)", data)
            nominal = float(values[0]) if values else 0.0
            upper = float(values[1]) if len(values) > 1 else None
            lower = float(values[2]) if len(values) > 2 else None

            return DimensionalTolerance(
                id=f"#{entity_id}",
                dimension_type=dim_type,
                nominal_value=nominal,
                upper_limit=upper,
                lower_limit=lower,
            )
        except Exception:
            return None

    def _parse_surface_finish(self, entity_id: str, entity: Dict) -> Optional[SurfaceFinish]:
        """Parse surface finish entity"""
        try:
            data = entity["data"]

            # Extract Ra value
            value_match = re.search(r"(\d+\.?\d*)", data)
            ra_value = float(value_match.group(1)) if value_match else 0.0

            return SurfaceFinish(id=f"#{entity_id}", roughness_value=ra_value)
        except Exception:
            return None

    def _parse_annotation(self, entity_id: str, entity: Dict) -> Optional[Dict[str, Any]]:
        """Parse annotation entity"""
        try:
            return {
                "id": f"#{entity_id}",
                "type": entity["type"],
                "data": entity["data"][:100],  # Truncate
            }
        except Exception:
            return None
