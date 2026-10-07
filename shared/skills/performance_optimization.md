# Performance Optimization

코드 병목 분석, 프로파일링, CP-SAT 솔버 튜닝, 실행 속도 개선.

## Critical Rules

1. **프로파일링 먼저, 최적화 나중** - 추측으로 최적화하지 않기
2. **베이스라인 측정 필수** - 개선 전후 비교 수치 기록
3. **가독성 vs 성능 트레이드오프 문서화** - 왜 최적화했는지 기록

## Instructions

### Step 1: 베이스라인 측정

```bash
time python orchestrator_main.py --workflow full
python -m cProfile -s cumulative orchestrator_main.py | head -30
```

### Step 2: 병목 식별 및 최적화

**자주 나오는 병목과 해결:**

| 병목 | 해결 | 개선 효과 |
|------|------|-----------|
| 파일 I/O 매번 로딩 | 캐시 (load once) | 100-500ms/call |
| 루프 내 regex 컴파일 | `re.compile()` 한 번만 | 20-50% |
| Python 중첩 루프 | NumPy 벡터화 | 100-1000x |
| 리스트 membership | `set` 사용 | 10-100x |

### Step 3: CP-SAT 솔버 튜닝

```python
params = cp_model.CpSolverParameters()
params.max_time_in_seconds = 30       # 기본 3600 → 30으로 줄임
params.log_search_progress = False     # 로깅 오버헤드 제거
params.num_workers = 4                 # CPU 코어 수만큼
params.use_symmetry_propagation = True
```

### Step 4: 개선 검증

```bash
time python orchestrator_main.py --workflow full
# improvement = (baseline - optimized) / baseline * 100%
```

## Examples

**regex 컴파일 최적화:**
```python
# Before: 루프 내 컴파일
for line in gcode_lines:
    match = re.search(r"G(\d+)", line)  # 매번 컴파일

# After: 한 번만 컴파일
GCODE_PATTERN = re.compile(r"G(\d+)")
for line in gcode_lines:
    match = GCODE_PATTERN.search(line)
```

**set membership:**
```python
# Before: O(n)
valid_codes = ["G00", "G01", "G02", "G03"]
if code in valid_codes: ...

# After: O(1)
valid_codes = {"G00", "G01", "G02", "G03"}
if code in valid_codes: ...
```

**CP-SAT 변수 감소:**
```python
# Before: start + end 변수 각각
start = model.NewIntVar(0, horizon, f"start_{op}")
end = model.NewIntVar(0, horizon, f"end_{op}")
model.Add(end == start + duration)

# After: start만, end는 암묵적
start = model.NewIntVar(0, horizon - duration, f"start_{op}")
# end = start + duration (계산으로 대체)
```

## Monitoring

```python
import time

def benchmark_workflow():
    times = {}
    for stage in workflow:
        start = time.perf_counter()
        execute_stage(stage)
        times[stage] = time.perf_counter() - start
    return times
```
