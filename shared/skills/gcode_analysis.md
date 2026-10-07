# G-Code Analysis Skill

## Description
Parses G-code files/text, extracts machining blocks, and calculates engagement parameters (Ap, Ae) for each motion command. Handles multiple encodings, modal G-codes, and position tracking.

## Input
- `gcode_source`: string (either raw G-code text or file path)
- `coordinate_system`: "absolute" | "incremental" (default: "absolute")
- `encoding_priority`: list of encoding attempts (default: ["utf-8", "cp1252"])

## Output
```json
{
  "status": "success" | "warning" | "error",
  "data": {
    "blocks": [
      {
        "block_number": integer,
        "command": string (e.g., "G01", "G00", "G02"),
        "start_position": [x, y, z],
        "end_position": [x, y, z],
        "Ap": float (axial depth of cut in Z),
        "Ae": float (radial engagement in XY),
        "rapid_distance": float,
        "cutting_distance": float,
        "feed_rate": float,
        "spindle_speed": float,
        "is_cutting": boolean
      }
    ],
    "total_distance": float,
    "total_cutting_distance": float,
    "total_rapid_distance": float,
    "max_Ap": float,
    "max_Ae": float
  },
  "errors": [string],
  "warnings": [string]
}
```

## Implementation Notes

### Supported Commands
- **G-codes**: G00 (rapid), G01 (linear), G02/G03 (arc), G04 (dwell)
- **M-codes**: M03 (spindle on), M04 (spindle reverse), M05 (spindle off)

### Core Algorithm
1. **File loading**: Attempt encodings in priority order; fall back to error handling
2. **Block extraction**: Split by newline; parse each line for G-code commands
3. **Modal state**: Track active G-codes, feed rate, spindle speed (preserve across blocks)
4. **Position tracking**: Maintain running (x, y, z) coordinates
5. **Engagement calculation**:
   - For G00/G01: Linear motion → Ap = |Z_end - Z_start|, Ae = distance in XY
   - For G02/G03: Arc motion → compute arc radius, sweep angle → radial engagement
6. **Aggregation**: Sum distances, track min/max/avg engagement

### Edge Cases
- **Coordinate-only lines**: Lines with only coordinates (no G-code) → inherit modal G-code
- **No cutting commands**: Programs with only rapid moves → set is_cutting=false for all
- **Incomplete data**: Missing coordinates → skip block or use last known position
- **Circular interpolation**: G02/G03 → extract radius/center from I, J, K offsets
- **Multiple encoding attempts**: Try UTF-8 first; fall back to cp1252, latin-1, etc.

### Performance Considerations
- **Streaming parse**: Process line-by-line (avoid loading entire file to memory)
- **Regex compilation**: Pre-compile patterns for G-code extraction (outside loop)
- **Modal state caching**: Keep active G-code/feed in memory (no dict lookup per block)

### Error Handling
- **File not found**: Return error status with descriptive message
- **Encoding failure**: Try alternative encodings; log warnings for each attempt
- **Parse errors**: Log malformed lines; continue with next block
- **Zero distance**: Handle G04 dwell (no motion) → record with zero distance
