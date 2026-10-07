# Cell MES Agent

Manufacturing Execution System 백엔드 API

## Quick Start

```bash
cd agents/cell-mes
uv sync

# DB 초기화
uv run python -c "
from src.app.db.session import engine
from src.app.db.base import Base
import asyncio
async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
asyncio.run(init())
"

# 서버 시작
uvicorn src.app.main:app --port 8000
```

## API Endpoints

### Equipment
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/equipment | 장비 목록 |
| GET | /api/v1/equipment/{id} | 장비 상세 |
| GET | /api/v1/equipment/{id}/status | 장비 상태 |

### Work Orders
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/work-orders | 작업지시 목록 |
| POST | /api/v1/work-orders | 작업지시 생성 |
| GET | /api/v1/work-orders/{id} | 작업지시 상세 |

### Production
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/production/summary | 생산 요약 |
| GET | /api/v1/production/results | 생산 실적 |
| POST | /api/v1/production/results | 실적 등록 |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/analytics/kpi | KPI 조회 |
| GET | /api/v1/analytics/oee | OEE 분석 |

## Database

SQLite (개발) / PostgreSQL (운영)

```bash
# 테스트 데이터 생성
uv run python -m src.seed_data
uv run python -m src.seed_historical_data
```

## Environment Variables

```bash
DATABASE_URL=sqlite+aiosqlite:///./data/mes.db
SECRET_KEY=your-secret-key
```

## Swagger UI

http://localhost:8000/api/docs

## Testing

```bash
uv run pytest tests/ -v
uv run pytest tests/ --cov=src
```

**Test Results**: 530 tests collected, 530 passed (as of 2026-02-21)
- Full test suite includes unit tests, integration tests, API contract tests, and functional regression tests
- State machine tests fixed: WorkOrder PAUSE<->ERROR transitions corrected
- All datetime migration fixes verified
