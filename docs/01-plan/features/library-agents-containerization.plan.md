---
template: plan-plus
feature: library-agents-containerization
date: 2026-05-02
author: xession
project: agents-workspace
phase: plan
---

# library-agents-containerization — Plan-Plus

## Executive Summary

| 관점 | 내용 |
|---|---|
| **Problem** | 6개 라이브러리(gcode-parser, cam-runner, step-pmi-reader, monitoring-data-replayer, cell-schedule-visualizer, torus-mock)가 Python 모듈로만 존재해 Docker Compose에 통합되지 않음. cell-mes/scheduler가 직접 import해야 하므로 의존성 결합·배포 단위 모호. 또한 미래 Agent orchestrator-centric 전환에 대비한 tool-friendly API 패턴이 없음. |
| **Solution** | 6개 라이브러리를 thin FastAPI wrapper로 감싸 독립 컨테이너로 실행. 각각 표준 골격(`/health`, `/docs`, `/api/v1/`, INTERNAL_SERVICE_KEY 인증, 구조화 로깅, pytest, CORS, /capabilities, OpenTelemetry trace_id) 적용. 미래 친화 4가지(API 설계 원칙 문서, service registry yaml, /capabilities endpoint, trace_id 전파) 동시 도입. |
| **Function / UX / Effect** | • 6개 신규 서비스 (port 8010-8015) Docker Compose 통합<br>• 각 서비스: FastAPI + Swagger + INTERNAL_SERVICE_KEY 인증 + pytest<br>• step-pmi-reader는 OCC 의존 (mambaorg/micromamba base, DTP 패턴 재사용)<br>• cell-mes에서 HTTP로 호출 가능 (기존 import 패턴은 점진적 교체)<br>• docs/architecture/api-design-principles.md 신규 (idempotent/Pydantic/error envelope/docstring)<br>• config/internal-services.yaml 신규 (service registry, orchestrator 도입 시 dynamic discovery 기반)<br>• /capabilities endpoint (MCP-style, 6개 모두)<br>• X-Trace-Id 헤더 전파 + 구조화 로깅 통합 |
| **Core Value** | **MES-centric → Orchestrator-centric 아키텍처 전환을 위한 토대 마련.** 본 사이클은 cell-mes 중심을 유지하지만, 6개 신규 서비스가 standalone tool로 격상되어 다음 사이클에 agent-orchestrator가 자연스럽게 흡수 가능. 본 사이클 +2-3일 추가로 미래 사이클 +2-3주 절감. |

## Context Anchor

| Key | Value |
|---|---|
| **WHY** | 라이브러리 → 서비스화로 배포 격리 + 미래 agent-orchestrator-centric 전환 토대 |
| **WHO** | 시스템 운영자 (배포 단위 단순화), 미래 agent orchestrator (tool 호출자), 도메인 개발자 (의존성 격리) |
| **RISK** | step-pmi-reader OCC 빌드 실패 / INTERNAL_SERVICE_KEY 누락 시 전 서비스 401 / cell-mes 기존 import 코드와 동시 운영 시 혼란 |
| **SUCCESS** | 13/13 docker compose Up + 각 서비스 /health 200 + /docs Swagger + pytest L1 PASS + service registry yaml 작성 + API 설계 원칙 문서 + /capabilities 응답 + trace_id 전파 |
| **SCOPE** | 6 신규 컨테이너 + 4 미래 친화 항목. **Out of scope: cell-mes에서 import → HTTP로 적극 마이그레이션, agent-orchestrator 본체, DB 분리, frontend CORS 본격 활성화** |

---

## 1. User Intent Discovery

### Q1. 서비스 분해 의미
선택: **α: 라이브러리 → API 서비스화** (cell-mes 모놀리스 분해 X, 6 라이브러리만)

### Q2. DB 전략
선택: **SQLite 유지** (DB 분리 작업은 본 사이클 OOS)

### Q3. 서비스화 패턴
선택: **A: Thin FastAPI wrapper + Dockerfile**

### Q4a. 컨테이너화할 라이브러리
선택: **6개 모두** (gcode-parser, cam-runner, step-pmi-reader, monitoring-data-replayer, cell-schedule-visualizer, torus-mock)

### Q4b. 표준 기능
선택: **Must 1-3 + Should 4-6 + Nice 7-8** (모두)

### Q5. Agent orchestrator 도입 시점
선택: **E: 별도 PDCA 사이클로 분리** (본 사이클은 컨테이너화만)

### Q6. 미래 친화 항목
선택: **1, 2, 4, 5** (API 설계 원칙 / Service registry / /capabilities / OpenTelemetry trace_id)

