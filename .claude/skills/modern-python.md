---
name: modern-python
description: Modern Python development with uv, ruff, pytest. Use for Python best practices.
---

# Modern Python Development

Best practices for Python development using modern tooling.

## Package Management with uv

**Install dependencies:**
```bash
uv sync                    # Install from pyproject.toml
uv add package-name        # Add new dependency
uv add --dev pytest        # Add dev dependency
uv remove package-name     # Remove dependency
```

**Run commands:**
```bash
uv run python script.py    # Run with project environment
uv run pytest              # Run tests
uv run ruff check .        # Run linter
```

**Lock files:**
```bash
uv lock                    # Update lock file
uv sync --frozen           # Install exact versions from lock
```

## Code Quality with ruff

**Configuration in pyproject.toml:**
```toml
[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # Pyflakes
    "I",      # isort
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "UP",     # pyupgrade
]
ignore = ["E501"]  # Line too long (handled by formatter)

[tool.ruff.lint.isort]
known-first-party = ["src"]
```

**Commands:**
```bash
uv run ruff check .        # Check for issues
uv run ruff check --fix .  # Auto-fix issues
uv run ruff format .       # Format code
```

## Testing with pytest

**Configuration in pyproject.toml:**
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-v --tb=short"
asyncio_mode = "auto"
```

**Commands:**
```bash
uv run pytest                          # Run all tests
uv run pytest tests/unit/              # Run specific directory
uv run pytest -k "test_name"           # Run matching tests
uv run pytest --cov=src                # With coverage
uv run pytest -x                       # Stop on first failure
uv run pytest --tb=long                # Verbose tracebacks
```

**Test structure:**
```python
import pytest
from src.module import function

class TestFunction:
    def test_basic_case(self):
        result = function(input)
        assert result == expected
    
    def test_edge_case(self):
        with pytest.raises(ValueError):
            function(invalid_input)
    
    @pytest.fixture
    def sample_data(self):
        return {"key": "value"}
    
    def test_with_fixture(self, sample_data):
        result = function(sample_data)
        assert result is not None
```

## Type Hints

**Modern syntax (Python 3.10+):**
```python
# Use built-in types
def process(items: list[str]) -> dict[str, int]:
    return {item: len(item) for item in items}

# Union with |
def fetch(id: int | str) -> User | None:
    ...

# TypedDict for structured dicts
from typing import TypedDict

class Config(TypedDict):
    host: str
    port: int
    debug: bool

# Protocols for duck typing
from typing import Protocol

class Serializable(Protocol):
    def to_dict(self) -> dict: ...
```

**Type checking:**
```bash
uv run mypy src/            # Full type check
uv run mypy --strict src/   # Strict mode
```

## Project Structure

```
project/
├── pyproject.toml          # Project config (dependencies, tools)
├── uv.lock                  # Lock file (commit this)
├── src/
│   └── package/
│       ├── __init__.py
│       ├── main.py
│       └── utils.py
├── tests/
│   ├── conftest.py         # Shared fixtures
│   ├── unit/
│   │   └── test_utils.py
│   └── integration/
│       └── test_api.py
└── .github/
    └── workflows/
        └── ci.yml
```

## pyproject.toml Template

```toml
[project]
name = "my-package"
version = "0.1.0"
description = "Project description"
requires-python = ">=3.11"
dependencies = [
    "httpx>=0.27",
    "pydantic>=2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=4.0",
    "ruff>=0.3",
    "mypy>=1.8",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

## CI/CD Template

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install uv
        uses: astral-sh/setup-uv@v4
      
      - name: Set up Python
        run: uv python install 3.11
      
      - name: Install dependencies
        run: uv sync --all-extras
      
      - name: Lint
        run: uv run ruff check .
      
      - name: Type check
        run: uv run mypy src/
      
      - name: Test
        run: uv run pytest --cov
```

## SQLAlchemy + SQLite 주의사항

### BIGINT 자동증가 제한

SQLite는 `INTEGER PRIMARY KEY`만 `ROWID` alias로 자동증가를 지원한다. SQLAlchemy의 `BigInteger`는 SQLite에서 `BIGINT`로 매핑되어 자동증가가 동작하지 않는다.

```python
# ❌ SQLite에서 INSERT 시 NOT NULL constraint failed 에러
from sqlalchemy import BigInteger
id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

# ✅ SQLite에서 정상 자동증가
from sqlalchemy import Integer
id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
```

**Rule**: SQLite를 사용하는 프로젝트에서는 primary key에 `BigInteger` 대신 `Integer`를 사용한다. PostgreSQL 마이그레이션이 필요한 경우에도 SQLite 개발환경에서는 `Integer`를 유지하고 production DDL에서만 `BIGINT` 사용.

### OccupiedSlot 패턴 (스케줄러 연동 시)

기존 생산실적이 점유 중인 시간대를 스케줄러에 전달하지 않으면 시간 충돌 발생. DB에서 기존 `ProdResult`의 `start_time`/`end_time`을 조회하여 `occupied_slots`로 변환 후 스케줄러에 전달해야 한다:

```python
# MES → Scheduler 설비 데이터에 점유구간 포함
async def _get_occupied_slots(self, equipment_ids, horizon_start, horizon_end):
    query = select(ProdResult).where(and_(
        ProdResult.target_equipment_id.in_(equipment_ids),
        ProdResult.start_time < horizon_end,
        ProdResult.end_time > horizon_start,
    ))
    # ... 초 단위로 변환하여 반환
```

## Best Practices

1. **Always use uv for package management** - Faster, more reliable than pip
2. **Run ruff before committing** - Catches issues early
3. **Write tests first** - See TDD skill
4. **Use type hints everywhere** - Better tooling, fewer bugs
5. **Keep dependencies minimal** - Less maintenance burden
6. **Pin versions in lock file** - Reproducible builds
7. **SQLite PK는 Integer 사용** - BigInteger는 자동증가 불가
8. **스케줄러 연동 시 occupied_slots 전달** - 기존 점유구간 누락 시 시간 충돌
