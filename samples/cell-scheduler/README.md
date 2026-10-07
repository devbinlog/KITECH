# Cell Scheduler Samples - ISO10791 통합 예제

## 📋 Overview

ISO10791 표준 G코드와 연계된 제조업 스케줄링 입력/출력 예제 (OR-Tools CP-SAT 기반)

## 📁 Directory Structure

```
cell-scheduler/
├── input/              # 스케줄링 입력 (8개 JSON 파일)
│   ├── 00_scheduling_request.json      # 스케줄링 요청 정보
│   ├── 01_work_orders.json             # ISO10791 연계 작업 주문
│   ├── 02_machines.json                # 4가지 장비 유형 정의
│   ├── 03_machine_type_params.json    # 장비별 파라미터
│   ├── 04_amrs.json                    # AGV/로봇 설정
│   ├── 05_cell_layout.json             # 셀 레이아웃
│   ├── 06_constraints.json             # 제약조건
│   └── 07_current_state.json           # 초기 상태
├── output/             # 스케줄링 결과
│   └── schedule_result.json
└── README.md (this file)
```

## 🎯 Equipment Configuration (4가지 장비 유형)

### 1. 3축 밀링 양산장비 (VMC_3AXIS_MASS)
- **Machines**: MCH-001, MCH-002
- **제조사**: DOOSAN DNM-4500
- **특징**: 고속 양산, 자동 공구 교체
- **활용**: ISO10791_001 초기 선삭

### 2. 3축 밀링 팔레트 장비 (VMC_3AXIS_PALLET)
- **Machines**: MCH-003, MCH-004
- **제조사**: DMG MORI CMX-600V
- **특징**: 팔레트 자동 교체, 다중 파트 동시 가공
- **활용**: ISO10791_010, ISO10791_050 정삭

### 3. 4축 밀링 팔레트 장비 (VMC_4AXIS_PALLET)
- **Machines**: MCH-005, MCH-006
- **제조사**: DMG MORI CMX-70U
- **특징**: 회전축(A축) 가공, 복잡한 형상 처리
- **활용**: ISO10791_010 복잡 부품 가공

### 4. 하드 터닝 장비 (HARD_TURNING)
- **Machines**: MCH-007, MCH-008
- **제조사**: MAZAK QTN-200MY
- **특징**: 경화강 선삭 전문, 고정밀 드로잉
- **활용**: ISO10791_050 선삭 작업

## 📊 ISO10791 연계 Work Orders

### Sample 1: ISO10791_001 (기본 도형)
```json
{
  "wo_id": "WO-2025-0117-001",
  "product_id": "ISO-001",
  "product_name": "ISO10791_001 샘플 부품",
  "order_quantity": 10,
  "priority": 1,
  "gcode_file": "samples/gcode-parser/ISO10791/ISO10791_001.nc",
  "operations": [{
    "op_id": "OP10",
    "op_name": "황삭 - 3축 밀링",
    "required_machine_type": "VMC_3AXIS_MASS",
    "cycle_time_sec": 180
  }]
}
```

### Sample 2: ISO10791_010 (배열 패턴)
      "file_path": "samples/gcode-parser/simple/basic_drilling.nc",
      "cycle_time_sec": 300,
      "cycle_time_confidence": 0.95,
      "tool_list": ["T1", "T2"],
      "tool_change_count": 1,
      "compatible_machines": ["MCH-001", "MCH-002"]
    }
  ]
}
```

### 5. Cell Layout (`05_cell_layout.json`)
**Purpose**: Physical arrangement and routing

```json
{
  "cell_layout": {
    "cell_id": "CELL-001",
    "machine_positions": {
      "MCH-001": [0, 0],
      "MCH-002": [10, 0]
    },
    "transport_matrix": [...]
  }
}
```

### 6. Constraints (`06_constraints.json`)
**Purpose**: Scheduling rules and limitations

```json
{
  "constraints": {
    "max_concurrent_jobs": 8,
    "setup_time_sec": 300,
    "break_schedule": [
      {
        "start": "12:00",
        "end": "13:00",
        "daily": true
      }
    ]
  }
}
```

### 7. AMR Specifications (`07_amr_specifications.json`)
**Purpose**: Automated Mobile Robot configuration

```json
{
  "amr_specs": {
    "available_amrs": 2,
    "capacity_units": 10,
    "speed_m_per_sec": 1.5,
    "battery_life_hours": 8
  }
}
```

### 8. Scheduling Request (`08_scheduling_request.json`)
**Purpose**: Optimization parameters

```json
{
  "scheduling_request": {
    "scheduling_horizon": {
      "start": "2025-01-17T08:00:00",
      "end": "2025-01-22T20:00:00"
    },
    "options": {
      "solver_time_limit_sec": 60,
      "optimization_objective": "minimize_makespan",
      "include_setup_time": true
    }
  }
}
```

## 🚀 Usage

### Command Line
```bash
# Generate schedule
python schedule_manufacturing_cell.py \
  --input-dir samples/cell-scheduler/input \
  --output schedule_result.json \
  --visualize

# Output: schedule_result.json + schedule_dashboard.html
```

### Python API
```python
from agents.cell_scheduler.src import CellSchedulerAgent

agent = CellSchedulerAgent()
result = agent.process("samples/cell-scheduler/input")
```

## 📊 Output Format

See [output/README.md](output/README.md) for schedule result structure.

## 🔍 Data Validation

### Input Checklist
- [ ] All 8 JSON files present and valid
- [ ] Work order IDs unique
- [ ] Machine IDs referenced correctly
- [ ] Dates in ISO 8601 format
- [ ] Priority values: high | medium | low
- [ ] Machine types match across files
- [ ] NC codes reference valid program IDs

### Constraint Validation
```bash
# Check for conflicts
python scripts/validate_scheduling_input.py samples/cell-scheduler/input
```

## 🎯 Common Scenarios

### Scenario 1: Simple 3 WO, 8 Machine Cell
- **Input**: `input/`
- **Machines**: 3 types (MILL, LATHE, DRILL)
- **Horizon**: 5 days
- **Result**: 8-15 scheduled tasks

### Scenario 2: High Priority Orders
- Modify `priority` in work_orders.json
- Run scheduler (high priority gets penalties)
- Compare makespan vs lateness tradeoffs

### Scenario 3: Material-Aware Scheduling
- Include material data in work orders
- Link to CAM runner for accurate cycle times
- Feed results to scheduler

## 📈 Optimization Objectives

| Objective | Focus | Use Case |
|-----------|-------|----------|
| minimize_makespan | Total time | One-time batch job |
| minimize_lateness | On-time delivery | Customer deadline |
| maximize_utilization | Machine efficiency | Utilization optimization |
| balanced | Mixed weighted | General production |

## 🔗 Integration

### With CAM Runner
```
1. Parse G-code: gcode-parser
2. Analyze cutting: cam-runner (gets cycle time)
3. Schedule jobs: cell-scheduler (uses cycle time)
4. Visualize: cell-schedule-visualizer
```

### With Orchestrator
```python
# orchestrator_main.py
scheduler_result = scheduler.solve(cam_analysis_result)
visualization = visualizer.process(scheduler_result)
```

## 📚 Reference

- [Scheduler Implementation Guide](../../SCHEDULER_IMPLEMENTATION_COMPLETE.md)
- [Visualizer Guide](../../VISUALIZER_AGENT_COMPLETE.md)
- OR-Tools: https://developers.google.com/optimization
