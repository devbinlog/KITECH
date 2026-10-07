# Agent Architecture - agents-workspace

## 🤖 에이전트 목록

| 에이전트 | 역할 | 포트 | 상태 |
|----------|------|------|------|
| **gcode-parser** | G-code 파싱 | - | ✅ |
| **cam-runner** | CAM 분석 (Ap/Ae, Cycle Time) | - | ✅ |
| **step-pmi-reader** | STEP PMI 추출 | - | ✅ |
| **cell-scheduler** | 스케줄링 (OR-Tools, GA, SA, TABU) | 8002 | ✅ |
| **cell-mes** | MES (작업지시, 실적, 설비) | 8000 | ✅ |
| **nl-router** | 자연어 처리 게이트웨이 | 8001 | ✅ |
| **cell-schedule-visualizer** | 스케줄 시각화 | - | ✅ |
| **digital-thread-project-manager** | DT 프로젝트 관리, CAM→XML | - | ✅ |
| **monitoring-data-replayer** | TDMS/LOG 리플레이 | - | ✅ |

---

## 🔗 에이전트 간 연결 관계도

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DESIGN / CAM PHASE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────┐         ┌──────────────────────┐                         │
│   │  STEP File   │────────►│  step-pmi-reader     │                         │
│   │  (CAD+PMI)   │         │  - PMI/GD&T 추출     │──────────┐              │
│   └──────────────┘         └──────────────────────┘          │              │
│                                                               │              │
│   ┌──────────────┐         ┌──────────────────────┐          │              │
│   │  CAM JSON    │────────►│  cam-runner          │          │              │
│   │  (PowerMill/ │         │  - Ap/Ae 분석        │          │              │
│   │   NX)        │         │  - Cycle Time 계산   │──────┐   │              │
│   └──────────────┘         └──────────────────────┘      │   │              │
│                                                           │   │              │
│   ┌──────────────┐         ┌──────────────────────┐      │   │              │
│   │  NC File     │────────►│  gcode-parser        │      │   │              │
│   │  (G-code)    │         │  - 경로 파싱         │──────┤   │              │
│   └──────────────┘         │  - T시퀀스 추출      │      │   │              │
│                            └──────────────────────┘      │   │              │
│                                                           ▼   ▼              │
│                            ┌─────────────────────────────────────────┐      │
│                            │  digital-thread-project-manager         │      │
│                            │  ─────────────────────────────────────  │      │
│                            │  • CAM JSON → ISO14649 XML 변환         │      │
│                            │  • dt_project 생성/관리                 │      │
│                            │  • PMI-Workingstep 연계 (TODO)          │      │
│                            │  • 품질 추적 (TODO)                     │      │
│                            └───────────────────┬─────────────────────┘      │
│                                                │                             │
└────────────────────────────────────────────────┼─────────────────────────────┘
                                                 │
                                                 │ dt_project
                                                 │ (workplan, workingsteps)
                                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PLANNING PHASE                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────┐       │
│   │  cell-mes (Port 8000)                                            │       │
│   │  ─────────────────────────────────────────────────────────────  │       │
│   │  • Product (제품 마스터)                                         │       │
│   │  • StdProcess (표준 공정)                                        │       │
│   │  • ProcessRouting (공정 경로)                                    │       │
│   │  • Equipment (설비)                                              │       │
│   │  • WorkOrder (작업지시)  ◄─────── dt_project 기반 생성           │       │
│   │  • ProdResult (실적)                                             │       │
│   └────────────────────────────────┬────────────────────────────────┘       │
│                                    │                                         │
│                                    │ WorkOrders + Equipment                  │
│                                    ▼                                         │
│   ┌─────────────────────────────────────────────────────────────────┐       │
│   │  cell-scheduler (Port 8002)                                      │       │
│   │  ─────────────────────────────────────────────────────────────  │       │
│   │  • OR-Tools / GA / SA / TABU 솔버                               │       │
│   │  • 설비 할당 + 시간 최적화                                       │       │
│   │  • Makespan 최소화                                               │       │
│   └────────────────────────────────┬────────────────────────────────┘       │
│                                    │                                         │
│                                    │ Schedule Result                         │
│                                    ▼                                         │
│   ┌─────────────────────────────────────────────────────────────────┐       │
│   │  cell-schedule-visualizer                                        │       │
│   │  ─────────────────────────────────────────────────────────────  │       │
│   │  • Gantt Chart 시각화                                            │       │
│   │  • 설비별 부하 분석                                              │       │
│   └─────────────────────────────────────────────────────────────────┘       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                                 │
                                                 │ Scheduled WorkOrders
                                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          EXECUTION PHASE                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────────────┐         ┌──────────────────────────────┐         │
