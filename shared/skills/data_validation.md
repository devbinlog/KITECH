# Data Validation

JSON/dict 입력을 dataclass로 변환하고 필드 타입, 범위, 관계를 검증. 타입 강제 변환과 상세 에러 리포팅 지원.

## Critical Rules

1. **`__post_init__`으로 검증** - dataclass 생성 시 자동 검증
2. **에러 축적 (no early exit)** - 첫 번째 에러에서 중단하지 않고 모든 에러 수집
3. **strict/lenient 모드 분리** - strict: 타입 불일치 시 에러, lenient: 자동 변환 시도

## Instructions

### Step 1: Dataclass 정의 + 검증

```python
@dataclass
class GcodeBlock:
    block_number: int
    command: str
    position: list[float]  # [x, y, z]
    feed_rate: Optional[float] = None

    def __post_init__(self):
        if len(self.position) != 3:
            raise ValueError(f"Position must have 3 coords, got {len(self.position)}")
        if self.feed_rate is not None and self.feed_rate < 0:
            raise ValueError(f"Feed rate must be non-negative, got {self.feed_rate}")
```

### Step 2: 중첩 구조 검증

```python
@dataclass
class CutterPath:
    tool: Tool          # 중첩 dataclass
    blocks: list[GcodeBlock]
    material: str
```

### Step 3: validate_data 함수 사용

```python
def validate_data(data_source, target_class, strict_mode=True):
    if isinstance(data_source, str):
        data_source = json.loads(data_source)
    try:
        obj = target_class(**data_source)
        return {"status": "success", "data": {"validated_object": obj}}
    except (TypeError, ValueError) as e:
        return {"status": "error", "errors": [{"field": "unknown", "error": str(e)}]}
```

## Examples

**범위 검증:**
```python
@dataclass
class MachineConfig:
    name: str
    utilization: float  # 0.0-1.0
    def __post_init__(self):
        if not 0.0 <= self.utilization <= 1.0:
            raise ValueError(f"Utilization must be 0.0-1.0, got {self.utilization}")
```

**Enum 검증:**
```python
class ToolType(Enum):
    CYL_CUTTER = "CylCutter"
    BALL_CUTTER = "BallCutter"

@dataclass
class Tool:
    type: ToolType
    def __post_init__(self):
        if isinstance(self.type, str):
            self.type = ToolType(self.type)
```

**패턴 매칭:**
```python
@dataclass
class WorkOrder:
    wo_id: str
    def __post_init__(self):
        if not re.match(r"^WO-\d{6}$", self.wo_id):
            raise ValueError(f"Invalid work order ID: {self.wo_id}")
```

**에이전트에서 사용:**
```python
class CellSchedulerAgent(BaseAgent):
    def execute(self, inputs: dict) -> AnalysisResult:
        validation = validate_data(inputs, ScheduleInput, strict_mode=False)
        if validation["status"] == "error":
            return AnalysisResult(status="error", errors=validation["errors"])
        schedule_input = validation["data"]["validated_object"]
        schedule = self.scheduler.solve(schedule_input)
        return AnalysisResult(status="success", data=schedule)
```

**테스트:**
```python
def test_valid_data():
    data = {"block_number": 1, "command": "G01", "position": [10.0, 20.0, 0.0]}
    result = validate_data(data, GcodeBlock)
    assert result["status"] == "success"

def test_validation_error():
    data = {"block_number": 1, "command": "G01", "position": [10.0, 20.0]}  # 2개만
    result = validate_data(data, GcodeBlock)
    assert result["status"] == "error"
```
