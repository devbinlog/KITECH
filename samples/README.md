# Manufacturing Intelligence System - Samples

Comprehensive sample data for each agent in the manufacturing intelligence pipeline.

## 📋 Overview

This directory contains sample inputs, outputs, and test cases for all system agents:
1. **gcode-parser**: CNC program validation and analysis
2. **cam-runner**: Stock model simulation with tool path analysis
3. **cell-scheduler**: Manufacturing cell scheduling optimization
4. **cell-schedule-visualizer**: Schedule visualization and metrics

## 🔄 Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  NC Code (G-code)                                          │
│  ↓                                                          │
│  [gcode-parser] → Validate → Block sequences              │
│  ↓                                                          │
│  [cam-runner] → Stock models → Ap/Ae metrics               │
│  ↓                                                          │
│  [cell-scheduler] → OR-Tools CP-SAT → Optimal assignment   │
│  ↓                                                          │
│  [cell-schedule-visualizer] → HTML dashboard → KPIs        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Directory Structure

```
samples/
├── README.md (this file)
│
├── gcode-parser/
│   ├── ISO10791/           (100 ISO standard test programs)
│   │   ├── ISO10791_001.nc
│   │   ├── ISO10791_002.nc
│   │   └── ... (to ISO10791_100.nc)
│   ├── simple/             (Basic examples)
│   │   ├── simple_linear.nc
│   │   └── simple_arc.nc
│   └── README.md           (Format details, validation)
│
├── cam-runner/
│   ├── stock_models/       (JSON stock definitions)
│   │   ├── aluminum_6061.json
│   │   ├── steel_45c.json
│   │   └── titanium_64.json
│   └── README.md           (Format, calculation examples)
│
├── cell-scheduler/
│   ├── input/              (8 JSON configuration files)
│   │   ├── 01_work_orders.json
│   │   ├── 02_machines.json
│   │   ├── 03_machine_capabilities.json
│   │   ├── 04_operation_resources.json
│   │   ├── 05_nc_code_registry.json
│   │   ├── 06_setup_times.json
│   │   ├── 07_constraints.json
│   │   └── 08_scheduling_request.json
│   ├── output/             (Generated results)
│   │   └── schedule_result.json
│   └── README.md           (Schema docs, scenarios)
│
└── cell-schedule-visualizer/
    ├── sample_schedule.json (Example output)
    ├── sample_dashboard.html (Example visualization)
    ├── expected_output/     (Reference metrics)
    │   ├── metrics.json
    │   └── gantt_data.json
    └── README.md            (Chart interpretation, customization)
```

## 🚀 Quick Start Examples

### 1. Parse G-code
```bash
# Validate ISO10791 standard program
python -c "
from agents.gcode_parser.src import GcodeParserAgent
agent = GcodeParserAgent()
result = agent.process('samples/gcode-parser/ISO10791/ISO10791_001.nc')
print(result)
"
```

**Result**: ✅ Block parsing, tool moves, rapid traversals

### 2. Run CAM Analysis
```bash
# Simulate with aluminum stock model
python -c "
from agents.cam_runner.src import CamRunnerAgent
agent = CamRunnerAgent()
result = agent.process(
  gcode='samples/gcode-parser/ISO10791/ISO10791_001.nc',
  stock='samples/cam-runner/stock_models/aluminum_6061.json'
)
print(f'Removed volume: {result[\"total_volume_removed\"]}')
"
```

**Result**: ✅ Block-level metrics, Ap/Ae values, feed rates

### 3. Schedule Operations
```bash
# Optimal cell scheduling
python schedule_manufacturing_cell.py \
  --input-dir samples/cell-scheduler/input \
  --visualize
```

**Output**: `schedule_result.json` + `schedule_dashboard.html`

**Result**: ✅ 8 tasks optimized, ~0.03 seconds solve time

### 4. View Schedule Dashboard
```bash
# Browser opens automatically
# Charts: Gantt timeline, machine utilization, lateness
```
```

### 일괄 분석

```python
import os
from gcode_agent import GcodeParserAgent

agent = GcodeParserAgent()
samples_dir = 'samples'

for filename in sorted(os.listdir(samples_dir)):
    if filename.endswith('.nc'):
        filepath = os.path.join(samples_dir, filename)
        print(f"\n분석 중: {filename}")
        agent.parse_gcode_file(filepath)
        report = agent.calculate_machining_time(agent.parse_gcode_text(open(filepath).read()))
        print(f"  총 시간: {report['total_time_minutes']:.2f}분")
```

---

## 📊 샘플 분류

### 기법별 분류
- **포켓 가공**: 3, 4, 28, 42, 49, 70, 75, 78, 88, 94, 95
- **홀 가공**: 8, 11, 29, 34, 72
- **프로파일 절삭**: 1, 2, 15, 16, 17, 25, 26, 32, 50, 51, 52, 53
- **패턴 절삭**: 10, 18, 27, 31, 39, 40, 43, 45, 46, 48, 54, 55, 64, 65
- **슬롯 가공**: 5, 6, 24
- **곡선 가공**: 22, 23, 39, 40, 47, 54, 62, 63, 73, 74, 83, 84, 86, 87, 93

### 복잡도별 분류
- **단순 (1-3개 명령)**: 15, 35, 36, 45, 76, 77
- **중간 (10-50개 명령)**: 1, 2, 9, 12, 13, 14, 22, 25, 26, 51, 52
- **복잡 (50개 이상 명령)**: 11, 28, 43, 72, 81, 82, 83, 84

### 시간별 분류
- **빠른 작업 (< 1분)**: 1, 2, 9, 15, 16, 17, 25, 35, 36, 45, 76, 77
- **중간 작업 (1-10분)**: 3, 4, 5, 6, 7, 12, 13, 14, 20, 21, 26
- **긴 작업 (10분 이상)**: 11, 28, 43, 72, 81, 82, 97

---

## 💡 학습 경로

초보자부터 고급 사용자까지의 추천 학습 순서:

1. **기초 (샘플 1-10)**: 기본 도형과 프로파일
2. **배열 (샘플 11-20)**: 반복 패턴과 배열
3. **기법 (샘플 21-40)**: 다양한 절삭 기법
4. **패턴 (샘플 41-70)**: 복잡한 패턴과 곡선
5. **고급 (샘플 71-100)**: 극단 조건과 종합 테스트

---

## 📝 주요 특징

- ✅ 100개의 다양한 G코드 패턴
- ✅ 3축 밀링 기반 설계
- ✅ 초보자부터 고급 사용자까지 커버
- ✅ 각 샘플은 독립적으로 실행 가능
- ✅ 실제 CNC 가공에 기반한 설계

---

**생성 날짜**: 2026년 1월 16일
