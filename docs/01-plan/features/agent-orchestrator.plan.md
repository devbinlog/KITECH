---
template: plan-plus
feature: agent-orchestrator
date: 2026-05-03
author: xession
project: agents-workspace
phase: plan
---

# agent-orchestrator — Plan-Plus

## Executive Summary

| 관점 | 내용 |
|---|---|
| **Problem** | 시스템이 MES-centric. 다단계 reasoning + tool 호출이 필요한 시나리오(예: "P1 100대 내일까지 가능?")가 cell-mes 단일 endpoint로 불가능. nl-router는 NL 분류·라우팅 수준이고 LangGraph 같은 본격 reasoning 부재. orchestrator/ 디렉토리는 dead code (architect: 호출처 0건). |
| **Solution** | `orchestrator/` → `agents/agent-orchestrator/` 이전 후 FastAPI 서비스화 (port 8020). LangGraph StateGraph + ReAct 패턴. 직전 사이클의 service registry yaml + /capabilities를 활용한 dynamic tool loader. LLM provider 추상화 (Anthropic/OpenAI/Ollama + Mock fallback). nl-router는 NL 파싱 전용으로 단순화 + tool로 노출. |
| **Function / UX / Effect** | • port 8020 FastAPI 서비스 + WebSocket /ws/chat + HTTP /api/v1/chat<br>• LangGraph StateGraph (Reasoning ↔ ToolCall) + SqliteSaver checkpoint<br>• 12 internal services를 자동 tool 등록 (yaml + /capabilities)<br>• LLM_PROVIDER=anthropic\|openai\|ollama (런타임 선택), API key 미설정 시 Mock 자동 fallback<br>• /sessions/{id}/trace endpoint (tool call audit)<br>• X-Trace-Id 전파 (이전 사이클 인프라 재사용)<br>• Frontend /chat WebSocket wire (최소) |
| **Core Value** | **MES-centric → Orchestrator-centric 아키텍처 전환 완성.** 모든 도메인 도구가 LLM 기반 reasoning loop에 의해 자동 호출 가능. 사용자가 자연어 한 줄로 multi-step 작업 (제품 조회 + 스케줄링 + 가시화)을 한 번에 실행. dev 환경은 Mock fallback으로 LLM key 없이도 부팅 가능. |

## Context Anchor

| Key | Value |
|---|---|
| **WHY** | MES-centric 한계 — 다단계 reasoning 부재. orchestrator/ 부활로 자연스러운 진화. |
| **WHO** | 시나리오 운영자, admin (NL로 multi-step 작업), dev (mock 모드로 환경 단순화) |
| **RISK** | LLM API 비용 / 키 관리 / mock 모드 인지 부재 / SqliteSaver 동시성 / nl-router 책임 변경 시 회귀 |
| **SUCCESS** | 13→14 docker compose Up + /health/capabilities/docs 200 + WebSocket 연결 + 12 tool 자동 등록 + mock fallback 작동 + frontend /chat 최소 wire |
| **SCOPE** | agents/agent-orchestrator/ 전체 + docker-compose.yml + .env + frontend /chat 페이지 wire. **Out of scope: 멀티-에이전트 분리, RAG/vector DB, tool marketplace, 비용 추적, frontend /chat 본격 UI** |

---

## 1. User Intent Discovery

### Q1. nl-router와 책임 분담
선택: **B: nl-router는 파싱 전용, orchestrator가 reasoning**

### Q2. Tool 등록 전략
선택: **Dynamic from yaml + /capabilities**

### Q3. Frontend /chat 연결
선택: **WebSocket streaming**

### Q4. 구현 접근
선택: **A: orchestrator/ 부활 + LangGraph**

### Q5. 포함 기능
선택: **Must 1-6 + Should 7-10 + Nice 11**
- Should 7-8: 대화 state 영속화 + LangGraph checkpoint
- Should 9-10: HTTP fallback + token streaming
- Nice 11: tool result inspection (/sessions/{id}/trace)

### Q6. LLM provider
선택: **셋 다 지원** (Anthropic + OpenAI + Ollama)

### Q7. LLM 의존성 정책
선택: **B: Mock provider 자동 fallback**

## 2. Alternatives Explored

| 책임 분담 | 선택? |
|---|:-:|
| B: nl-router 파싱 / orchestrator reasoning | ✅ |
| A: orchestrator → nl-router를 tool | ❌ |
| C: 병렬 (frontend가 선택) | ❌ |
| D: nl-router 흡수 | ❌ |

| Tool 등록 | 선택? |
|---|:-:|
| Dynamic yaml + /capabilities | ✅ |
| Static hardcode | ❌ |
| MCP 기반 | ❌ |
| Hybrid | ❌ |

| 구현 접근 | 선택? |
|---|:-:|
| A: orchestrator/ 부활 + LangGraph | ✅ |
| B: Greenfield rewrite | ❌ |
| C: AgentSDK / AutoGen | ❌ |
| D: Custom mini-orchestrator | ❌ |