## 2. Alternatives Explored

| 분해 패턴 | 선택? |
|---|:-:|
| α: 라이브러리 → API 서비스화 | ✅ |
| β: cell-mes 모놀리스 분해 | ❌ (4-6주 소요) |
| α + β: 풀 마이크로서비스 | ❌ |

| DB 전략 | 선택? |
|---|:-:|
| SQLite 유지 | ✅ |
| PostgreSQL 단독 | ❌ (다음 사이클) |
| PostgreSQL + TimescaleDB | ❌ |
| PostgreSQL + MongoDB | ❌ |

| 서비스화 기술 | 선택? |
|---|:-:|
| A: Thin FastAPI wrapper | ✅ |
| B: 공유 base image | ❌ (deps 충돌) |
| C: gRPC | ❌ (과한 솔루션) |

| Agent orchestrator | 선택? |
|---|:-:|
| A: 이번에 함께 (orchestrator/ 부활) | ❌ |
| B: nl-router 확장 | ❌ |
| C: MCP 기반 | ❌ |
| D: 현재 유지 | ❌ |
| E: 별도 PDCA 사이클 | ✅ |

## 3. YAGNI Review

### 3.1 Included (본 사이클)

#### 6 라이브러리 컨테이너화
1. gcode-parser (port 8010, python:3.11-slim)
2. cam-runner (port 8011, python:3.11-slim)
3. step-pmi-reader (port 8012, mambaorg/micromamba — OCC)
4. monitoring-data-replayer (port 8013, python:3.11-slim)
5. cell-schedule-visualizer (port 8014, python:3.11-slim + matplotlib)
6. torus-mock (port 8015, python:3.11-slim)

#### 표준 기능 (서비스당 동일)
- `/health` (no auth)
- `/docs` (Swagger UI)
- `/api/v1/` 버전 prefix
- INTERNAL_SERVICE_KEY 인증 (X-Internal-Key 헤더)
- 구조화 로깅 (shared/common 활용)
- CORS (frontend 직접 호출 대비)
- pytest L1 회귀
- pre-commit pytest 훅 통합 (cell-mes 패턴 재사용)

#### 미래 친화 (1, 2, 4, 5)
1. **API 설계 원칙 문서** — `docs/architecture/api-design-principles.md`
   - idempotent / Pydantic / 에러 envelope / 풍부한 docstring
2. **Service registry yaml** — `config/internal-services.yaml`
   - 6개 신규 + 기존 cell-mes/nl-router/scheduler/dtp 등록
3. **/capabilities endpoint** — 서비스당 1개
   - MCP-style 도구 설명 노출
4. **OpenTelemetry trace_id** — `shared/common/tracing.py`
   - X-Trace-Id 헤더 in/out + 로깅 자동 inclusion

### 3.2 Out of Scope

- Agent orchestrator 본체 (별도 PDCA 사이클)
- cell-mes에서 import → HTTP 적극 마이그레이션 (이번엔 endpoint만 가동, 점진적 교체)
- DB PostgreSQL 마이그레이션 (별도 사이클)
- Frontend 직접 호출 + CORS 본격 활성화
- API gateway (Kong, Traefik)
- Service mesh (Istio)
- K8s 배포 manifest
- gRPC 전환

## 4. Brainstorming Log

| 단계 | 핵심 결정 |
|---|---|
| Phase 0 | 6 라이브러리 미컨테이너화 / SQLite 단일 DB / orchestrator 디렉토리 dead code |
| Phase 1-Q1 | α 선택 (라이브러리 → API, 모놀리스 분해 X) |
| Phase 1-Q2 | DB 분리 OOS (SQLite 유지) |
| Phase 1-Q3 | A: Thin FastAPI wrapper 선택 |
| Phase 1-Q4 | 6 라이브러리 모두 + 모든 표준 기능 |
| Phase 1-Q5 | Agent orchestrator는 별도 사이클 |
| Phase 1-Q6 | 미래 친화 1+2+4+5 추가 (3은 이미 포함) |
| Phase 2 | A 단일 결정 (Thin FastAPI wrapper) |
| Phase 4 | 13/13 컨테이너 가동 + tool-friendly API 설계 + 점진적 cell-mes 통합 |

## 5. Architecture & Module Map

### 5.1 신규 디렉토리/파일 (~60개)

