# Digital Thread Project Manager

CAM to ISO 14649 XML converter for Digital Thread projects.

## Features

- **CAM Parsers**: NX and PowerMill JSON parsing
- **XML Converter**: CAM operations to ISO 14649 workingstep XML
- **Tool Extraction**: ISO 13399 cutting tool data from CAM
- **NC Splitter**: Split NC files by tool change (T/M6)
- **Schema Validation**: xsdata-based dt_asset validation

## Installation

```bash
cd agents/digital-thread-project-manager
uv sync
```

## Usage

### Python API

```python
from src import DigitalThreadProjectManager

# Initialize agent
agent = DigitalThreadProjectManager(cam_type="nx")

# Convert CAM JSON to workingstep XMLs
xmls = agent.convert_cam_to_xml(
    cam_path="path/to/cam.json",
    mapping_path="path/to/mapping.json",
    output_path="output/"  # optional
)

# Extract ISO 13399 tool data
tools = agent.extract_tools(
    cam_path="path/to/cam.json",
    mapping_path="path/to/mapping.json",
    global_asset_id="http://example.com/tools",
    base_asset_id="tool",
)

# Split NC file by tool
segments = agent.split_nc_by_tool(
    nc_path="path/to/program.nc",
    output_path="output/nc/"
)
```

### Direct Converter Usage

```python
from src.converters import CamConverter

converter = CamConverter(cam_type="nx")

# Load CAM and mapping
with open("cam.json") as f:
    cam_json = json.load(f)
with open("mapping.json") as f:
    mapping = json.load(f)

# Extract operations
ops = converter.pick_ops(cam_json)

# Convert each operation to XML
for i, op in enumerate(ops):
    xml = converter.create_workingstep_xml(op, mapping, i)
    print(xml)
```

## Mapping Format

CAM to ISO 14649 mapping config (JSON):

```json
{
  "CAM.field.path": "MachiningWorkingstep.its_operation.MachiningOperation.field",
  "Tool Information.Diameter": "...MachiningTool.effective_cutting_diameter"
}
```

## Supported CAM Systems

| System | Type String | JSON Structure |
|--------|-------------|----------------|
| NX CAM | `nx` | `{key: {}, values: [...ops]}` |
| PowerMill | `powermill` | Single op or `{operation: {...}}` |

## Testing

```bash
uv run pytest
```

## Project Structure

```
digital-thread-project-manager/
├── src/
│   ├── __init__.py
│   ├── agent.py              # Main agent class
│   ├── models/
│   │   └── dt_asset.py       # ISO 14649 schema dataclasses
│   ├── parsers/
│   │   ├── cam_nx.py         # NX CAM parser
│   │   ├── cam_powermill.py  # PowerMill parser
│   │   ├── nc_parser.py      # NC file splitter
│   │   └── xml_parser.py     # XML utilities
│   ├── converters/
│   │   └── cam_converter.py  # CAM to XML converter
│   └── services/
│       └── workplan_service.py
├── tests/
├── pyproject.toml
└── README.md
```

## Related Standards

- **ISO 14649**: Industrial automation - Physical device control
- **ISO 13399**: Cutting tool data representation
- **dt_asset**: Digital Thread Asset schema (internal)