| LLM 정책 | 선택? |
|---|:-:|
| B: Mock fallback | ✅ |
| B+C: Mock + Ollama 우선 | ❌ |
| A: 엄격 | ❌ |

## 3. YAGNI Review

### 3.1 Included

#### Must
1. FastAPI service (port 8020, shared.common.service_base.create_app)
2. WebSocket /ws/chat (frontend 연결, 실시간 streaming)
3. HTTP /api/v1/chat (fallback)
4. LangGraph StateGraph (ReAct: Reasoning ↔ ToolCall)
5. LLM provider 추상화 (Anthropic / OpenAI / Ollama / Mock)
6. /capabilities + /health (다른 서비스 패턴과 일관)

#### Should
7. Conversation state persistence (SqliteSaver, /app/agents/agent-orchestrator/data/conversations.db)
8. LangGraph checkpoint (자동 — SqliteSaver가 매 step 저장)
9. HTTP /chat endpoint (WebSocket 못 쓰는 환경)
10. Token-level streaming (LLM이 토큰 단위로 stream — WebSocket 채팅 UX)
11. /api/v1/sessions/{id}/trace — tool call audit

#### Plus (LLM 정책 B)
- Mock LLM provider — API key 누락 시 자동 fallback
- /health에 llm_status (active/mock/local) 노출

### 3.2 Out of Scope

- 멀티-에이전트 (planner/executor/critic 분리) — 다음 사이클
- Vector DB / RAG
- Tool marketplace / plugin system
- Nice 12-15: admin UI / 비용 추적 / 다중 모델 fallback / tool budget
- frontend /chat UI 본격 구현 (최소 wire만)
- nl-router 본격 단순화 (이번엔 tool 등록만 + 필요시 이주)

## 4. Brainstorming Log

| Phase | 결정 |
|---|---|
| Phase 0 | orchestrator/ dead code, shared/common 인프라 준비, service registry yaml + /capabilities 활용 가능 |
| Phase 1 Q1 | B — 책임 명확 분리 |
| Phase 1 Q2 | Dynamic yaml + /capabilities (이전 사이클 인프라 활용) |
| Phase 1 Q3 | WebSocket streaming |
| Phase 2 | A — orchestrator/ 재활용 |
| Phase 3 | Must + Should + Nice 11 |
| Phase 1 Q6 | 3 provider 모두 |
| Phase 1 Q7 | B — Mock fallback |
| Phase 4 | Section 1 (architecture) + 2 (components) + 3 (flow) 모두 OK |

## 5. Architecture & Module Map

### 5.1 디렉토리 구조

```
agents/agent-orchestrator/         # orchestrator/ 에서 이전 + 확장
├── Dockerfile                     # 신규 python:3.11-slim
├── pyproject.toml                 # 신규
├── data/                          # gitignored — SqliteSaver
├── src/
│   ├── service.py                 # FastAPI app (create_app)
│   ├── api/v1/
│   │   ├── chat.py                # /chat (HTTP) + /ws/chat (WebSocket)
│   │   └── sessions.py            # /sessions/{id}/trace
│   ├── core/
│   │   ├── llm_provider.py        # Anthropic / OpenAI / Ollama / Mock
│   │   ├── tool_loader.py         # yaml + /capabilities → BaseTool
│   │   ├── checkpoint.py          # SqliteSaver wrapper
│   │   └── streaming.py           # WebSocket helpers
│   ├── graph/
│   │   ├── state.py               # AgentState TypedDict
│   │   ├── nodes.py               # Reasoning / ToolCall / Inspect
│   │   └── builder.py             # build_agent_graph()
│   ├── workflows/                 # 기존 orchestrator/src/workflows.py 이전
│   └── converters/                # 기존 cam_to_scheduler.py 이전
└── tests/
    ├── conftest.py
    ├── test_service.py
    ├── test_llm_provider.py
    ├── test_tool_loader.py
    └── test_graph.py
```

### 5.2 환경변수

```
LLM_PROVIDER=anthropic|openai|ollama   # default 없음 — unset이면 mock
ANTHROPIC_API_KEY=...
OPENAI_API_KEY=...
OLLAMA_BASE_URL=http://host.docker.internal:11434
LLM_MODEL=claude-3-5-sonnet-20241022   # provider별 default 자동
LLM_TEMPERATURE=0.1
ORCHESTRATOR_DB_PATH=/app/agents/agent-orchestrator/data/conversations.db
ORCHESTRATOR_PORT=8020
SERVICE_REGISTRY_PATH=/app/config/internal-services.yaml
INTERNAL_SERVICE_KEY=${INTERNAL_SERVICE_KEY}
```

### 5.3 데이터 흐름 (Section 3에서 그림)

WebSocket /ws/chat → AgentState (with checkpoint) → ReAct loop (LLM ↔ tool) → 12개 internal services → 답변 streaming

