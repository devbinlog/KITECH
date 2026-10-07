# CAM Runner Samples

## 📋 Overview

Stock models and CAM analysis examples for manufacturing simulation.

## 📁 Directory Structure

```
cam-runner/
├── stock_models/      # Stock Material Models
│   ├── aluminum_6061_100x100.json
│   ├── steel_45c_50x50.json
│   └── titanium_64_custom.json
├── results/           # CAM Analysis Results
│   ├── block_001_analysis.csv
│   └── analysis_report.json
└── README.md (this file)
```

## 🎯 Sample Types

### Stock Models
- **Purpose**: Define initial material state for Dexel/Octree models
- **Format**: JSON
- **Contains**:
  - Material properties (density, hardness, machinability)
  - Dimensions and coordinate system
  - Height field or hierarchical spatial structure

### Materials Available

| Material | Density | Hardness | Machinability | File |
|----------|---------|----------|---------------|------|
| Aluminum 6061 | 2.70 | 95 | 8.0 (baseline) | aluminum_6061_100x100.json |
| Steel 45C | 7.85 | 200 | 4.0 | steel_45c_50x50.json |
| Titanium 64 | 4.43 | 320 | 2.0 | titanium_64_custom.json |

## 🚀 Usage

### CAM Analysis
```bash
# Analyze single G-code with stock model
python advanced_analysis.py \
  --gcode samples/gcode-parser/simple/basic_milling.nc \
  --stock samples/cam-runner/stock_models/aluminum_6061_100x100.json \
  --output analysis_result.json
```

### Python API
```python
from agents.cam_runner.src import CAMRunnerAgent

agent = CAMRunnerAgent()
result = agent.analyze_gcode_paths({
    'gcode_file': 'samples/gcode-parser/simple/basic_milling.nc',
    'stock_model': 'samples/cam-runner/stock_models/aluminum_6061_100x100.json'
})
```

## 📊 Stock Model Format

```json
{
  "material_name": "Aluminum 6061",
  "material_properties": {
    "density": 2.70,
    "hardness": 95,
    "machinability": 8.0
  },
  "dimensions": {
    "length_mm": 100,
    "width_mm": 100,
    "height_mm": 50
  },
  "coordinate_system": {
    "origin": [0, 0, 0],
    "x_direction": [1, 0, 0],
    "y_direction": [0, 1, 0],
    "z_direction": [0, 0, 1]
  },
  "representation": "dexel",
  "dexel_grid": {
    "resolution_x": 10,
    "resolution_y": 10,
    "height_field": [[...]]
  }
}
```

## 📈 Analysis Results

### Block-Level Metrics
- **Ap** (Radial Depth of Cut): mm
- **Ae** (Axial Depth of Cut): mm
- **Volume Removed**: mm³
- **Feed Rate**: mm/min (adjusted for material)
- **Cutting Time**: seconds
- **Tool Index**: which tool used

### Expected Output
```csv
block_number,line_number,operation,ap_mm,ae_mm,volume_mm3,feed_rate_mm_min,cutting_time_sec,material_adjusted_feed
1,10,G00_Rapid,0,0,0,0,0,0
2,20,G01_Feed,2.5,1.0,2.5,250,10,187.5
3,30,G02_CircularCW,3.0,2.0,6.0,300,20,200
```

## 🔄 Material-Aware Calculations

Feed rate adjustment based on material machinability:

```
Adjusted Feed Rate = Base Rate × (Material Machinability / 8.0)

Example:
- Base Rate: 300 mm/min
- Aluminum 6061 (machinability 8.0): 300 × (8.0/8.0) = 300 mm/min
- Steel 45C (machinability 4.0): 300 × (4.0/8.0) = 150 mm/min
- Titanium 64 (machinability 2.0): 300 × (2.0/8.0) = 75 mm/min
```

## 📝 Creating Custom Stock Models

```python
import json

custom_model = {
    "material_name": "Custom Material",
    "material_properties": {
        "density": 3.5,
        "hardness": 250,
        "machinability": 3.5
    },
    "dimensions": {
        "length_mm": 150,
        "width_mm": 100,
        "height_mm": 75
    },
    "coordinate_system": {
        "origin": [0, 0, 0],
        "x_direction": [1, 0, 0],
        "y_direction": [0, 1, 0],
        "z_direction": [0, 0, 1]
    },
    "representation": "octree",
    "octree": {...}
}

with open('custom_material.json', 'w') as f:
    json.dump(custom_model, f, indent=2)
```

## ✅ Sample Validation

- [ ] Material properties within realistic ranges
- [ ] Dimensions match physical constraints
- [ ] Coordinate system is orthogonal (unit vectors)
- [ ] JSON valid and parseable
- [ ] Height field/octree properly structured

## 🎯 Use Cases

1. **Basic Testing**: Use aluminum_6061 samples for quick validation
2. **Performance Comparison**: Compare results across materials
3. **Production Planning**: Estimate cutting times for jobs
4. **Material Selection**: Evaluate machinability impact
5. **Optimization**: Find best feed rates for different materials

## 📚 Related Documentation

- See [CAM Runner Documentation](../../agents/cam-runner/README.md)
- Material property references in [samples/config/materials.json](../config/materials.json)
