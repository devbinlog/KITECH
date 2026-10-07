# Test-Driven Code Updates

코드 변경 시 테스트를 동기화하는 워크플로우. 모든 코드 수정은 반드시 테스트 업데이트와 함께 커밋한다.

## Critical Rules

1. **테스트 없는 코드 변경 금지** - 모든 변경에 대응하는 테스트 필수
2. **커버리지 하락 금지** - 변경 전후 커버리지 비교, 하락 시 테스트 추가
3. **항상 `uv run` 사용** - `pytest`, `black`, `ruff` 모두 `uv run` 접두사
4. **깨진 테스트로 커밋 금지** - 모든 테스트 통과 후에만 커밋

## Instructions

### Step 1: 변경 전 베이스라인 확인

```bash
uv run pytest agents/<module>/tests/ -v --tb=short
uv run pytest agents/<module>/tests/ --cov=agents.<module>
```

결과 기록: 테스트 수, 커버리지 %, 영향받는 함수

### Step 2: 코드 변경 + 테스트 동시 업데이트

- 동작 변경 → 기존 테스트 assertion 업데이트
- 새 기능 추가 → 새 테스트 추가
- 시그니처 변경 → 테스트 입력/출력 즉시 반영

### Step 3: 테스트 실행 및 검증

```bash
# 모듈 단위 테스트
uv run pytest agents/<module>/tests/ -v

# 전체 테스트 (통합 포함)
uv run pytest tests/ -v

# 커버리지 리포트
uv run pytest agents/<module>/tests/ --cov=agents.<module> --cov-report=term-missing
```

### Step 4: 커밋 전 체크리스트

```bash
uv run pytest tests/ -v                                    # 전체 테스트
uv run pytest agents/<module>/tests/ --cov                 # 커버리지
uv run black agents/ shared/ orchestrator/                 # 포맷
uv run ruff check agents/ shared/ orchestrator/            # 린트
```

## Test Coverage Matrix

| 카테고리 | 중요도 | 예시 |
|----------|--------|------|
| Happy Path | Critical | 정상 입력, 일반 사용 패턴 |
| Boundary Values | High | 최소/최대값, 빈 입력, 0 |
| Invalid Input | High | 타입 불일치, 잘못된 포맷 |
| Error Handling | High | 예외 발생, 에러 메시지 |
| State Changes | Medium | 상태 변경, 순차 동작 |

## Examples

**기존 동작 변경 시:**
```python
# 구현이 strip() 추가됨 → 테스트도 업데이트
def test_parse_gcode_strips_whitespace():
    result = parse_gcode("G01 X10  \n")
    assert result[0] == "G01 X10"  # strip 반영
```

**새 기능 추가 시:**
```python
def test_g91_enables_incremental_mode():
    parser = GcodeParser()
    parser.parse("G91")
    assert parser.incremental_mode == True

def test_incremental_coordinates_are_relative():
    parser = GcodeParser()
    parser.position = {"x": 10, "y": 20, "z": 0}
    parser.incremental_mode = True
    result = parser.parse("G01 X5")
    assert result["new_position"]["x"] == 15  # 10 + 5
```

**커밋 메시지 예시:**
```
feat: Add G91 incremental coordinate mode support

- Implement G91/G90 mode switching
- Add 4 new tests covering all mode transitions
- All 16 tests passing, 97% coverage (+2%)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

## Troubleshooting

### 테스트 실패 시 판단 기준

1. `uv run pytest -v --tb=short`로 실패 메시지 확인
2. **의도된 동작 변경인가?**
   - YES → 테스트 assertion 업데이트
   - NO → 코드 버그 수정
3. 모든 테스트 통과될 때까지 반복

### 커버리지 하락 시

```bash
# 커버리지 미달 라인 확인
uv run pytest --cov --cov-report=term-missing

# 미달 라인에 대한 테스트 추가
```

## Anti-patterns

```python
# ❌ 코드 변경 후 테스트 미업데이트
def parse_gcode(text):
    return [line.strip() for line in text.split("\n")]  # 변경됨
def test_parse_gcode():
    assert result[0] == "G01 X10  "  # 옛날 assertion → 실패!

# ❌ 커버리지 하락 무시
# Before: 98% → After: 92%  # 6% 하락 무시!

# ❌ uv run 없이 실행
pytest tests/ -v           # ❌
uv run pytest tests/ -v    # ✅
```

## Related Skills

- [test_implementation.md](test_implementation.md) - pytest 픽스처, 테스트 패턴
- [error_handling.md](error_handling.md) - 에러 테스트 패턴
