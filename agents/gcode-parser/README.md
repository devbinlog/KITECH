# G-code Parser Agent

G-code 텍스트를 파싱하여 블록별 이동, 가공 정보를 추출하는 에이전트

## Quick Start

```bash
cd agents/gcode-parser
uv sync
uv run pytest tests/
```

## Usage

```python
from src.gcode_parser_agent import GcodeParserAgent

agent = GcodeParserAgent()
result = agent.process("G00 X10 Y20\nG01 Z-5 F100\nM30")

print(result["data"]["blocks"])  # 파싱된 블록 목록
print(result["data"]["summary"])  # 요약 정보
```

## Input/Output

### Input
- G-code 문자열 또는 파일 경로
- 지원 인코딩: UTF-8, CP1252, Latin-1

### Output
```json
{
  "status": "success",
  "data": {
    "blocks": [
      {"command": "G00", "X": 10, "Y": 20, "is_cutting": false},
      {"command": "G01", "Z": -5, "F": 100, "is_cutting": true}
    ],
    "summary": {
      "total_blocks": 2,
      "cutting_blocks": 1,
      "tool_changes": 0
    }
  }
}
```

## Supported G-codes

| Code | Description |
|------|-------------|
| G00 | Rapid positioning |
| G01 | Linear interpolation |
| G02 | Circular CW |
| G03 | Circular CCW |
| G28 | Return to home |
| M03/M04 | Spindle on |
| M05 | Spindle off |
| M06 | Tool change |
| M30 | Program end |

## Testing

```bash
uv run pytest tests/ -v
uv run pytest tests/ --cov=src
```

## API

### `GcodeParserAgent.process(input_data, **kwargs)`
- `input_data`: G-code string or file path
- Returns: Dict with status and parsed data