│   │  실제 가공 / 설비     │────────►│  monitoring-data-replayer    │         │
│   │  (TDMS/LOG 생성)     │         │  ────────────────────────────│         │
│   └──────────────────────┘         │  • TDMS 파싱 (nptdms)        │         │
│                                    │  • LOG/TSV 파싱              │         │
│                                    │  • 실시간 리플레이            │         │
│                                    │  • WebSocket 스트리밍        │         │
│                                    └──────────────┬───────────────┘         │
│                                                   │                          │
│                                                   │ Monitoring Data          │
│                                                   ▼                          │
│   ┌─────────────────────────────────────────────────────────────────┐       │
│   │  cell-mes (실적 기록)                                            │       │
│   │  ─────────────────────────────────────────────────────────────  │       │
│   │  • ProdResult 생성                                               │       │
│   │  • Equipment.last_data 업데이트                                  │       │
│   │  • 이상 감지 시 EqLog 기록                                       │       │
│   └─────────────────────────────────────────────────────────────────┘       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                                 │
                                                 │ 품질 데이터
                                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          QUALITY TRACKING (TODO)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────┐       │
│   │  digital-thread-project-manager (품질 추적 모듈)                 │       │
│   │  ─────────────────────────────────────────────────────────────  │       │
│   │  • PMI ↔ Workingstep 연계                                       │       │
│   │  • NC Line ↔ Monitoring 동기화                                  │       │
│   │  • 이상 탐지 → 품질 리스크 평가                                  │       │
│   │  • 재검사 권고 생성                                              │       │
│   └─────────────────────────────────────────────────────────────────┘       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                                 │
                                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            USER INTERFACE                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────┐       │
│   │  nl-router (Port 8001) - 자연어 게이트웨이                       │       │
│   │  ─────────────────────────────────────────────────────────────  │       │
│   │  "오늘 작업 현황 알려줘" → cell-mes.daily_status                │       │
│   │  "Boss 시편 스케줄 잡아줘" → cell-scheduler.schedule            │       │
│   │  "진동 데이터 보여줘" → monitoring-data-replayer.replay         │       │
│   │  "품질 이상 있어?" → dt-project-manager.quality_check           │       │
│   └─────────────────────────────────────────────────────────────────┘       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 데이터 흐름 요약

```
STEP ──► step-pmi-reader ──┐
                           │
CAM JSON ──► cam-runner ───┼──► digital-thread-project-manager
                           │              │
NC ──► gcode-parser ───────┘              │
                                          │ dt_project
                                          ▼
                                    cell-mes (WorkOrder)
                                          │
                                          ▼
                                    cell-scheduler
                                          │
                                          ▼
                             cell-schedule-visualizer
                                          │
                                    (실행)
                                          │
                                          ▼
                             monitoring-data-replayer
                                          │
                                          ▼
                              cell-mes (ProdResult)
                                          │
                                          ▼
                        digital-thread-project-manager
                              (품질 추적 - TODO)
```

---

## 🔗 Digital Thread ↔ MES 매핑

| Digital Thread | MES | 설명 |
|----------------|-----|------|
| `dt_project` | - | 프로젝트 개념 없음 (TODO) |
| `its_workpieces.its_id` | `Product.code` | 제품 식별 |
| `main_workplan` | `ProcessRouting[]` | 공정 경로 |
| `workingstep` | `StdProcess` | 표준 공정 |
| `workingstep.its_tool` | - | 공구 관리 없음 (TODO) |
| `ref_dt_machine_tool` | `Equipment` | 설비 |
| `ref_nc_file` | `ProcessRoutingFile` | NC 프로그램 |

---

## 🔧 미구현 연결 (TODO)

| Priority | From | To | 내용 |
|----------|------|-----|------|
| 1 | dt-project-manager | cell-mes | dt_project → WorkOrder 자동 생성 |
| 2 | monitoring-replayer | cell-mes | 실시간 데이터 → Equipment 업데이트 |
| 3 | monitoring-replayer | dt-project-manager | 품질 추적용 데이터 연계 |
| 4 | step-pmi-reader | dt-project-manager | PMI-Workingstep 연계 |

---

## 📁 프로젝트 구조

```
agents-workspace/
├── agents/
│   ├── gcode-parser/
│   ├── cam-runner/
│   ├── step-pmi-reader/
│   ├── cell-scheduler/
│   ├── cell-mes/
│   ├── nl-router/
│   ├── cell-schedule-visualizer/
│   ├── digital-thread-project-manager/  ← 신규
│   └── monitoring-data-replayer/        ← 신규
├── samples/
│   └── digital-thread-project-manager/
│       ├── json/      # CAM JSON
│       ├── xml/       # dt_asset XML
│       ├── step/      # STEP+PMI
│       ├── tdms/      # 모니터링 데이터
│       └── nc/        # G-code
├── docs/
│   └── AGENT_ARCHITECTURE.md  ← 이 문서
├── orchestrator/
└── services.env
```

---

## 🚀 서비스 실행

```bash
cd ~/SynologyDrive/Drive/Development/agents-workspace

# 전체 시작
./start-services.sh

# 개별 시작
./start-services.sh mes       # Port 8000
./start-services.sh router    # Port 8001
./start-services.sh scheduler # Port 8002

# 상태 확인
./status-services.sh

# 중지
./stop-services.sh
```

---

*Last Updated: 2026-02-03*
