# CAM Computation Skill

## Description
Analyzes cutting tool paths, calculates tool-specific engagement metrics, handles multiple tool geometries (cylindrical, ball, bull end mills), and optionally integrates advanced stock material models.

## Input
```json
{
  "blocks": [
    {
      "block_number": integer,
      "command": string,
      "start_position": [x, y, z],
      "end_position": [x, y, z],
      "Ap": float,
      "Ae": float,
      "feed_rate": float,
      "spindle_speed": float
    }
  ],
  "tool": {
    "type": "CylCutter" | "BallCutter" | "BullCutter",
    "diameter": float (mm),
    "radius": float (mm, for ball/bull),
    "corner_radius": float (mm, for bull only)
  },
  "material": {
    "name": string,
    "hardness": float,
    "feed_per_tooth": float
  },
  "use_advanced_stock": boolean (default: false)
}
```

## Output
```json
{
  "status": "success" | "warning" | "error",
  "data": {
    "tool_path_analysis": {
      "min_Ap": float,
      "max_Ap": float,
      "avg_Ap": float,
      "min_Ae": float,
      "max_Ae": float,
      "avg_Ae": float
    },
    "tool_engagement": {
      "within_limits": boolean,
      "limiting_factor": string,
      "safety_margin": float (0.0-1.0)
    },
    "stock_removal": {
      "estimated_volume_mm3": float,
      "tool_wear_index": float
    },
    "cutting_time_seconds": float,
    "warnings": [string]
  },
  "errors": [string]
}
```

## Implementation Notes

### Tool Geometry Constraints
- **CylCutter**: 
  - Radial engagement limited by tool diameter
  - Ap limited by cutting edge height
  - Typical limit: Ae ≤ diameter, Ap ≤ height
  
- **BallCutter**:
  - Radial engagement limited by tool radius
  - Ap/Ae both constrained by radius
  - Max engagement at center (ball tip)
  
- **BullCutter**:
  - Combines cylindrical flute + corner radius
  - Corner engagement depends on corner_radius
  - Transitions between cylindrical and corner cutting

### Engagement Calculation
1. **For G00/G01 (linear motion)**:
   - Ap = |Z_end - Z_start| (axial depth)
   - Ae = sqrt((X_end-X_start)² + (Y_end-Y_start)²) (radial distance)
   - Apply tool geometry limits

2. **For G02/G03 (arc motion)**:
   - Extract arc radius from I, J, K or R parameter
   - Compute sweep angle (start→end)
   - Calculate engagement based on arc path
   - Handle full circles (360°)

### Feed Validation
- Calculate theoretical engagement per tooth: `engagement = feed_rate / (spindle_speed * num_teeth)`
- Validate against material feed_per_tooth
- Log warning if engagement exceeds material capability
- Assume default num_teeth if not specified

### Advanced Stock Mode (Optional)
- If `use_advanced_stock=true` and OpenCAMLib available:
  - Use dexel/octree stock model
  - Calculate actual material removal volume
  - Estimate tool wear progression
  - Apply stock-aware engagement corrections
- If OpenCAMLib unavailable: Log warning, use simplified calculations

### Stock Removal Calculation
```
volume_mm3 = sum(Ap[i] * Ae[i] * distance[i] for each block)
tool_wear_index = (volume_mm3 / tool_diameter) / reference_wear_volume
```

### Error Handling
- **Tool diameter ≤ 0**: Return error
- **Zero feed rate**: Log warning; use default feed rate
- **No blocks**: Return empty analysis with warning
- **Feed exceeds limit**: Log warning; mark within_limits=false
- **OpenCAMLib error**: Fall back to simplified mode; log warning
