# 병합 노트: `lot_no` 의미 분리 (`sublot_no` 신설)

## 요약
스케줄링 결과의 `lot_no`가 **두 의미로 혼용**되어 분리함.

| 의미 | 변경 전 | 변경 후 |
|------|---------|---------|
| 분할 조각 순번 (qty/lot_size, 예 1,2,3) | `lot_no` (int) | **`sublot_no`** (int) |
| 작업지시 별칭 (MES `work_orders.lot_no`) | (없음) | **`lot_no`** (str) |

## 결과 JSON 변경
```diff
- "lot_no": 1,            // 분할 순번 (int)
+ "sublot_no": 1,         // 분할 순번 (int)
+ "lot_no": "LOT-001",    // 작업지시 별칭 (str)
```


## 변경 파일 (전부 `agents/cell-scheduler/`, cell-mes 무변경)
- `src/app/schemas.py` — `WorkOrderSchema`에 `lot_no` 추가, `ScheduledTaskSchema` 필드 분리
- `src/solvers/base_solver.py`, `src/solvers/ortools_solver.py` — 내부 변수/생성부 `sublot_no` 정리, 별칭 `lot_no` 기록
- `src/app/services/scheduler_service.py` — 변환·응답에 두 필드 반영
- `src/app/output_saver.py`, `run_scheduler.py`, `run_samples.py` — 라벨/출력 dict
- `tests/test_features.py`, `tests/test_solver_scheduling.py`


