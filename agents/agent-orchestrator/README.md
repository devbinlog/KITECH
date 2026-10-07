# Orchestrator

LangGraph 기반 워크플로우 오케스트레이션

## Quick Start

```bash
cd orchestrator
uv sync
uv run pytest tests/
```

## Usage

```python
from src.langgraph_orchestrator import LangGraphOrchestrator

orch = LangGraphOrchestrator()

# G-code로 전체 제조 워크플로우 실행
with open("sample.nc") as f:
    gcode = f.read()

result = orch.run_workflow(
    gcode_input=gcode,
    workflow_name="full-manufacturing"
)

print(result["status"])
print(result["stages"]["cell_scheduling"]["scheduled_tasks"])
```

## Workflows

### minimal-analysis
```
G-code → gcode_parsing → cam_analysis
```
- 사이클 타임 빠른 추정

### full-manufacturing
```
G-code → gcode_parsing → cam_analysis → cell_scheduling → schedule_visualization
```
- 완전한 생산 계획 수립

## Custom Workflow

`samples/workflows/` 에 JSON 파일 추가:

```json
{
  "name": "my-workflow",
  "description": "Custom workflow",
  "stages": [
    {"name": "gcode_parsing", "agent": "gcode-parser"},
    {"name": "cam_analysis", "agent": "cam-runner", "depends_on": ["gcode_parsing"]}
  ]
}
```

## Converters

| Converter | From | To |
|-----------|------|-----|
| cam_to_scheduler | CAM 결과 | Scheduler 입력 |

## Adding Agents

```python
# langgraph_orchestrator.py
self.agents = {
    "gcode-parser": GcodeParserAgent(),
    "cam-runner": CamRunnerAgent(),
    "my-agent": MyAgent(),  # 추가
}
```

## Testing

```bash
uv run pytest tests/ -v
uv run pytest tests/ --cov=src
```
