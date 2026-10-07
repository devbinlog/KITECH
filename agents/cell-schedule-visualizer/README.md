# Cell Schedule Visualizer Agent

스케줄링 결과를 간트 차트 및 HTML 리포트로 시각화하는 에이전트

## Quick Start

```bash
cd agents/cell-schedule-visualizer
uv sync
uv run pytest tests/
```

## Usage

```python
from src.schedule_visualizer_agent import ScheduleVisualizerAgent

agent = ScheduleVisualizerAgent()

# 스케줄러 결과를 입력으로 사용
schedule_result = {
    "scheduled_tasks": [...],
    "statistics": {"makespan_hours": 8.5}
}

result = agent.process(schedule_result)
print(result["gantt_data"])  # 간트 차트 데이터
```

## Input/Output

### Input
- Cell Scheduler 출력 결과
- `scheduled_tasks`, `statistics` 포함

### Output
```json
{
  "status": "success",
  "gantt_data": {
    "tasks": [
      {"resource": "CNC-001", "start": "2026-02-02T08:00", "end": "2026-02-02T12:00"}
    ],
    "resources": ["CNC-001", "CNC-002"]
  },
  "html_report": "output/schedule_report.html"
}
```

## Visualization Types

| Type | Description |
|------|-------------|
| Gantt Chart | 장비별 작업 타임라인 |
| Utilization | 장비 가동률 차트 |
| Summary | 통계 요약 테이블 |

## Testing

```bash
uv run pytest tests/ -v
uv run pytest tests/ --cov=src
```
