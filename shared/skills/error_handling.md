# Error Handling

에이전트/함수 실행을 try-catch로 감싸고, 표준 AnalysisResult 객체를 반환. 예외를 raise하지 않고 에러를 축적하여 fault-tolerant 워크플로우 구현.

## Critical Rules

1. **프로덕션 에이전트에서 예외 raise 금지** - 항상 AnalysisResult 반환
2. **로그에 컨텍스트 포함** - agent name, stage name, 관련 데이터
3. **워크플로우에서 에러 축적** - 첫 번째 에러에서 중단하지 않고 계속 실행
4. **적절한 로그 레벨 사용** - ERROR: 실패, WARNING: 저하 모드, INFO: 진행

## AnalysisResult 구조

```python
@dataclass
class AnalysisResult:
    status: str  # "success", "warning", "error"
    message: str = ""
    data: dict = field(default_factory=dict)
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
```

## Instructions

### Step 1: safe_execute 래퍼 사용

```python
def safe_execute(func, inputs, context=None):
    context = context or {}
    agent_name = context.get("agent_name", "unknown")
    try:
        result = func(**inputs)
        return AnalysisResult(status="success", data=result)
    except ValueError as e:
        logger.error(f"Invalid input in {agent_name}: {e}")
        return AnalysisResult(status="error", errors=[str(e)])
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return AnalysisResult(status="error", errors=[str(e)])
    except ImportError as e:
        logger.warning(f"Optional library unavailable: {e}")
        return AnalysisResult(status="warning", warnings=[str(e)])
    except Exception as e:
        logger.exception(f"Unexpected error in {agent_name}")
        return AnalysisResult(status="error", errors=[f"{type(e).__name__}: {e}"])
```

### Step 2: 예외 분류

| 레벨 | 예외 | status |
|------|------|--------|
| Error | ValueError, TypeError, FileNotFoundError, KeyError, TimeoutError | `"error"` |
| Warning | ImportError, DeprecationWarning | `"warning"` |

### Step 3: 워크플로우에서 에러 축적

```python
def orchestrate_workflow(stages, state):
    for stage_name, agent in stages:
        try:
            result = agent.execute(state)
            if result.status == "error":
                state["stage_errors"].append({"stage": stage_name, "error": result.errors})
            else:
                state["stage_results"][stage_name] = result.data
        except Exception as e:
            state["stage_errors"].append({"stage": stage_name, "error": str(e)})
    # partial_success if some succeeded, some failed
```

## Examples

**구조화된 로깅:**
```python
logger.info("Starting analysis", extra={"agent": agent_name, "lines": len(gcode.split("\n"))})
logger.error("Parse error", extra={"agent": agent_name, "error": str(e), "preview": gcode[:100]})
```

**로거 설정:**
```python
def setup_logging(agent_name, log_level=logging.INFO):
    logger = logging.getLogger(agent_name)
    logger.setLevel(log_level)
    if logger.handlers:
        return logger
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    return logger
```

**테스트:**
```python
def test_error_on_invalid_input():
    result = safe_execute(parser.analyze, {"gcode_source": None}, {"agent_name": "gcode_parser"})
    assert result.status == "error"
    assert len(result.errors) > 0

def test_warning_on_missing_library():
    result = safe_execute(cam.analyze_with_stock, {"gcode_blocks": []}, {"agent_name": "cam"})
    assert result.status == "warning"
```
