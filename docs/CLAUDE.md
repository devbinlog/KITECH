# Claude Code Project Context

## Project Overview

Manufacturing Agents Workspace - 제조 MES 시스템과 스케줄링 에이전트들의 모노레포.

## Technology Stack

### Backend
- **Python >=3.11** with **uv** package manager (REQUIRED)
- **FastAPI** for REST APIs
- **SQLAlchemy** (async) for database
- **Pydantic** for validation
- **OR-Tools** + Metaheuristics for scheduling

### Frontend
- **Next.js 14** with App Router
- **TypeScript**
- **TailwindCSS**
- **React Query** for data fetching

## Project Structure

```
agents-workspace/
├── agents/
│   ├── cell-mes/                  # MES System (Backend + Frontend)
│   ├── cell-scheduler/            # Scheduling Service (port 8002)
│   ├── cell-schedule-visualizer/  # Gantt Chart Visualization
│   ├── nl-router/                 # Natural Language Router (port 8001)
│   ├── gcode-parser/              # G-code Parser Agent
│   ├── cam-runner/                # CAM Computation Agent
│   ├── digital-thread-project-manager/  # CAM→ISO 14649 XML
│   ├── monitoring-data-replayer/  # Monitoring Data Replay
│   ├── step-pmi-reader/           # STEP PMI Feature Extraction
│   └── torus-mock/                # TORUS Platform Mock Server
├── orchestrator/          # LangGraph workflow orchestration
├── shared/
│   └── skills/            # Development skills & patterns
├── samples/               # Test data & workflow definitions
└── tests/                 # Integration tests
```

## Critical Rules

### 1. Always Use uv (pip 사용 금지)
```bash
# ✅ CORRECT
uv sync
uv run pytest tests/ -v
uv run ruff format agents/ shared/
uv run ruff check agents/ shared/

# ❌ WRONG - Never use pip directly
pip install package
```

### 2. uv Workspace 규칙 (반드시 준수)
```bash
# uv.lock은 루트에 단 1개만 존재해야 함
# ❌ agents/cell-mes/uv.lock  ← 절대 만들지 말 것
# ✅ /uv.lock                 ← 루트만 허용

# 새 의존성 추가 시 항상 루트에서 실행
uv add <package>      # 루트에서
uv sync               # 루트에서

# Python 버전은 모든 멤버가 >=3.11로 통일
# [dependency-groups]와 [project.optional-dependencies] 이중 정의 금지
#   → optional-dependencies만 사용
# Hatch wheel packages는 디렉토리(["src"])를 가리켜야 함, 파일 아님
```
- Reference: `shared/skills/uv_workspace.md`

### 3. Test-Driven Development
- Run tests before and after changes
- Coverage must not drop
- Reference: `shared/skills/test_driven_updates.md`

### 4. Code Quality
```bash
# Before every commit
uv run pytest tests/ -v              # Tests pass
uv run ruff format agents/ shared/   # Formatted
uv run ruff check agents/ shared/    # Linted
```

### 5. Commit Message Format
```
<type>: Brief description

- Specific change 1
- Specific change 2

Tests:
- Added X tests
- All N tests passing

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

## Available Commands

| Command | Description |
|---------|-------------|
| `/test` | Run tests for module |
| `/format` | Format and lint code |
| `/check` | Pre-commit checks |
| `/commit` | Create proper commit |
| `/sync` | Sync dependencies |
| `/coverage` | Check test coverage |
| `/skill` | Load development skill |
| `/start-mes` | Start MES services |

## Key Development Skills

Located in `shared/skills/`:

- **uv_workspace.md** - uv workspace 관리 규칙 (필독)
- **test_driven_updates.md** - Code change workflow
- **test_implementation.md** - Test patterns
- **error_handling.md** - Error patterns
- **config_management.md** - Config loading
- **data_validation.md** - Validation patterns
- **dependency_integration.md** - Dependency management
- **service_management.md** - Service 운영/트러블슈팅

## Service Ports

| Service | Port |
|---------|------|
| Cell-MES Backend | 8000 |
| NL-Router | 8001 |
| Cell-Scheduler | 8002 |
| Cell-MES Frontend | 3000 |

## Common Tasks

### Seed MES Data (통합 시드 스크립트)
```bash
cd agents/cell-mes

# 기준일 = 오늘, 30일간 데이터 생성
uv run python -m src.seed_data

# 특정 기준일 지정
uv run python -m src.seed_data --date 2026-02-10

# 60일간 데이터 생성
uv run python -m src.seed_data --days 60

# 기존 데이터 무결성 검증만
uv run python -m src.seed_data --validate
```
- 마스터, 작업지시, 생산실적, 품질(검사/SPC/NCR), 다운타임, 알람, 설비이력을 한 번에 생성
- `--date` 기준일에 따라 LOT 번호(`LOT-YYYYMMDD-NNN`)와 모든 날짜가 일관되게 결정
- `seed_quality_data.py`, `seed_historical_data.py`는 deprecated → `seed_data.py`로 통합됨

### Run Specific Agent Tests
```bash
uv run pytest agents/cell-scheduler/tests/ -v
```

### Check Coverage
```bash
uv run pytest agents/cell-scheduler/tests/ --cov=agents.cell_scheduler
```

### Start Development Server
```bash
./start-services.sh
```

## Guidelines Reference

For detailed guidelines, see:
- `DEVELOPMENT_GUIDELINES.md` - Full development workflow
- `shared/skills/README.md` - Skills catalog