각 6개 서비스 동일 구조:
```
agents/<lib>/
├── Dockerfile                          # 신규
├── pyproject.toml                      # 수정 (fastapi/uvicorn 추가)
├── src/
│   ├── service.py                      # 신규 — FastAPI app
│   ├── api/v1/
│   │   ├── health.py                   # /health
│   │   ├── capabilities.py             # /capabilities (MCP-style)
│   │   └── endpoints.py                # 도메인 endpoint
│   └── core/
│       ├── auth.py                     # INTERNAL_SERVICE_KEY
│       ├── tracing.py                  # X-Trace-Id 미들웨어 (또는 shared/)
│       └── (기존 라이브러리 코드)
└── tests/
    ├── conftest.py
    └── test_api.py                     # L1
```

공통:
- `docs/architecture/api-design-principles.md` (신규)
- `config/internal-services.yaml` (신규)
- `shared/common/tracing.py` (신규 — OpenTelemetry 호환 trace_id)
- `docker-compose.yml` (수정 — 6 services 추가)
- `.pre-commit-config.yaml` (수정 — pytest 훅을 모든 agents/* 적용)

### 5.2 데이터 흐름

```
Now:
Frontend → cell-mes → [6 신규] (X-Internal-Key)

Future:
Frontend → agent-orchestrator → cell-mes / scheduler / [6 신규]
```

## 6. Implementation Order

```
0단계: 횡단 (shared/common/tracing.py + API 설계 원칙 문서 + service registry skeleton)
1단계: gcode-parser (가장 가벼움)
2단계: cam-runner
3단계: step-pmi-reader (OCC, micromamba — 가장 무거움)
4단계: monitoring-data-replayer
5단계: cell-schedule-visualizer (matplotlib)
6단계: torus-mock
7단계: docker-compose.yml 통합 + service registry yaml 채우기
8단계: 회귀 검증 (13/13 Up + /health 200 × 6 + /docs × 6 + pytest)
```

병렬 실행 전략: 1-6 단계는 file ownership이 격리되어 6개 sub-agent 병렬 가능.

## 7. Success Criteria (Plan Success Criteria)

| # | Criteria | 평가 |
|---|---|---|
| 1 | docker compose ps 13/13 Up | docker compose ps |
| 2 | 각 신규 서비스 /health 200 | curl |
| 3 | 각 신규 서비스 /docs Swagger UI | 브라우저 |
| 4 | 각 신규 서비스 /capabilities 응답 | curl + JSON 검증 |
| 5 | INTERNAL_SERVICE_KEY 누락 시 401 | curl |
| 6 | INTERNAL_SERVICE_KEY 정합 시 200 | curl + X-Internal-Key |
| 7 | X-Trace-Id 헤더 in/out 전파 + 로깅 inclusion | curl + log inspect |
| 8 | 각 서비스 pytest L1 PASS | uv run pytest |
| 9 | docs/architecture/api-design-principles.md 존재 | grep |
| 10 | config/internal-services.yaml 13개 서비스 등록 | yaml load |
| 11 | step-pmi-reader OCC import OK (컨테이너 내부) | docker exec |
| 12 | 기존 7 서비스 회귀 0 (cell-mes/nl-router/scheduler/dtp/n8n/redis/frontend) | docker compose ps + curl /health |

## 8. Risk

| 위험 | 완화 |
|---|---|
| step-pmi-reader OCC 빌드 실패 | DTP의 검증된 micromamba Dockerfile 패턴 재사용 |
| INTERNAL_SERVICE_KEY 누락 | docker-compose `${VAR:-MISSING}` + .env 검증 |
| 6 sub-agent 병렬 실행 시 docker-compose.yml 동시 수정 충돌 | docker-compose.yml은 main thread만 수정 (sub-agent는 자기 파일만) |
| pytest 신규 추가 시 회귀 가능 | 각 sub-agent가 자체 pytest 통과 후 종료 |
| trace_id 미들웨어가 기존 cell-mes 영향 | shared/common/tracing.py는 미들웨어 추가만, 기존 호출 영향 0 |
| matplotlib 시각화는 stateless 보장 어려움 | tmpfile + cleanup 패턴, 또는 SVG inline return |

## 9. Out of Scope (재확인)

- agent-orchestrator 본체 — 별도 PDCA 사이클 (E 결정)
- DB PostgreSQL/TimescaleDB 마이그레이션 — 별도 사이클
- cell-mes의 import → HTTP 마이그레이션 — 점진적, 본 사이클 OOS
- frontend 직접 호출 + CORS 본격 활성화 — 본 사이클은 cell-mes 경유만 보장
- API gateway, service mesh, K8s, gRPC

## 10. Next Step

```
/pdca design library-agents-containerization
또는
auto mode로 즉시 6 sub-agent 병렬 구현 진행
```
