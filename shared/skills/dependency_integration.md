# Dependency Integration

선택적/조건부 의존성(OpenCAMLib, OR-Tools, Plotly) 관리. 라이브러리 미설치 시 graceful fallback, 버전 충돌 처리, feature flag 관리.

## Critical Rules

1. **항상 `uv add` 사용** - `pip install` 금지. 상세: [uv_workspace.md](uv_workspace.md)
2. **`[dependency-groups]` 사용 금지** - `[project.optional-dependencies]`만 사용
3. **공통 의존성 버전 통일** - 에이전트마다 다르면 uv resolve 실패
4. **필수 의존성은 fail fast** - 선택 의존성만 fallback 처리

## Instructions

### Step 1: 의존성 추가

```bash
# 루트에서 실행 (필수)
uv add --package cell-mes <package>
uv sync
```

### Step 2: Conditional Import 패턴 적용

```python
try:
    import opencamlib as ocl
    HAS_OPENCAMLIB = True
except ImportError:
    HAS_OPENCAMLIB = False
    logging.warning("opencamlib not installed; advanced features unavailable")
```

### Step 3: Fallback 전략 선택

| 전략 | 사용 시점 | 패턴 |
|------|-----------|------|
| **Error** | 필수 의존성 (ortools) | `raise ImportError` |
| **Warning** | 향상 기능 (opencamlib) | `logger.warning()`, 계속 실행 |
| **Disable** | 부가 기능 (plotly) | feature 비활성화, 대체 사용 |

### Step 4: pyproject.toml 작성

```toml
[project]
requires-python = ">=3.11"
dependencies = [
    "ortools>=9.7.2996",    # 필수
    "numpy>=1.24.0",        # 필수
]

[project.optional-dependencies]
advanced = ["opencamlib>=1.0.0"]
visualization = ["plotly>=5.0.0"]
dev = ["pytest>=7.4.0", "pytest-asyncio>=0.23.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src"]  # 디렉토리만, 파일 경로 금지
```

## Standard Versions

에이전트 간 공통 라이브러리는 동일 버전 범위 유지:

```toml
fastapi >= 0.109.0
uvicorn[standard] >= 0.27.0
pydantic >= 2.5.0
httpx >= 0.26.0
pytest >= 7.4.0
pytest-asyncio >= 0.23.0
```

## Examples

**필수 의존성 체크:**
```python
def check_required_dependency(lib_name, min_version=None):
    try:
        lib = __import__(lib_name)
        if min_version:
            from packaging import version
            if version.parse(lib.__version__) < version.parse(min_version):
                raise ImportError(f"{lib_name} {lib.__version__} < {min_version}")
        return lib
    except ImportError as e:
        raise ImportError(f"Install with: uv add {lib_name}") from e
```

**선택 의존성 fallback:**
```python
def analyze_with_stock(gcode_blocks, tool, stock_model=None):
    if HAS_OPENCAMLIB and stock_model is not None:
        result = advanced_cam_runner.analyze(gcode_blocks, tool, stock_model)
        result["mode"] = "advanced"
        return result
    result = simple_cam_runner.analyze(gcode_blocks, tool)
    result["mode"] = "simple"
    return result
```

**테스트에서 의존성 스킵:**
```python
import pytest

pytestmark = pytest.mark.skipif(
    not HAS_OPENCAMLIB, reason="OpenCAMLib not installed"
)

class TestAdvancedCAM:
    def test_stock_model_analysis(self):
        ...
```

## Anti-patterns

```bash
pip install opencamlib          # ❌ pip 사용
uv add opencamlib               # ❌ 에이전트 하위에서 실행
uv add --package cam-runner opencamlib  # ✅ 루트에서 실행
```

```toml
# ❌ dependency-groups와 optional-dependencies 동시 사용
[project.optional-dependencies]
dev = ["pytest>=7.0"]
[dependency-groups]
dev = ["pytest>=9.0"]

# ❌ Hatch packages에 파일 지정
packages = ["src/my_agent.py"]  # ❌
packages = ["src"]              # ✅
```
