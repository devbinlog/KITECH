# uv Workspace 관리

## Critical Rules

1. **uv.lock은 루트에 단 1개만** - 에이전트 하위에 절대 만들지 말 것
2. **Python >=3.11 통일** - 모든 멤버 pyproject.toml에서 동일해야 함
3. **optional-dependencies만 사용** - `[dependency-groups]` 금지 (충돌 원인)
4. **Hatch packages는 디렉토리** - `packages = ["src"]` (파일 경로 금지)
5. **공통 의존성 버전 통일** - 에이전트마다 다르면 resolve 실패

## Instructions

### Step 1: 의존성 추가/변경

항상 **프로젝트 루트에서** 실행:

```bash
uv add --package cell-mes <new-package>   # 특정 에이전트에 추가
uv sync                                    # 전체 동기화
```

### Step 2: 새 에이전트 추가

1. `agents/<agent-name>/` 디렉토리 생성
2. pyproject.toml 작성 (아래 템플릿)
3. 루트 `pyproject.toml`의 `[tool.uv.workspace].members`에 추가
4. 루트에서 `uv sync` 실행
5. 에이전트 하위에 uv.lock 생기지 않았는지 확인

```toml
[project]
name = "new-agent"
version = "0.1.0"
description = "Description"
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src"]
```

### 표준 의존성 버전

여러 에이전트에서 사용하는 라이브러리는 반드시 동일 버전 범위 유지:

```toml
fastapi >= 0.109.0
uvicorn[standard] >= 0.27.0
pydantic >= 2.5.0
httpx >= 0.26.0
pytest >= 7.4.0
pytest-asyncio >= 0.23.0
```

## Examples

**에이전트에 새 패키지 추가:**
```bash
# 루트에서 실행
uv add --package cell-scheduler numpy
uv sync
```

**lock 재생성:**
```bash
rm uv.lock && uv lock && uv sync
```

## Troubleshooting

### uv sync/lock 실패

**체크리스트:**
```bash
# 1. 에이전트 하위 uv.lock 확인 → 있으면 삭제
find agents/ -name "uv.lock" -type f

# 2. Python 버전 확인 → 모두 >=3.11인지
grep -r "requires-python" agents/*/pyproject.toml pyproject.toml

# 3. dependency-groups 이중 정의 확인 → 있으면 제거
grep -r "\[dependency-groups\]" agents/*/pyproject.toml
```

### 흔한 에러

| 에러 | 원인 | 해결 |
|------|------|------|
| `No solution found` | 버전 충돌 | 에이전트 간 버전 범위 통일 |
| `requires Python >=X.Y` | Python 버전 불일치 | 모든 멤버 `>=3.11`로 통일 |
| `Multiple workspace roots` | 에이전트에 별도 lock | `rm agents/*/uv.lock` |
| `Build failed` | Hatch packages 경로 | `packages = ["src"]`로 수정 |

### 완전 초기화 (최후 수단)

```bash
rm -f uv.lock
find agents/ -name "uv.lock" -delete
rm -rf .venv
uv lock && uv sync
```

## Anti-patterns

```bash
cd agents/cell-mes && uv sync   # ❌ 에이전트 하위에서 실행
pip install fastapi              # ❌ pip 사용
```

```toml
# ❌ 에이전트마다 다른 Python 버전
requires-python = ">=3.10"  # cell-scheduler
requires-python = ">=3.11"  # nl-router

# ❌ dependency-groups와 optional-dependencies 동시 사용
[project.optional-dependencies]
dev = ["pytest>=7.0"]
[dependency-groups]
dev = ["pytest>=9.0"]

# ❌ Hatch packages에 파일 지정
packages = ["src/my_agent.py"]
```
