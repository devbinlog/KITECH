# G-Code Parser Samples

## 📋 Overview

Manufacturing CNC machine G-code samples for testing and analysis.

## 📁 Directory Structure

```
gcode-parser/
├── ISO10791/          # ISO 10791 Standard Test Cases
│   ├── ISO10791_001.nc  to ISO10791_100.nc
│   └── README.md
├── simple/            # Simple Test Cases
│   ├── basic_drilling.nc
│   ├── basic_milling.nc
│   └── README.md
└── README.md (this file)
```

## 🎯 Sample Types

### ISO10791 Standard Test Suite
- **Purpose**: Standardized CNC machine testing
- **Source**: ISO/TC 184/SC 1 (Industrial Automation)
- **Files**: 100 test programs covering:
  - Linear interpolation
  - Circular interpolation
  - Complex tool paths
  - Speed/feed variations
  - Setup changes
- **Use Case**: Comprehensive validation of G-code parser

### Simple Examples
- **Purpose**: Basic functionality testing
- **Files**:
  - `basic_drilling.nc` - Simple drilling pattern
  - `basic_milling.nc` - Basic milling operations
- **Use Case**: Quick validation, learning

## 🚀 Usage

### With gcode-parser Agent
```python
from agents.gcode_parser.src import GcodeParserAgent

agent = GcodeParserAgent()
result = agent.process("samples/gcode-parser/ISO10791/ISO10791_001.nc")
```

### With CLI
```bash
# Parse single file
python advanced_analysis.py samples/gcode-parser/simple/basic_drilling.nc

# Batch analysis
python batch_analysis.py samples/gcode-parser/ISO10791/
```

## 📊 Expected Output

```json
{
  "status": "success",
  "gcode_file": "basic_drilling.nc",
  "blocks": [
    {
      "line_number": 1,
      "block_text": "G90 G54 G00 X0 Y0 Z10",
      "modal_groups": [...],
      "movements": {...}
    }
  ],
  "statistics": {
    "total_blocks": 50,
    "tool_changes": 2,
    "total_path_length": 1250.5
  }
}
```

## 🔍 File Format Details

### G-Code Structure
```
% (program start)
O1234 (program number/name)
(comment)
G90 (absolute positioning)
G00 X10 Y20 Z5 (rapid move)
G01 Z-2 F100 (feed move)
M30 (program end)
% (program end)
```

### Supported Commands
- **Rapid Move**: G00
- **Linear Feed**: G01
- **Circular Interpolation**: G02 (CW), G03 (CCW)
- **Tool Change**: M06
- **Spindle Control**: M03, M04, M05
- **Coolant**: M07, M08, M09

## 📈 Sample Complexity

| Sample | Lines | Blocks | Tools | Moves | Complexity |
|--------|-------|--------|-------|-------|------------|
| basic_drilling.nc | 20 | 15 | 1 | Linear | Low |
| basic_milling.nc | 40 | 30 | 2 | Mixed | Medium |
| ISO10791_001 | 100+ | 80+ | 3+ | Complex | High |

## ✅ Validation Checklist

- [ ] File can be parsed without errors
- [ ] Block count matches expected
- [ ] Tool changes detected correctly
- [ ] Path length calculated
- [ ] Movements extracted
- [ ] Coordinates within machine limits

## 📝 Notes

- ISO10791 files follow strict standardization for machine testing
- Simple examples are ideal for troubleshooting
- Add your own samples in respective subdirectories
- Keep raw .nc files unchanged (read-only recommended)

## 🔗 References

- [ISO 10791 Standard](https://www.iso.org/standard/59765.html)
- [G-Code Reference](https://en.wikipedia.org/wiki/G-code)
- [CNC Programming Guide](https://www.cnccookbook.com/g-code/)
