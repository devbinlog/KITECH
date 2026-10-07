# agents-workspace

Manufacturing AI Agent System - G-code 분석부터 스케줄링까지 완전한 제조 워크플로우 자동화

## 🚀 Quick Start

```bash
# 1. 환경 설정
cp .env.example .env.dev

# 2. 의존성 설치
uv sync

# 3. 서비스 시작
./start-services.sh

# 4. 상태 확인
./status-services.sh
```

**5분 안에 실행 가능!** 🎉

## 📁 Project Structure

```
agents-workspace/
├── agents/                    # 개별 에이전트들
│   ├── gcode-parser/         # G-code 파싱 및 분석
│   ├── cam-runner/           # CAM 경로 분석 및 사이클 타임
│   ├── step-pmi-reader/      # STEP PMI 추출
│   ├── cell-scheduler/       # OR-Tools 기반 스케줄링
│   ├── cell-schedule-visualizer/  # 간트 차트 시각화
│   ├── cell-mes/             # MES 백엔드 API
│   ├── nl-router/            # 자연어 처리 게이트웨이
│   ├── digital-thread-project-manager/  # ⭐ DT 프로젝트 관리
│   └── monitoring-data-replayer/        # ⭐ 모니터링 리플레이
├── orchestrator/             # LangGraph 워크플로우 오케스트레이션
├── shared/                   # 공유 유틸리티
│   ├── common/               # 로깅, 에러 핸들링
│   └── skills/               # AI 에이전트 스킬 정의
├── samples/                  # 샘플 데이터 및 테스트 입력
├── demo/                     # 데모 영상
├── docs/                     # 아키텍처 문서
└── tests/                    # 통합 테스트
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Frontend (React)                                │
│                           http://localhost:3000                              │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
┌───────────────┐         ┌───────────────┐         ┌───────────────┐
│   Cell-MES    │◄───────►│   NL-Router   │         │ Cell-Scheduler│
│   (8000)      │         │   (8001)      │         │   (8002)      │
│ REST API      │         │ 자연어 처리    │         │ 스케줄링 솔버  │
└───────┬───────┘         └───────────────┘         └───────┬───────┘
        │                                                   │
        │                   Redis Event Bus                 │
        └────────────────────────┬──────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
              ┌─────┴─────┐             ┌─────┴─────┐
              │   Redis   │             │  SQLite   │
              │  (6379)   │             │   (DB)    │
              └───────────┘             └───────────┘
```

### DDD Layer Structure (Cell-MES)

```
agents/cell-mes/src/
├── domain/           # 핵심 비즈니스 로직 (순수 Python)
│   └── production/
│       ├── entities.py     # WorkOrderEntity
│       ├── value_objects.py # LotNumber, Quantity
│       └── repository.py    # Repository 인터페이스
├── application/      # 유스케이스
│   └── production/
│       ├── commands.py      # CreateWorkOrder
│       └── handlers.py      # 핸들러
├── infrastructure/   # 외부 의존성
│   └── persistence/
└── app/              # FastAPI (API 엔드포인트)
```

자세한 내용은 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) 참조.

## 🔧 Services

| Service | Port | Description |
|---------|------|-------------|
| Cell-MES | 8000 | MES 백엔드 API (FastAPI) |
| NL-Router | 8001 | 자연어 처리 게이트웨이 |
| Cell-Scheduler | 8002 | 스케줄링 API |

## 📊 Key Features

### 1. G-code Analysis
```python
from agents.gcode_parser import GcodeParserAgent

agent = GcodeParserAgent()
result = agent.process("G00 X10 Y20\nG01 Z-5 F100")
# → 블록별 이동 거리, 가공 시간 분석
```

### 2. CAM Path Analysis
```python
from agents.cam_runner import CamRunnerAgent

agent = CamRunnerAgent()
result = agent.process(gcode_data)
# → Ap/Ae 계산, 사이클 타임 예측
```

### 3. Production Scheduling
```python
from agents.cell_scheduler import CellSchedulerAgent

agent = CellSchedulerAgent()
result = agent.process(input_dir, solver_type="OR_TOOLS")
# → 최적 스케줄, 간트 데이터
```

### 4. Workflow Orchestration
```python
from orchestrator import LangGraphOrchestrator

orch = LangGraphOrchestrator()
result = orch.run_workflow(gcode_input, "full-manufacturing")
# → G-code → CAM → Scheduling → Visualization 자동화
```

## 🧪 Testing

```bash
# 전체 테스트
uv run pytest

# 에이전트별 테스트
cd agents/gcode-parser && uv run pytest tests/

# 커버리지 측정
uv run pytest --cov=src --cov-report=html
```