## 6. Implementation Order

```
1. orchestrator/ → agents/agent-orchestrator/ git mv
2. pyproject.toml + Dockerfile 신규
3. core/llm_provider.py (Anthropic/OpenAI/Ollama/Mock)
4. core/tool_loader.py (yaml + /capabilities → BaseTool)
5. graph/{state,nodes,builder}.py (LangGraph StateGraph)
6. core/checkpoint.py (SqliteSaver)
7. api/v1/{chat,sessions}.py (HTTP + WebSocket)
8. src/service.py (create_app + 등록)
9. tests/ (mock LLM 기반 L1)
10. docker-compose.yml + .env
11. config/internal-services.yaml에 agent-orchestrator 자기 자신 추가
12. frontend /chat 최소 wire (선택)
13. 회귀 검증 (14/14 Up + /health 200 + tool 자동 등록 검증)
```

## 7. Success Criteria

| # | Criteria |
|---|---|
| 1 | docker compose ps 14/14 Up |
| 2 | /health 200 + llm_status 표시 |
| 3 | /capabilities 200 + tool list 노출 |
| 4 | /docs Swagger UI 200 |
| 5 | /api/v1/chat HTTP 200 (mock LLM 응답) |
| 6 | /ws/chat WebSocket 연결 + ping/pong |
| 7 | /sessions/{id}/trace 응답 |
| 8 | API key unset → mock provider 자동 fallback (부팅 성공) |
| 9 | API key set → 실제 LLM 호출 동작 |
| 10 | 12 internal services tool 자동 등록 (yaml + /capabilities) |
| 11 | pytest 모든 단계 PASS (mock LLM) |
| 12 | 기존 13 서비스 회귀 0 |
| 13 | conversation state SqliteSaver에 저장 + 복원 |

## 8. Risk

| 위험 | 완화 |
|---|---|
| LangGraph 버전 호환성 | langgraph 0.2.x + langchain 0.3.x 명시 (pyproject.toml lock) |
| LLM API 비용 | mock 모드 default + 명시적 API key 설정 시만 호출 |
| SqliteSaver 동시 쓰기 | session별 thread_id 격리 + WAL mode |
| tool /capabilities 응답 변경 | best-effort load + 실패 시 skip + log |
| nl-router 영향 | 본 사이클은 단순 tool 등록만 (nl-router 코드 변경 X) |
| frontend /chat 영향 | 최소 wire 또는 OOS — 기존 page.tsx 보존 |

## 9. Out of Scope (재확인)

- 멀티-에이전트 (planner/executor 분리)
- Vector DB / RAG
- Tool marketplace
- Nice 12-15 (admin UI, 비용 추적, fallback chain, budget)
- frontend /chat 본격 UI
- nl-router 코드 단순화 (이주)
- DB PostgreSQL 마이그레이션

## 10. 기존 Frontend UI ↔ Orchestrator 공존 모델 (사용자 명시 요청)

본 사이클은 **두 경로 공존** 설계:

| 사용자 액션이 명확함 | 사용자 의도가 자연어/모호함 |
|---|---|
| 기존 페이지 (`/master`, `/production`, `/quality`, `/analytics`, `/scheduler`, `/scenarios`) | `/chat` (신규 — orchestrator) |
| Frontend → cell-mes 직접 HTTP | Frontend → orchestrator WebSocket → tool 호출 |
| 빠르고 결정적 (CRUD, 차트, 리스트) | LLM 추론 + 다단계 tool calling |
| **변경 없음** | 신규 영역 |

### 본 사이클이 건드리지 않는 것 (회귀 위험 0)

- `app/(main)/master/*` 페이지 (제품/공정/라우팅/시나리오/설비)
- `app/(main)/production/*` 페이지 (작업지시/실적)
- `app/(main)/quality/*` 페이지 (검사/SPC/NCR)
- `app/(main)/analytics/*` 페이지
- `app/(main)/scheduler/*` 페이지
- `Sidebar.tsx` (이전 사이클의 n8n 외부 링크 포함, 그대로)
- cell-mes / nl-router / scheduler / dtp / 6 라이브러리 백엔드 코드

### 본 사이클이 변경하는 frontend (최소)

- `app/(main)/chat/page.tsx` — WebSocket 연결 추가 (orchestrator:8020/ws/chat)
- 메시지 input + assistant 응답 표시 (가장 단순한 chat UI)
- 본격 UI/UX는 다음 사이클 OOS

### 사용자 관점의 효과

- 기존 UI 사용자: 영향 0 (모든 페이지 그대로)
- 신규 chat 사용자: "P1 100대 내일까지 가능해?" 같은 질의를 자연어로 던지면 orchestrator가 cell-mes/scheduler를 자동 호출해 답변 생성
- 두 경로가 서로 보완 — 정확한 액션은 기존 UI가 효율적, 탐색적/모호한 의도는 chat이 적합
