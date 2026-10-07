# Service Management

agents-workspace 서비스 시작/중지, 인증 패턴, DB 관리, 트러블슈팅 가이드.

## Critical Rules

1. **포트 변경 시 `services.env`와 각 서비스 `.env` 둘 다 수정**
2. **내부 서비스 호출은 `X-Internal-Service-Key` 헤더 사용** (JWT 아님)
3. **base_url에 `/api/v1` 포함 금지** - endpoint에만 넣을 것
4. **uv workspace 규칙 준수** - 상세: [uv_workspace.md](uv_workspace.md)

## 서비스 구조

```
Frontend (React, :3000)
    ├── Cell-MES (:8000)
    ├── NL-Router (:8001)
    └── Cell-Scheduler (:8002)
```

## Instructions

### 서비스 시작/중지

```bash
./start-services.sh                    # 전체 시작
./start-services.sh mes|router|scheduler  # 개별 시작
./stop-services.sh                     # 전체 중지
./status-services.sh                   # 상태 확인
```

### 내부 서비스 인증

**Cell-MES (서버측 - deps.py):**
```python
async def get_current_user(db, token, x_internal_service_key):
    if x_internal_service_key == settings.INTERNAL_SERVICE_KEY:
        return ServiceUser()
    # 일반 JWT 인증 ...
```

**NL-Router (클라이언트측):**
```python
headers = {"X-Internal-Service-Key": INTERNAL_SERVICE_KEY}
response = await self.http_client.request(method=call.method, url=endpoint, headers=headers)
```

### DB 완전 리셋 (Cell-MES SQLite)

```bash
# 1. 서비스 중단
./stop-services.sh

# 2. DB 삭제 및 재생성
rm -f agents/cell-mes/data/mes.db
cd agents/cell-mes
uv run python -c "
import asyncio
from src.app.db.session import engine
from src.app.db.base import Base
from src.app.models import equipment, master, production, user
async def create():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('Done!')
asyncio.run(create())
"

# 3. 시드 데이터
uv run python -m src.seed_data
uv run python -m src.seed_historical_data

# 4. 재시작
cd ../..
./start-services.sh
```

### Alembic 마이그레이션

```bash
uv run alembic current                           # 현재 버전
uv run alembic revision --autogenerate -m "msg"  # 생성
uv run alembic upgrade head                      # 적용
uv run alembic stamp head                        # 현재 상태 기록
```

마이그레이션 꼬임 시: DB 완전 리셋이 가장 빠름

## Troubleshooting

### 포트 충돌

```bash
ps aux | grep "port 800"
pkill -9 -f "port 8000"
```

### 인증 에러 (401)

1. `INTERNAL_SERVICE_KEY` 환경변수 확인
2. 헤더명 정확히: `X-Internal-Service-Key`
3. Cell-MES `deps.py`에서 서비스 키 체크 로직 확인

### URL 경로 중복 (400)

```
base_url: http://localhost:8000/api/v1  + endpoint: /api/v1/...  → ❌ 중복
base_url: http://localhost:8000         + endpoint: /api/v1/...  → ✅
```

### Pydantic 에러

`config.py`에 `extra="ignore"` 추가:
```python
model_config = SettingsConfigDict(extra="ignore")
```

### SQLite BIGINT 함정

**증상**: `NOT NULL constraint failed: work_orders.id`

**해결**: INSERT 시 id 명시적 지정
```python
max_id = await session.execute(select(func.max(Model.id)))
new_id = (max_id.scalar() or 0) + 1
```

### 스키마 확인

```bash
sqlite3 agents/cell-mes/data/mes.db ".tables"
sqlite3 agents/cell-mes/data/mes.db ".schema work_orders"
```

## Anti-patterns

```python
# ❌ base_url에 /api/v1 포함
MES_API_BASE_URL = "http://localhost:8000/api/v1"
endpoint = "/api/v1/analytics/..."  # 중복!
```

```bash
# ❌ pkill 패턴에 콜론 사용 (매칭 안 됨)
pkill -f "uvicorn.*:8000"
# ✅
pkill -f "port 8000"
```

## 관련 파일

| 파일 | 용도 |
|------|------|
| `services.env` | 포트 중앙 관리 |
| `start-services.sh` / `stop-services.sh` | 서비스 시작/중지 |
| `agents/cell-mes/src/app/api/deps.py` | 인증 처리 |
| `agents/nl-router/src/nl_router_agent.py` | MES API 호출 |
