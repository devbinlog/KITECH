# NL Router Agent

자연어 쿼리를 분석하여 적절한 MES API로 라우팅하는 에이전트

## Quick Start

```bash
cd agents/nl-router
uv sync

# 서버 시작
uvicorn src.app.main:app --port 8001
```

## Usage

```python
from src.nl_router_agent import NLRouterAgent

agent = NLRouterAgent(config={"mes_base_url": "http://localhost:8000"})
result = agent.process("오늘 생산 현황 보여줘")

print(result["intent"])    # 분류된 의도
print(result["entities"])  # 추출된 엔티티
print(result["response"])  # API 응답
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/nlm/query | 자연어 쿼리 처리 |
| GET | /api/v1/nlm/skills | 등록된 스킬 목록 |
| WS | /ws/{client_id} | WebSocket 연결 |

## Supported Intents

| Intent | Example Query |
|--------|---------------|
| PRODUCTION_STATUS | "오늘 생산 현황" |
| EQUIPMENT_STATUS | "CNC 장비 상태" |
| SCHEDULE_QUERY | "내일 스케줄 조회" |
| KPI_QUERY | "이번 주 가동률" |
| TRACEABILITY | "LOT-001 이력 추적" |
| ERROR_DIAGNOSIS | "알람 현황" |

## Architecture

```
Query → IntentClassifier → EntityExtractor → SkillRegistry → APISelector → MES API
```

## Components

| Component | Description |
|-----------|-------------|
| IntentClassifier | 의도 분류 (규칙 + LLM) |
| EntityExtractor | 엔티티 추출 (날짜, 장비ID 등) |
| SkillRegistry | 스킬 매핑 |
| APISelector | API 호출 계획 생성 |

## Environment Variables

```bash
MES_BASE_URL=http://localhost:8000
OPENAI_API_KEY=sk-xxx  # Optional, for LLM
```

## Testing

```bash
uv run pytest tests/ -v
uv run pytest tests/ --cov=src
```