### Test Results (2026-02-08)
| Agent | Tests | Status |
|-------|-------|--------|
| gcode-parser | 46 passed | ✅ |
| cam-runner | 54 passed, 24 skipped | ✅ |
| cell-scheduler | 157 passed, 9 skipped | ✅ |
| cell-mes | 355 passed, 1 skipped | ✅ |
| nl-router | 289 passed | ✅ |
| digital-thread-project-manager | 85 passed, 1 skipped | ✅ |
| monitoring-data-replayer | 30 passed | ✅ |
| step-pmi-reader | 18 passed | ✅ |
| **Total** | **1,034 passed, 35 skipped** | ✅ |

## ⚙️ Configuration

### 환경 설정 파일

```
프로젝트 루트/
├── .env.example     # 템플릿 (커밋)
├── .env.dev         # 개발 환경
├── .env.prod        # 운영 환경
└── services.env     # 포트 설정
```

### 주요 환경변수

```bash
# 서비스 URL
CELL_MES_URL=http://localhost:8000
NL_ROUTER_URL=http://localhost:8001
CELL_SCHEDULER_URL=http://localhost:8002
REDIS_URL=redis://localhost:6379

# 데이터베이스
DATABASE_URL=sqlite+aiosqlite:///./data/mes.db

# 인증 (프로덕션에서 반드시 변경!)
SECRET_KEY=your-secret-key
INTERNAL_SERVICE_KEY=your-internal-key

# CORS (쉼표 구분)
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# 로깅
LOG_LEVEL=INFO
```

### 환경별 설정

```bash
# 개발 환경
ENV=development
DEBUG=true

# 운영 환경
ENV=production
DEBUG=false
```

See `.env.example` for all options.

### Logging
```python
from shared.common import setup_logging, get_logger

setup_logging(level="INFO", format="json")
logger = get_logger(__name__)
logger.info("Processing", extra={"wo_id": "WO-001"})
```

### Error Handling
```python
from shared.common import ValidationError, error_handler

@error_handler
def process(data):
    if not data:
        raise ValidationError("Data required")
    return {"status": "success"}
```

## 📚 Documentation

### API Documentation
- **Cell-MES**: http://localhost:8000/api/docs
- **NL-Router**: http://localhost:8001/docs
- **Cell-Scheduler**: http://localhost:8002/api/docs

### Project Documentation
- [Development Guidelines](docs/DEVELOPMENT_GUIDELINES.md) - 개발 가이드라인
- [Database Schema](docs/db_Schema_v5.md) - DB 스키마 설계
- [Digital Thread SPC QMS](docs/DIGITAL_THREAD_SPC_QMS.md) - 품질 관리 시스템
- [Project Status](docs/TODO.md) - 현재 진행 상황
- [Claude Integration](docs/CLAUDE.md) - AI 에이전트 연동
- [Development Log](docs/CONVERSATION_LOG_2026-02-01-04.md) - 개발 기록

## 🛠️ Development

### Code Quality
```bash
# Lint
uv run ruff check agents/ orchestrator/

# Type check
uv run mypy agents/gcode-parser/src/

# Complexity analysis
uv run radon cc agents/ -a -s
```

### Adding a New Agent
1. Create directory: `agents/my-agent/`
2. Add `src/`, `tests/`, `pyproject.toml`
3. Register in `orchestrator/src/langgraph_orchestrator.py`
4. Add workflow in `samples/workflows/`

## 🤝 협업 (Mac + Windows)

본 프로젝트는 **SynologyDrive 폴더 동기화 + git** 모델로 Mac/Windows 분산 협업합니다.

| 문서 | 내용 |
|---|---|
| [docs/HANDOVER.md](docs/HANDOVER.md) | 신규 개발자 30분 온보딩 (양쪽 OS 셋업) |
| [docs/COLLABORATION.md](docs/COLLABORATION.md) | 협업 룰 (동시 편집 금지, 인계 체크리스트, 충돌 처리) |
| [docs/COLLABORATION-SYNOLOGY-EXCLUDE.md](docs/COLLABORATION-SYNOLOGY-EXCLUDE.md) | SynologyDrive 동기화 제외 패턴 — `.git/`, `.venv/`, `node_modules/` 등 |

### 단일 명령 인터페이스 (Makefile)
```bash
make up        # docker compose up -d
make ps        # 상태 확인
make test      # 백엔드 pytest
make check     # ruff + tsc + pytest 통합 검증
make seed      # mes.db 시드
```

Windows에서 `make` 미설치 시: `winget install GnuWin32.Make` 또는 `scripts/*.ps1` 직접 실행.

### Pre-commit hook
```bash
make pre-commit-install
# 또는: uv run pre-commit install
```
빌드 산출물·동기화 충돌 흔적·`.env.dev` 등이 실수로 커밋되지 않도록 자동 검사.

## 📄 License

MIT
