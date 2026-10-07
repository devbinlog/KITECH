# Test Implementation

pytest 픽스처, 테스트 케이스, assertion 작성 패턴. result object 구조 검증, 엣지 케이스 커버리지, 외부 의존성 mocking.

## Critical Rules

1. **Arrange-Act-Assert 패턴** - 모든 테스트에 적용
2. **항상 `uv run pytest` 사용** - 직접 `pytest` 실행 금지
3. **커버리지 목표: 라인 80%+, 크리티컬 패스 95%+**
4. **result 구조 반드시 검증** - status, data, errors, warnings 필드

## Instructions

### 테스트 구조 (Arrange-Act-Assert)

```python
def test_gcode_parser_valid_input():
    # Arrange
    gcode = "G00 X10 Y20\nG01 Z-5 F100"
    # Act
    result = gcode_parser_agent.analyze(gcode)
    # Assert
    assert result["status"] == "success"
    assert len(result["data"]["blocks"]) == 2
```

### 픽스처 패턴

```python
@pytest.fixture
def sample_gcode():
    return "G00 X10 Y20\nG01 Z-5 F100\nM03 S1000"

@pytest.fixture
def mock_tool():
    return {"type": "CylCutter", "diameter": 6.0, "radius": 3.0}

@pytest.fixture
def gcode_file(tmp_path):
    file_path = tmp_path / "test.nc"
    file_path.write_text("G00 X10\nG01 Z-5")
    return file_path
```

### Mocking 패턴

```python
@patch("google.ortools.sat.python.cp_model.CpModel")
def test_scheduler_with_mocked_solver(mock_cp_model):
    mock_cp_model.return_value = MagicMock()
    result = scheduler.schedule(operations, machines)
    assert mock_cp_model.called
```

### Result Object 검증

```python
def assert_result_structure(result):
    assert isinstance(result, dict)
    assert result["status"] in ["success", "warning", "error"]
    assert "data" in result or "errors" in result
    assert isinstance(result.get("errors"), list)
```

## Examples

**엣지 케이스 테스트:**
```python
class TestGcodeParser:
    def test_empty_gcode(self):
        assert parser.analyze("")["status"] == "error"

    def test_single_block(self):
        assert len(parser.analyze("G01 X10 Y20")["data"]["blocks"]) == 1

    def test_max_coordinates(self):
        assert parser.analyze("G01 X999999 Y999999")["status"] == "success"

    def test_invalid_gcode(self):
        assert "warnings" in parser.analyze("G99 X10")
```

## Commands

```bash
uv run pytest tests/ -v                                          # 전체
uv run pytest tests/ --cov=agents --cov=shared --cov-report=html # 커버리지
uv run pytest tests/test_gcode.py::TestGcodeParser -v            # 특정 클래스
uv run pytest tests/ -m "not slow"                               # 마커 필터
```

## Test File Organization

```
agents/<module>/tests/
├── test_agent.py           # 단위 테스트
├── conftest.py             # 공유 픽스처
tests/
├── integration/
│   └── test_full_workflow.py
└── fixtures/
    ├── sample_gcode.txt
    └── sample_schedule_input.json
```
