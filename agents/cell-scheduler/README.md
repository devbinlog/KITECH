# Cell Scheduler Agent

OR-Tools 기반 생산 스케줄링 최적화 에이전트

## Quick Start

```bash
cd agents/cell-scheduler
uv sync
uv run pytest tests/
```

## Usage

```python
from src.cell_scheduler_agent import CellSchedulerAgent

agent = CellSchedulerAgent()

# 파일 경로로 입력
result = agent.process("samples/cell-scheduler/input", solver_type="OR_TOOLS")

# 또는 딕셔너리로 입력
result = agent.process({
    "work_orders": [...],
    "machines": [...],
    "request": {"scheduling_request": {...}}
}, solver_type="GA")

print(result["scheduled_tasks"])
print(result["statistics"]["makespan_hours"])
```

## Solvers

| Solver | Algorithm | Best For |
|--------|-----------|----------|
| OR_TOOLS | Constraint Programming | 최적해 (소규모) |
| GA | Genetic Algorithm | 대규모 탐색 |
| SA | Simulated Annealing | 지역 최적해 |
| TABU | Tabu Search | 순환 회피 |
| ALNS | Adaptive LNS | 복잡한 제약 |

## Input Format

```json
{
  "request": {
    "scheduling_request": {
      "scheduling_horizon": {
        "start": "2026-02-02T08:00:00",
        "end": "2026-02-09T20:00:00"
      }
    }
  },
  "work_orders": [{
    "wo_id": "WO-001",
    "jobs": [{
      "job_id": "JOB-001",
      "operations": [{
        "op_id": "OP-001",
        "nc_code": {"cycle_time_sec": 300}
      }]
    }]
  }],
  "machines": [{
    "machine_id": "CNC-001",
    "machine_type": "CNC"
  }]
}
```

## Output

```json
{
  "status": "success",
  "scheduled_tasks": [
    {"wo_id": "WO-001", "machine_id": "CNC-001", "start_time": 0, "end_time": 300}
  ],
  "statistics": {
    "makespan_hours": 0.08,
    "avg_utilization": 0.85
  }
}
```

## REST API

```bash
# 서버 시작
uvicorn src.app.main:app --port 8002

# 스케줄링 요청
curl -X POST http://localhost:8002/api/solve \
  -H "Content-Type: application/json" \
  -d '{"work_orders": [...], "machines": [...]}'
```

## Testing

```bash
uv run pytest tests/ -v
uv run pytest tests/ --cov=src
```
