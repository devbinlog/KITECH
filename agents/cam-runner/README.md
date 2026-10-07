# CAM Runner Agent

G-code 경로를 분석하여 Ap(절삭깊이), Ae(절삭폭), 사이클 타임을 계산하는 에이전트

## Quick Start

```bash
cd agents/cam-runner
uv sync
uv run pytest tests/
```

## Usage

```python
from src.cam_runner_agent import CamRunnerAgent

agent = CamRunnerAgent()

# G-code 파서 결과를 입력으로 사용
gcode_data = {
    "blocks": [
        {"command": "G00", "X": 0, "Y": 0, "Z": 5},
        {"command": "G01", "X": 10, "Y": 10, "Z": -5, "F": 100}
    ]
}

result = agent.process(gcode_data)
print(result["data"]["cycle_time"])  # 사이클 타임
print(result["data"]["paths"])       # 경로별 Ap/Ae
```

## Input/Output

### Input
- G-code 파서 출력 (blocks 배열)
- 또는 직접 경로 데이터

### Output
```json
{
  "status": "success",
  "data": {
    "cycle_time": {
      "total_cycle_time_sec": 249.3,
      "cutting_time_sec": 200.0,
      "rapid_time_sec": 49.3
    },
    "summary": {
      "total_paths": 15,
      "cutting_segments": 12,
      "avg_Ap": 3.5,
      "avg_Ae": 2.1
    },
    "paths": [
      {"Ap": 5.0, "Ae": 3.0, "is_cutting": true}
    ]
  }
}
```

## Key Metrics

| Metric | Description |
|--------|-------------|
| Ap | Axial depth of cut (Z 방향) |
| Ae | Radial width of cut (XY 방향) |
| Cycle Time | 총 가공 시간 예측 |

## Testing

```bash
uv run pytest tests/ -v
uv run pytest tests/ --cov=src
```
