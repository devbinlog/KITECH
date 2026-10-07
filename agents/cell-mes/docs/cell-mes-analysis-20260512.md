# Cell-MES 소스코드 전체 분석 문서

> 작성일: 2026-05-12  
> 분석 대상: `agents/cell-mes/`

---

## 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [디렉토리 구조](#2-디렉토리-구조)
3. [백엔드 — 기술 스택 및 설정](#3-백엔드--기술-스택-및-설정)
4. [API 엔드포인트 전체 목록](#4-api-엔드포인트-전체-목록)
5. [데이터베이스 스키마](#5-데이터베이스-스키마)
6. [핵심 서비스 상세](#6-핵심-서비스-상세)
7. [NLM — AI 자연어 어시스턴트](#7-nlm--ai-자연어-어시스턴트)
8. [설비 연동 — AAS 미들웨어](#8-설비-연동--aas-미들웨어)
9. [인증 및 인가](#9-인증-및-인가)
10. [프론트엔드 — 기술 스택 및 페이지 구조](#10-프론트엔드--기술-스택-및-페이지-구조)
11. [프론트엔드 — 컴포넌트 목록](#11-프론트엔드--컴포넌트-목록)
12. [프론트엔드 — 상태 관리](#12-프론트엔드--상태-관리)
13. [Alembic 마이그레이션 이력](#13-alembic-마이그레이션-이력)
14. [Docker 및 배포](#14-docker-및-배포)
15. [테스트 구성](#15-테스트-구성)
16. [환경 변수 전체 목록](#16-환경-변수-전체-목록)

---

## 1. 프로젝트 개요

**Cell-MES**는 스마트 팩토리용 **제조 실행 시스템(Manufacturing Execution System)** 이다.

- **아키텍처**: FastAPI 백엔드 + Next.js 프론트엔드 풀스택
- **DB**: 개발 환경 SQLite, 운영 환경 PostgreSQL (asyncio 지원)
- **설비 연동**: AAS(Asset Administration Shell) 기반 미들웨어와 HTTP 폴링
- **AI 기능**: 경량 NLM(Natural Language MES) — 자연어로 생산 데이터 조회
- **생산 방식**: Lot-Size 1 아키텍처 — 작업지시를 Unit 단위로 순차 처리
- **시나리오 관리**: n8n 워크플로우 YAML ↔ JSON 양방향 변환

---

## 2. 디렉토리 구조

```
agents/cell-mes/
├── src/
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py                  # 의존성 주입 (DB세션, 사용자 인증)
│   │   │   └── v1/
│   │   │       ├── api.py               # 전체 라우터 등록
│   │   │       └── endpoints/           # 19개 엔드포인트 모듈
│   │   ├── core/
│   │   │   ├── config.py                # 환경변수 기반 설정 (Pydantic Settings)
│   │   │   └── security.py             # JWT 생성/검증, bcrypt
│   │   ├── db/
│   │   │   ├── base.py                  # SQLAlchemy Base
│   │   │   └── session.py              # AsyncSessionLocal, 엔진 설정
│   │   ├── models/
│   │   │   ├── master.py               # ProcessCategory, Cell, StdProcess, Product, ProcessRouting, Scenario
│   │   │   ├── equipment.py            # Equipment, EqLog, EquipmentStatusHistory
│   │   │   ├── production.py           # WorkOrder, Unit, ProdResult
│   │   │   ├── quality.py              # InspectionPlan, InspectionResult, SPCChart, SPCDataPoint, NonConformance, MeasurementDevice
│   │   │   └── user.py                 # User
│   │   ├── schemas/                    # Pydantic 요청/응답 스키마
│   │   └── services/
│   │       ├── aggregation_service.py  # KPI/분석 집계 로직
│   │       ├── cache_service.py        # 캐시 서비스
│   │       ├── circuit_breaker.py      # 서킷 브레이커 패턴
│   │       ├── dispatch_service.py     # Lot-Size 1 디스패치 데몬
│   │       ├── event_publisher.py      # 이벤트 발행 (향후 메시지 큐 연동)
│   │       ├── n8n_runner.py           # n8n 시나리오 실행
│   │       ├── polling_service.py      # 설비 상태 폴링
│   │       ├── quality_service.py      # 품질 관리 로직
│   │       ├── scenario_actions_catalog.py  # n8n 노드 액션 카탈로그
│   │       ├── scenario_converter.py   # n8n YAML ↔ JSON 변환
│   │       ├── scheduler_integration.py     # 외부 스케줄러 연동
│   │       ├── sync_service.py         # AAS 설비 동기화
│   │       ├── nlm_retriever/          # NLM 검색 엔진
│   │       │   ├── base.py
│   │       │   ├── cross_encoder_ranker.py
│   │       │   ├── embedding_retriever.py
│   │       │   ├── examples.py
│   │       │   ├── hybrid_retriever.py
│   │       │   ├── keyword_retriever.py
│   │       │   └── pipeline.py
│   │       └── scheduling/             # 스케줄링 관련 서비스
│   │           ├── http_client.py
│   │           ├── lock.py
│   │           ├── projector.py
│   │           └── result_applier.py
│   ├── clients/
│   │   └── middleware_client.py        # 미들웨어 HTTP 클라이언트 (싱글턴)
│   ├── parsers/                        # 설비 데이터 파서 (CNC, Robot, PLC)
│   ├── protocols/                      # 프로토콜 정의
│   └── seed_data.py                    # 초기 데이터 시딩
├── frontend/
│   ├── app/                            # Next.js App Router
│   ├── components/                     # 55개+ 리액트 컴포넌트
│   ├── stores/                         # Zustand 스토어
│   ├── types/                          # TypeScript 타입 정의
│   └── services/                       # API 클라이언트
├── alembic/
│   └── versions/                       # 6개 마이그레이션 버전
├── tests/                              # 530개 pytest 테스트
├── docs/                               # 설계 명세서
├── .env.example                        # 환경변수 템플릿
├── Dockerfile                          # Docker 빌드 설정
├── alembic.ini                         # Alembic 설정
└── pyproject.toml                      # Python 프로젝트 설정
```

---

## 3. 백엔드 — 기술 스택 및 설정

### 의존성 (`pyproject.toml`)

| 분류 | 패키지 | 버전 |
|------|--------|------|
| **웹 프레임워크** | fastapi | ≥0.109.0 |
| **ASGI 서버** | uvicorn[standard] | ≥0.27.0 |
| **ORM** | sqlalchemy[asyncio] | ≥2.0.0 |
| **PostgreSQL 드라이버** | asyncpg | ≥0.29.0 |
| **SQLite 드라이버** | aiosqlite | ≥0.22.1 |
| **마이그레이션** | alembic | ≥1.13.0 |
| **HTTP 클라이언트** | httpx | ≥0.26.0 |
| **JWT** | python-jose[cryptography] | ≥3.3.0 |
| **비밀번호 해싱** | passlib[bcrypt] | ≥1.7.0 |
| **데이터 검증** | pydantic | ≥2.5.0 |
| **설정 관리** | pydantic-settings | ≥2.1.0 |
| **YAML 처리** | pyyaml | ≥6.0.0 |
| **AI 임베딩** | sentence-transformers | ≥5.2.2 |
| **키워드 랭킹** | rank-bm25 | ≥0.2.2 |

### 애플리케이션 시작 (`src/app/main.py`)

FastAPI lifespan 이벤트에서 두 개의 백그라운드 태스크를 시작한다.

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    polling_task = asyncio.create_task(_background_polling_loop())  # 설비 상태 폴링 (3초 간격)
    dispatch_task = asyncio.create_task(run_dispatch_loop())        # Lot-Size 1 디스패치 (2초 간격)
    yield
    polling_task.cancel()
    dispatch_task.cancel()
```

**주요 설정**:
- Swagger UI: `/api/docs`
- ReDoc: `/api/redoc`
- OpenAPI JSON: `/api/v1/openapi.json`
- Health Check: `GET /health`
- 에이전트용 도구 목록: `GET /capabilities`
- 업로드 파일 정적 서빙: `/uploads/`

### 설정 클래스 (`src/app/core/config.py`)

`pydantic-settings`의 `BaseSettings` 상속. `.env` 파일 자동 로드.

```python
class Settings(BaseSettings):
    ENV: str = "development"
    APP_NAME: str = "Cell-MES"
    APP_VERSION: str = "0.1.0"
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/mes.db"  # 기본: SQLite
    SECRET_KEY: str = "..."
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440   # 24시간
    MIDDLEWARE_URL: str = "http://10.10.10.113:8100"
    EQUIPMENT_POLL_INTERVAL_SEC: int = 3
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"
    INTERNAL_SERVICE_KEY: str = "..."         # 내부 서비스 인증용
    SCHEDULER_DEFAULT_SOLVER: str = "OR_TOOLS"
    SCHEDULER_DEFAULT_HORIZON_HOURS: int = 24
```

---

## 4. API 엔드포인트 전체 목록

모든 API는 `/api/v1/` 프리픽스를 사용한다.

### 인증 (`/auth`)

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| POST | `/auth/login` | 로그인, JWT 토큰 발급 | 없음 |
| POST | `/auth/register` | 회원가입 | 없음 |
| GET | `/auth/me` | 현재 사용자 조회 | 인증 |

### 마스터 데이터 (`/masters`)

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| GET | `/masters/products` | 품목 목록 | 인증 |
| POST | `/masters/products` | 품목 생성 | ADMIN |
| PUT | `/masters/products/{id}` | 품목 수정 | ADMIN |
| DELETE | `/masters/products/{id}` | 품목 삭제 | ADMIN |
| GET | `/masters/std-processes` | 표준공정 목록 | 인증 |
| POST | `/masters/std-processes` | 표준공정 생성 | ADMIN |

### 설비 (`/masters/equipments`)

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| GET | `/masters/equipments` | 설비 목록 | 인증 |
| POST | `/masters/equipments` | 설비 수동 등록 | ADMIN |
| POST | `/masters/equipments/sync` | **AAS 미들웨어 동기화** | ADMIN |
| GET | `/masters/equipments/middleware-health` | 미들웨어 헬스체크 | 인증 |
| GET | `/masters/equipments/{id}` | 설비 단건 조회 | 인증 |
| DELETE | `/masters/equipments/{id}` | 설비 삭제 (소프트) | ADMIN |
| GET | `/masters/equipments/{id}/status` | 설비 현재 상태 | 인증 |
| GET | `/masters/equipments/{id}/status-history` | 상태 변경 이력 | 인증 |
| POST | `/masters/equipments/{id}/status-history` | 상태 변경 기록 | 인증 |
| GET | `/masters/equipments/{id}/status-summary` | 상태별 시간 요약 (OEE) | 인증 |

### 공정 라우팅 (`/masters/products`)

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| GET | `/masters/products/{id}/routings` | 라우팅 목록 | 인증 |
| POST | `/masters/products/{id}/routings` | 라우팅 생성 | ADMIN |
| PUT | `/masters/products/{id}/routings/{rid}` | 라우팅 수정 | ADMIN |
| DELETE | `/masters/products/{id}/routings/{rid}` | 라우팅 삭제 | ADMIN |
| POST | `/masters/products/{id}/routings/{rid}/files` | 파일 업로드 (NC/IMG/DOC) | ADMIN |

### 시나리오 (`/masters/scenarios`)

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| GET | `/masters/scenarios` | 시나리오 목록 | 인증 |
| POST | `/masters/scenarios` | 시나리오 생성 | ADMIN |
| GET | `/masters/scenarios/{id}` | 시나리오 단건 조회 | 인증 |
| PUT | `/masters/scenarios/{id}` | 시나리오 수정 | ADMIN |
| DELETE | `/masters/scenarios/{id}` | 시나리오 삭제 | ADMIN |
| GET | `/masters/scenarios/{id}/n8n` | YAML → n8n JSON 변환 | 인증 |
| PUT | `/masters/scenarios/{id}/n8n` | n8n JSON → YAML 저장 | ADMIN |

### n8n 변환기 (`/converters`)

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| POST | `/converters/yaml-to-n8n` | YAML → n8n JSON | 인증 |
| POST | `/converters/n8n-to-yaml` | n8n JSON → YAML | 인증 |

### 생산 (`/production`)

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| GET | `/production/orders` | 작업지시 목록 | 인증 |
| POST | `/production/orders` | 작업지시 생성 | 인증 |
| GET | `/production/orders/{id}` | 작업지시 단건 | 인증 |
| PATCH | `/production/orders/{id}/status` | 상태 변경 | 인증 |
| GET | `/production/results` | 생산 실적 목록 | 인증 |
| POST | `/production/results` | 생산 실적 등록 | 인증 |

### 스케줄러 (`/scheduler`)

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| GET | `/scheduler/schedule` | 스케줄 조회 | 인증 |
| POST | `/scheduler/request` | 스케줄링 요청 | 인증 |
| GET | `/scheduler/equipment-availability` | 설비 가용성 조회 | 인증 |

### 분석 (`/analytics`)

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| GET | `/analytics/dashboard` | KPI 대시보드 | 인증 |
| GET | `/analytics/equipment-utilization` | 설비 이용률 | 인증 |
| GET | `/analytics/lot-traceability/{lot_no}` | 로트 추적 | 인증 |
| GET | `/analytics/daily-status` | 일일 생산 현황 | 인증 |

### NLM AI 어시스턴트 (`/nlm`)

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| POST | `/nlm/query` | 자연어 쿼리 처리 | 인증 |
| GET | `/nlm/history` | 쿼리 이력 | 인증 |
| GET | `/nlm/favorites` | 즐겨찾기 목록 | 인증 |
| POST | `/nlm/favorites` | 즐겨찾기 추가 | 인증 |
| DELETE | `/nlm/favorites` | 즐겨찾기 삭제 | 인증 |
| GET | `/nlm/quota` | 사용량 조회 | 인증 |

### 품질 관리

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| GET | `/inspection-plans` | 검사 계획 목록 | 인증 |
| POST | `/inspection-plans` | 검사 계획 생성 | ADMIN |
| GET | `/inspection-results` | 검사 결과 목록 | 인증 |
| POST | `/inspection-results` | 검사 결과 등록 | 인증 |
| GET | `/ncr` | NCR 목록 | 인증 |
| POST | `/ncr` | NCR 생성 | 인증 |
| PATCH | `/ncr/{id}` | NCR 상태 변경 | 인증 |

### 다운타임 (`/downtime`)

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| GET | `/downtime` | 다운타임 목록 | 인증 |
| POST | `/downtime` | 다운타임 기록 | 인증 |

### 알람 (`/alarms`)

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| GET | `/alarms` | 알람 목록 | 인증 |
| PATCH | `/alarms/{id}/acknowledge` | 알람 확인 처리 | 인증 |

### 셀/공정 분류

| Method | Path | 설명 | 권한 |
|--------|------|------|------|
| GET | `/masters/cells` | 셀 목록 | 인증 |
| POST | `/masters/cells` | 셀 생성 | ADMIN |
| GET | `/masters/process-categories` | 공정 분류 목록 | 인증 |
| POST | `/masters/process-categories` | 공정 분류 생성 | ADMIN |

---

## 5. 데이터베이스 스키마

### 마스터 데이터 (`models/master.py`)

```
process_categories
  id, code(UK), name, created_at

cells
  id, code(UK), name, location, created_at

std_processes
  id, code(UK), name, description
  category_id(FK→process_categories)
  equipment_type          -- "CNC", "ROBOT", "PLC" 등 설비 유형 매핑
  cycle_time_sec(default=60)
  setup_time_sec(default=0)

products
  id, code(UK), name, unit(default="EA"), is_deleted, created_at

process_routings
  id, product_id(FK→products CASCADE), std_process_id(FK→std_processes)
  sequence, revision(default="A"), remarks, created_at
  UK(product_id, sequence, revision)

process_routing_files
  id, process_routing_id(FK CASCADE)
  file_type("NC"/"IMAGE"/"DOC"), file_path, sort_order, created_at

scenarios
  id, code(UK), product_id(FK→products)
  name, file_path, is_active, created_at
```

### 설비 (`models/equipment.py`)

```
equipments
  id, eq_code(UK), aas_id(UK)    -- aas_id: 미들웨어의 AAS 식별자
  eq_name, model_name
  equipment_type                  -- "CNC" / "ROBOT" / "AMR" / "PLC"
  location, cell_id(FK→cells)
  connection_config(JSON)         -- {"ip": "...", "port": 502, "protocol": "modbus"}
  spec_data(JSON)                 -- {"manufacturer": "Doosan", "max_rpm": 20000}
  last_data(JSON)                 -- 실시간 센서 데이터 (미들웨어 AAS submodels 원본)
  current_status                  -- "RUN" / "IDLE" / "STOP" / "ERROR"
  updated_at, last_connected_at, is_deleted

  is_connected: property          -- last_connected_at 기준 30초 내이면 True

eq_logs
  id, equipment_id(FK→equipments)
  level("INFO"/"WARN"/"ERROR"), message, occurred_at

equipment_status_history
  id, equipment_id(FK→equipments)
  previous_status, new_status     -- "RUN"/"IDLE"/"STOP"/"SETUP"/"ERROR"/"MAINTENANCE"
  changed_at, previous_duration_minutes
  reason, work_order_id(FK→work_orders), changed_by
```

### 생산 (`models/production.py`)

```
work_orders
  id, lot_no(UK)
  product_id(FK→products), scenario_id(FK→scenarios)
  target_qty, qty, priority(default=5), due_date
  completed_qty, current_process
  start_time, end_time
  status                          -- READY / SCHEDULED / RUNNING / PAUSE / ERROR / DONE / CANCEL
  created_at

  VALID_TRANSITIONS = {
    "READY":     ["SCHEDULED", "RUNNING", "CANCEL"],
    "SCHEDULED": ["RUNNING", "CANCEL"],
    "RUNNING":   ["PAUSE", "DONE", "ERROR", "CANCEL"],
    "PAUSE":     ["RUNNING", "DONE", "CANCEL"],
    "ERROR":     ["RUNNING", "DONE"],
    "DONE":      [],
    "CANCEL":    [],
  }

units                             -- Lot-Size 1 큐 토큰
  id, work_order_id(FK→work_orders)
  unit_no, scenario_id(FK→scenarios)
  status                          -- READY / RUNNING / DONE / ERROR
  created_at, started_at, completed_at

prod_results
  id, work_order_id(FK→work_orders), unit_id(FK→units)
  process_routing_id(FK→process_routings)
  equipment_id(FK→equipments)
  target_equipment_id(FK→equipments)   -- 스케줄러가 배정한 설비
  ok_qty, ng_qty
  start_time, end_time

  yield_rate: property            -- ok_qty / total_qty * 100
```

### 품질 (`models/quality.py`)

```
inspection_plans
  id, product_id(FK→products), operation_id(FK→process_routings)
  pmi_source, feature_id         -- Digital Thread / PMI 연계
  characteristic, nominal, usl, lsl, unit
  inspection_type                -- INCOMING / IN_PROCESS / FINAL / PERIODIC
  sampling_plan                  -- FIRST_ARTICLE / PERIODIC / 100%
  frequency, enable_spc
  spc_control_type               -- X_BAR_R / X_BAR_S / P_CHART / C_CHART
  is_active

inspection_results
  id, inspection_plan_id(FK), work_order_id(FK), equipment_id(FK)
  lot_no, serial_no, nc_program_id
  source                         -- OMM / EQUATOR / CMM / MANUAL
  device_id(FK→measurement_devices)
  measured_value, deviation, is_conforming
  measurement_metadata(JSON)

spc_charts
  id, inspection_plan_id(FK)
  center_line, upper_control_limit, lower_control_limit
  upper_warning_limit, lower_warning_limit
  range_center_line, range_upper_control_limit, range_lower_control_limit
  sample_count, last_calculation_date, chart_type, revision, is_active

spc_data_points
  id, spc_chart_id(FK)
  subgroup_number, mean_value, range_value, standard_deviation
  sample_size, raw_values(JSON)
  is_out_of_control, violation_rules(JSON)  -- Western Electric Rules
  work_order_id, lot_number

non_conformances
  id, ncr_no(UK)                 -- "NCR-2026-0001"
  work_order_id(FK), lot_no, serial_no, machine_id(FK), inspection_result_id(FK)
  defect_type                    -- DIMENSION / SURFACE / MATERIAL
  characteristic, specified_value, actual_value
  disposition                    -- REWORK / SCRAP / USE_AS_IS / RETURN
  status                         -- OPEN / IN_PROGRESS / CLOSED / VERIFIED / CANCELLED
  description, root_cause, corrective_action
  reported_by, assigned_to
  is_auto_generated              -- SPC 위반 자동 생성 여부
  trigger_data(JSON)

measurement_devices
  id, name, source_type          -- OMM / EQUATOR / CMM / MANUAL
  machine_id(FK→equipments), serial_number, calibration_due
  connection_config(JSON)        -- {"connection_type": "FILE", "path": "...", "format": "csv"}
  is_active
```

### 사용자 (`models/user.py`)

```
users
  id, username(UK), password_hash
  role                            -- "ADMIN" / "OPERATOR" / "SERVICE"
  created_at
```

---

## 6. 핵심 서비스 상세

### 6.1 Dispatch Service — Lot-Size 1 아키텍처 (`services/dispatch_service.py`)

작업지시(WorkOrder)를 개별 Unit으로 분할하여 미들웨어가 소비할 수 있도록 큐에 1개씩 공급하는 데몬.

**동작 원리**:
```
while True (2초 간격):
  RUNNING 상태 WorkOrder 전체 조회
    ↓
  각 WorkOrder에 대해:
    총 생성된 Unit 수 >= target_qty → skip
    현재 READY Unit 수 == 0 → 새 Unit 1개 INSERT
```

**특징**:
- 단일 작업지시에 항상 READY Unit이 최대 1개만 존재하도록 제어
- 미들웨어가 Unit을 처리하면 다음 Unit이 공급됨 → 순차 처리 보장
- 중간에 scenario_id 변경이 가능 (대기 중인 Unit에 반영됨)

### 6.2 Polling Service — AAS 설비 상태 폴링 (`services/polling_service.py`)

3초 간격으로 미들웨어 `/api/aas/view`를 호출하여 전체 설비 상태를 일괄 갱신.

**상태 결정 로직**:
```python
if not is_connected:               → "STOP"
elif robot.status in ("IDLE",):    → "IDLE"
elif robot.status in ("BUSY", ...):→ "RUN"
elif cnc.doorState == "open":      → "RUN"
else:                              → "IDLE"
```

**데이터 보호**:
- `_deep_merge()`: 미들웨어가 일시적으로 빈 데이터를 반환해도 기존 데이터 유지
- 완전히 빈 응답은 skip — 깜빡임(flicker) 방지

### 6.3 Sync Service — AAS 설비 동기화 (`services/sync_service.py`)

`POST /masters/equipments/sync` 에서 호출. AAS에서 장비를 발견하여 MES DB와 동기화.

| 상황 | 처리 |
|------|------|
| 미들웨어에 있고 DB에 없음 | INSERT (create) |
| 미들웨어에 있고 DB에 있음 | UPDATE eq_name, type, last_connected_at |
| DB에 있고 미들웨어에 없음 + delete_orphans=True | is_deleted=True (소프트 삭제) |

**설비 타입 자동 분류**:
- `submodels.cncGateway` 있음 → `"CNC"`
- `submodels.robotGateway` 있음 → `"ROBOT"`
- `submodels.localGateway` 있음 → `"PLC"`
- 기타 → `"CNC"` (기본값)

**오류 격리**: asset 하나 처리 실패 시 해당 asset만 오류 기록, 나머지 계속 처리 (savepoint).

### 6.4 Scenario Converter (`services/scenario_converter.py`)

n8n 워크플로우 JSON과 내부 YAML 시나리오 간 양방향 변환.

**YAML → n8n JSON**:
1. Manual Trigger 노드 생성
2. Configuration 노드 (AAS asset 정보)
3. 각 step을 n8n Execute Workflow 또는 n8n HTTP 노드로 변환
4. Sticky Note 노드 추가 (레이아웃 정보 보존)
5. 노드 간 connection 생성

**n8n JSON → YAML**:
1. n8n 노드 순회
2. Sticky Note 노드 → notes[] 배열로 분리
3. 실행 노드 → steps[] 로 정규화

**Sticky Note 색상 매핑**:
```python
COLOR_NAME_TO_INT = {"yellow": 3, "blue": 4, "pink": 6, "green": 5}
```

### 6.5 Aggregation Service (`services/aggregation_service.py`)

분석/NLM 응답 생성에 사용되는 집계 함수 모음.

| 함수 | 반환 내용 |
|------|---------|
| `aggregate_daily_status(db, date)` | 작업지시 현황, 생산 실적, 설비 상태, KPI |
| `aggregate_equipment_utilization(db, equipment_id, days)` | 설비별 가동률, 병목 분석 |
| `aggregate_lot_traceability(db, lot_no)` | 로트 공정 이력, 수율, 타임라인 |
| `aggregate_kpi_dashboard(db)` | 오늘/주간/현재 KPI 요약 |

### 6.6 Event Publisher (`services/event_publisher.py`)

MES 이벤트를 발행하는 인터페이스 레이어.

**발행 이벤트**: `work_order.started`, `work_order.completed`, `equipment.status_changed`, `quality.defect_detected`, `alarm.triggered`

**현재 구현**: 로그 출력만 수행 (향후 Redis Pub/Sub / Kafka / WebSocket 통합 예정).

### 6.7 Circuit Breaker (`services/circuit_breaker.py`)

미들웨어 연결 불안정 시 장애 전파 방지. 일정 횟수 이상 실패하면 일시적으로 요청 차단.

### 6.8 Scheduling 서비스 (`services/scheduling/`)

| 파일 | 역할 |
|------|------|
| `http_client.py` | 외부 Cell-Scheduler 에이전트 HTTP 클라이언트 |
| `lock.py` | 스케줄링 요청 중복 방지 락 |
| `projector.py` | 스케줄 결과를 ProdResult로 프로젝션 |
| `result_applier.py` | 스케줄 결과 DB 반영 |

---

## 7. NLM — AI 자연어 어시스턴트

파일: `src/app/api/v1/endpoints/nlm.py`, `src/app/services/nlm_retriever/`

### 7.1 아키텍처

```
사용자 입력 (POST /nlm/query)
    │
    ▼
KeywordRetriever.retrieve(query)
    ├─ SynonymDict (26개 카테고리, 동의어 확장)
    ├─ IntentDetector (20개 의도, 키워드+패턴 점수 계산)
    │     키워드 매칭: +2점 / 정규식 패턴 매칭: +3점
    │     기간 표현 감지 → trend 강제 라우팅 (+10점)
    │     에러 키워드 감지 → equipment_error 부스팅 (+12점)
    └─ 상위 1개 의도 선택
    │
    ▼
DateExtractor (시간 엔티티 추출)
    ├─ 단일 날짜: 오늘/어제/그제, "YYYY-MM-DD", "N일 전"
    └─ 날짜 범위: 이번주/지난달, "최근 N일", "N일간"
    │
    ▼
ResponseGenerator (의도별 핸들러)
    ├─ DB 집계 (aggregation_service 호출)
    ├─ 텍스트 응답 생성
    └─ UISchema 생성 (KPICard, LineChart, DataTable 등)
    │
    ▼
QueryResult { text_response, ui_schema, metadata }
```

### 7.2 지원 의도 (20개)

| 의도 | 설명 | 예시 쿼리 |
|------|------|---------|
| `greeting` | 인사 | "안녕" |
| `help` | 도움말 | "뭘 할 수 있어?" |
| `daily_status` | 일일 생산 현황 | "오늘 생산 현황", "라인 살아있어?" |
| `production_count` | 생산량 조회 | "몇 개 만들었어?", "달성률" |
| `current_status` | 현재 상태 | "지금 뭐해?" |
| `compare_status` | 기간 비교 | "어제랑 오늘 비교" |
| `trend` | 추세 분석 | "이번 달 추이", "최근 7일" |
| `equipment_status` | 설비 현황 | "설비 가동률", "병목 설비" |
| `equipment_error` | 설비 고장 | "고장난 설비", "빨간불 들어왔어" |
| `equipment_idle` | 유휴 설비 | "놀고 있는 장비" |
| `yield_status` | 수율 | "수율 얼마야?" |
| `defect_analysis` | 불량 분석 | "불량 원인", "클레임" |
| `lot_trace` | 로트 추적 | "LOT-001 이력" |
| `work_orders` | 작업지시 | "작업 현황", "오더 목록" |
| `work_orders_in_progress` | 진행 중 작업 | "진행중인 작업" |
| `work_orders_pending` | 대기 작업 | "다음 뭐야?", "이거 끝나면" |
| `work_orders_completed` | 완료 작업 | "완료된 작업" |
| `schedule` | 스케줄 | "오늘 일정", "납기 맞출 수 있어?" |
| `schedule_delay` | 지연 | "지연되는 작업" |
| `kpi` | KPI 대시보드 | "KPI 보여줘", "OEE" |
| `report` | 리포트 | "일일 보고서", "경영진 보고" |

### 7.3 동적 UI 생성

NLM 응답의 `ui_schema`는 프론트엔드 `DynamicRenderer`가 실시간으로 렌더링.

```json
{
  "layout": "dashboard",
  "title": "오늘 생산 현황",
  "components": [
    { "type": "KPICard", "props": { "title": "수율", "value": 96.5, "unit": "%", "color": "blue", "target": 95 } },
    { "type": "DataTable", "props": { "columns": [...], "data": [...], "searchable": true } },
    { "type": "LineChart", "props": { "data": [...], "xKey": "date", "yKey": "생산량" } },
    { "type": "TraceabilityTimeline", "props": { "steps": [...] } }
  ]
}
```

**지원 컴포넌트 타입**: `KPICard`, `DataTable`, `LineChart`, `BarChart`, `PieChart`, `StatusGrid`, `StatusCards`, `TraceabilityTimeline`, `GanttChart`

### 7.4 NLM Retriever 서비스 (`services/nlm_retriever/`)

| 파일 | 역할 |
|------|------|
| `keyword_retriever.py` | 규칙 기반 검색 (동의어 사전 + 정규식) |
| `embedding_retriever.py` | ML 기반 검색 (sentence-transformers 임베딩) |
| `hybrid_retriever.py` | 키워드 + 임베딩 앙상블 |
| `cross_encoder_ranker.py` | 최종 순위 재조정 |
| `examples.py` | 의도별 예제 데이터셋 |
| `pipeline.py` | 전체 파이프라인 오케스트레이터 |

**현재 활성화**: `nlm.py`에서 `KeywordRetriever`만 직접 사용 (경량, 외부 API 불필요).

---

## 8. 설비 연동 — AAS 미들웨어

### 8.1 MiddlewareClient (`src/clients/middleware_client.py`)

```python
class MiddlewareClient:
    base_url: str  # settings.MIDDLEWARE_URL (기본: http://10.10.10.113:8100)

    async def fetch_all_assets() -> List[dict]
        # GET {base_url}/api/aas/view
        # 응답: {"data": [...]} 또는 직접 리스트

    async def get_equipment_status(connection_config) -> dict
        # GET {base_url}/api/resources/status?{connection_config}

    async def send_work_info(payload) -> bool
        # POST {base_url}/api/lots/{job_id}/start

    async def health_check() -> bool
        # GET {base_url}/api/aas/view → status < 400 여부
```

싱글턴 인스턴스 `middleware_client`를 전역 공유.

### 8.2 AAS 데이터 파싱 (`polling_service._parse_aas_item`)

미들웨어 응답에서 설비 상태를 파싱:

```
AAS Item {
  id, idShort,
  submodels: {
    cncGateway:    { isConnected, status: { doorState, ... } }
    robotGateway:  { isConnected, status: { status: "IDLE"/"BUSY"/... } }
    modbusGateway: { isConnected, status: {...} }
    workInformation: { ... }
  }
}
```

`equipment.last_data`에는 `submodels` 원본을 통째로 저장 → 프론트엔드에서 확장성 있게 접근 가능.

---

## 9. 인증 및 인가

### 9.1 JWT 토큰 인증 (`src/app/core/security.py`)

- 알고리즘: HS256
- 유효기간: 24시간 (설정 가능)
- 토큰 구조: `{ sub: user_id, exp: expiry_timestamp }`
- 프론트엔드: `localStorage`에 토큰 보관, 모든 요청에 `Authorization: Bearer <token>` 헤더 포함

### 9.2 역할 기반 접근 제어 (RBAC)

| 역할 | 권한 |
|------|------|
| `ADMIN` | 마스터 데이터 생성/수정/삭제, 시스템 설정, 설비 동기화 |
| `OPERATOR` | 생산 운영 (작업지시, 실적 등록), 데이터 조회 |
| `SERVICE` | 내부 서비스 인증 (NL-Router, Scheduler) |

### 9.3 의존성 주입 (`src/app/api/deps.py`)

```python
CurrentUser  = Depends(get_current_user)      # JWT 또는 X-Internal-Service-Key
AdminUser    = Depends(get_current_admin_user) # ADMIN 역할 필수
DBSession    = Depends(get_db)                 # 비동기 DB 세션
```

### 9.4 내부 서비스 인증

`X-Internal-Service-Key` 헤더로 서비스 간 인증:
```python
if x_internal_service_key == settings.INTERNAL_SERVICE_KEY:
    return ServiceUser(role="SERVICE")
```

---

## 10. 프론트엔드 — 기술 스택 및 페이지 구조

### 기술 스택 (`frontend/package.json`)

| 분류 | 패키지 | 버전 |
|------|--------|------|
| **프레임워크** | next | 14.2.0 |
| **UI 라이브러리** | react | ^18.2.0 |
| **언어** | typescript | ^5.4.0 |
| **스타일링** | tailwindcss | ^3.4.0 |
| **서버 상태** | @tanstack/react-query | ^5.28.0 |
| **클라이언트 상태** | zustand | ^4.5.0 |
| **HTTP** | axios | ^1.6.0 |
| **차트** | recharts | ^2.12.0 |
| **플로우 에디터** | reactflow | ^11.11.0 |
| **날짜** | date-fns | ^3.3.0 |
| **아이콘** | lucide-react | ^0.363.0 |
| **JSON 뷰어** | react-json-view-lite | ^1.2.0 |
| **E2E 테스트** | playwright | ^1.58.2 |
| **단위 테스트** | vitest | ^4.0.18 |

### 페이지 라우트 구조 (`frontend/app/`)

```
app/
├── layout.tsx                          # 루트 레이아웃 (QueryClient, Providers)
├── providers.tsx                       # TanStack Query 등 전역 Provider
├── login/page.tsx                      # 로그인 페이지
└── (main)/                             # 인증 필요 그룹 (layout에서 인증 체크)
    ├── layout.tsx                      # 사이드바 + 네비게이션
    ├── page.tsx                        # 대시보드 (KPI 카드, 설비 현황)
    ├── chat/page.tsx                   # NLM AI 어시스턴트 채팅
    ├── production/
    │   ├── orders/page.tsx             # 작업지시 관리 (CRUD + 상태 변경)
    │   └── results/page.tsx            # 생산 실적 조회
    ├── quality/
    │   ├── page.tsx                    # 품질 대시보드
    │   ├── spc/page.tsx                # SPC 관리도
    │   ├── ncr/page.tsx                # NCR 관리
    │   ├── inspection-plans/page.tsx   # 검사 계획
    │   └── inspection-results/page.tsx # 검사 결과
    ├── master/
    │   ├── products/page.tsx           # 품목 관리
    │   ├── processes/page.tsx          # 표준 공정 관리
    │   ├── routings/page.tsx           # 공정 라우팅 관리
    │   ├── equipments/page.tsx         # 설비 관리 (AAS 동기화 버튼 포함)
    │   ├── cells/page.tsx              # 셀(작업 그룹) 관리
    │   └── scenarios/
    │       ├── page.tsx                # 시나리오 목록
    │       └── [id]/edit/page.tsx      # n8n 비주얼 시나리오 에디터
    ├── scheduler/
    │   ├── page.tsx                    # 간트 차트 스케줄 뷰
    │   ├── execute/page.tsx            # 스케줄 실행 제어
    │   └── settings/page.tsx          # 스케줄러 설정
    ├── analytics/
    │   ├── page.tsx                    # KPI 대시보드
    │   ├── equipment/page.tsx          # 설비 이용률 분석
    │   └── lot-trace/page.tsx          # 로트 추적 타임라인
    ├── alarms/page.tsx                 # 설비 알람 관리
    └── downtime/page.tsx               # 다운타임 관리
```

---

## 11. 프론트엔드 — 컴포넌트 목록

### Chat 컴포넌트 (`components/chat/`)
- `ChatInterface` — 전체 채팅 UI 컨테이너
- `ChatInput` — 쿼리 입력창 (즐겨찾기 버튼 포함)
- `ChatMessage` / `MessageBubble` — 메시지 렌더링
- `HistorySidebar` — 이전 쿼리 히스토리
- `QuickActions` — 자주 쓰는 쿼리 버튼 모음
- `ToolCallCard` — 도구 호출 시각화

### Dynamic Renderer (`components/dynamic/`)
NLM 응답의 UISchema를 동적으로 React 컴포넌트로 변환하는 핵심 모듈.
- `DynamicRenderer` — UISchema → React 변환 라우터
- `DynamicDataTable` — 정렬/검색/페이지네이션 테이블
- `KPICard` — KPI 지표 카드 (목표선, 추세 방향)
- `StatusCards` — 상태 요약 카드 그룹
- `StatusGrid` — 설비 상태 그리드 (4열)
- `TraceabilityTimeline` — 로트 공정 타임라인
- `DynamicLineChart` / `DynamicBarChart` / `DynamicPieChart` — 차트
- `GanttChart` — 간트 차트 (작업지시 × 설비)

### 시나리오 에디터 (`components/scenario-editor/`)
ReactFlow 기반 n8n 워크플로우 비주얼 에디터 (24개 컴포넌트).
- `ScenarioCanvas` — 메인 캔버스 (ReactFlow 래퍼)
- `NodeStatusIndicator` — 노드 실행 상태 표시
- `ScenarioStepNode` / `ScenarioConfigNode` / `StickyNoteNode` / `ManualTriggerNode` — 노드 타입
- `NodeSearchPalette` — 노드 검색/추가 팔레트
- `ParameterPanel` / `StepParameterForm` — 노드 파라미터 편집
- `RoutingRulesEditor` — 조건부 라우팅 규칙 편집
- `VariableExplorer` — 변수 탐색기
- `YamlPreviewModal` — YAML 미리보기
- `ExecutionPanel` / `RunStatusIndicator` / `ExecutionDataViewer` — 실행 상태
- `KeyboardShortcutsHelp` — 단축키 도움말
- `ExpressionInput` — n8n 표현식 입력
- `RoutingEdge` — 커스텀 라우팅 엣지

### 스케줄러 컴포넌트 (`components/scheduler/`)
- `SchedulerGanttChart` — 설비별 작업지시 간트 차트
- `JsonModal` — 스케줄 JSON 원본 뷰어

### 품질 컴포넌트 (`components/quality/`)
- `InspectionPlanForm` / `InspectionPlanTable` — 검사 계획 CRUD
- `NCRForm` — NCR 등록 폼
- `SPCChart` — SPC 관리도 (Recharts 기반)
- `InspectionPlanFormImproved` — 개선된 검사 계획 폼

### 공통 UI (`components/ui/`, `components/common/`)
- `Sidebar` — 좌측 네비게이션 (KITECH 로고 포함)
- `Popover` / `Tooltip` — 팝오버, 툴팁
- `ConnectionBadge` — 미들웨어 연결 상태 뱃지
- `SortableHeader` — 정렬 가능한 테이블 헤더
- `KitechLogo` — KITECH 브랜드 로고
- `ConnectionStatus` — WebSocket/API 연결 상태 표시
- `ErrorBoundary` — React 오류 경계
- `LoadingState` — 로딩 스피너

---

## 12. 프론트엔드 — 상태 관리

### Zustand 스토어 (`frontend/stores/`)

**authStore.ts**:
```typescript
interface AuthState {
  user: User | null
  isAuthenticated: boolean
  setAuth: (token: string, user: User) => void   // 로그인 시 호출
  logout: () => void
  checkAuth: () => boolean                        // 토큰 유효성 확인
}
// persist: localStorage에 user 정보 영구 저장
```

**chatStore.ts**:
```typescript
interface ChatState {
  messages: Message[]
  isLoading: boolean
  favorites: string[]
  addMessage: (message: Message) => void
  clearMessages: () => void
  setLoading: (loading: boolean) => void
  addFavorite(query: string) / removeFavorite(query: string)
}
// persist: favorites만 localStorage에 저장 (messages는 ephemeral)
```

### TanStack React Query

- 모든 GET API 요청 자동 캐싱
- `staleTime` 설정으로 자동 갱신 제어 (설비 상태: 2000ms)
- `useMutation`으로 POST/PUT/DELETE 요청 + 자동 캐시 무효화

### API 클라이언트 생성

```bash
npm run generate:api
# openapi-typescript-codegen으로 백엔드 OpenAPI JSON에서
# 타입 안전 API 클라이언트 자동 생성 (src/generated/api/)
```

---

## 13. Alembic 마이그레이션 이력

| 버전 | 파일명 | 주요 변경 |
|------|--------|---------|
| `001` | `001_initial_schema.py` | 초기 스키마 — users, std_processes, products, equipments, process_routings, scenarios, work_orders, prod_results, eq_logs |
| `002` | `002_add_stdprocess_scheduler_fields.py` | StdProcess에 스케줄러 필드 추가 — setup_time_sec, cycle_time_sec, equipment_type |
| `003` | `003_add_quality_tables.py` | 품질 관리 테이블 추가 — inspection_plans, inspection_results, non_conformances, spc_charts, spc_data_points |
| `004` | `004_add_process_categories_and_cells.py` | 공정 분류 및 셀 관리 — process_categories, cells, equipments.cell_id FK 추가 |
| `006` | `006_add_unit_table_for_lot_size_1_.py` | Lot-Size 1 아키텍처 — units 테이블 신규 추가 |
| `dcb434f` | `dcb434f47f7d_add_users_table.py` | 사용자 테이블 강화 — users.role 컬럼 추가 |

**마이그레이션 명령**:
```bash
alembic upgrade head        # 최신 버전으로 적용
alembic downgrade -1        # 한 버전 롤백
alembic current             # 현재 적용된 버전 확인
alembic history             # 전체 마이그레이션 이력
```

---

## 14. Docker 및 배포

### Dockerfile

```dockerfile
FROM python:3.11-slim

# uv 패키지 매니저 복사 (빠른 설치)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY . /app

# 전체 워크스페이스 의존성 설치 (로컬 패키지 포함)
RUN uv sync --frozen --all-packages

WORKDIR /app/agents/cell-mes
CMD ["uv", "run", "--no-sync", "uvicorn", "src.app.main:app",
     "--host", "0.0.0.0", "--port", "8000"]
```

### 로컬 개발 실행

```bash
cd agents/cell-mes
uv sync
uv run uvicorn src.app.main:app --reload --port 8000

# 프론트엔드
cd frontend
npm install
npm run dev           # http://localhost:3000
```

### 운영 환경 실행

```bash
docker build -t cell-mes:latest .
docker run -d -p 8000:8000 \
  -e ENV=production \
  -e DATABASE_URL="postgresql+asyncpg://user:pass@db:5432/cell_mes" \
  -e SECRET_KEY="<강력한-랜덤-키>" \
  -e INTERNAL_SERVICE_KEY="<내부-서비스-키>" \
  -e MIDDLEWARE_URL="http://10.10.10.113:8100" \
  -e CORS_ORIGINS="https://mes.example.com" \
  cell-mes:latest
```

---

## 15. 테스트 구성

### 백엔드 (`tests/`)
- **도구**: pytest + pytest-asyncio + pytest-cov
- **총 테스트 수**: 530개
- **DB**: 테스트용 SQLite in-memory

```bash
uv run pytest                            # 전체 실행
uv run pytest --cov=src tests/           # 커버리지 포함
uv run pytest tests/test_equipments.py  # 특정 파일
```

### 프론트엔드 (`frontend/__tests__/`)
- **도구**: Vitest + Playwright
- **E2E 테스트 파일** (18개):

| 파일 | 테스트 대상 |
|------|-----------|
| `auth.test.ts` | 로그인/로그아웃 |
| `chat.test.ts` | NLM 채팅 |
| `alarms.test.ts` | 알람 목록/처리 |
| `analytics.test.ts` | 분석 대시보드 |
| `crud/equipments.test.ts` | 설비 CRUD |
| `crud/products.test.ts` | 품목 CRUD |
| `crud/processes.test.ts` | 표준공정 CRUD |
| `crud/routings.test.ts` | 라우팅 CRUD |
| `crud/scenarios.test.ts` | 시나리오 CRUD |
| `crud/work-orders.test.ts` | 작업지시 CRUD |
| `crud/production-results.test.ts` | 생산 실적 CRUD |
| `crud/ncr.test.ts` | NCR CRUD |
| `crud/inspection-plans.test.ts` | 검사 계획 CRUD |

```bash
npm run test              # 전체
npm run test:unit         # 단위 테스트만
npm run test:e2e          # E2E 테스트만
npm run test:coverage     # 커버리지 포함
```

---

## 16. 환경 변수 전체 목록

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `ENV` | `development` | 환경 구분 (development/production) |
| `DEBUG` | `false` | 디버그 모드 |
| `APP_NAME` | `Cell-MES` | 앱 이름 |
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/mes.db` | DB 연결 문자열 |
| `SECRET_KEY` | *(변경 필수)* | JWT 서명 키 |
| `ALGORITHM` | `HS256` | JWT 알고리즘 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | JWT 유효기간 (분) |
| `INTERNAL_SERVICE_KEY` | *(변경 필수)* | 내부 서비스 인증 키 |
| `MIDDLEWARE_URL` | `http://10.10.10.113:8100` | AAS 미들웨어 서버 URL |
| `MIDDLEWARE_TIMEOUT` | `30` | 미들웨어 요청 타임아웃 (초) |
| `NL_ROUTER_URL` | `http://localhost:8001` | NL-Router 서비스 URL |
| `CELL_SCHEDULER_URL` | `http://localhost:8002` | Cell-Scheduler 서비스 URL |
| `TORUS_GATEWAY_URL` | `http://10.10.10.113:5001` | Torus Gateway URL |
| `REDIS_URL` | `redis://localhost:6379` | Redis URL (향후 캐시용) |
| `EQUIPMENT_POLL_INTERVAL_SEC` | `3` | 설비 폴링 간격 (초) |
| `UPLOAD_DIR` | `./uploads` | 파일 업로드 디렉토리 |
| `MAX_FILE_SIZE_MB` | `50` | 최대 업로드 파일 크기 (MB) |
| `CORS_ORIGINS` | `http://localhost:3000,...` | 허용 CORS 출처 (쉼표 구분) |
| `SCENARIOS_DIR` | `./scenarios` | 시나리오 YAML 저장 디렉토리 |
| `LOG_LEVEL` | `INFO` | 로그 레벨 |
| `SCHEDULER_DEFAULT_SOLVER` | `OR_TOOLS` | 스케줄러 최적화 솔버 |
| `SCHEDULER_DEFAULT_HORIZON_HOURS` | `24` | 스케줄 수평선 (시간) |
| `SCHEDULER_DEFAULT_TIME_LIMIT_SEC` | `60` | 최적화 제한 시간 (초) |

---

## 부록. 주요 파일 경로 빠른 참조

| 기능 | 파일 경로 |
|------|---------|
| FastAPI 진입점 | `src/app/main.py` |
| 설정 관리 | `src/app/core/config.py` |
| JWT 보안 | `src/app/core/security.py` |
| API 라우터 등록 | `src/app/api/v1/api.py` |
| 의존성 주입 | `src/app/api/deps.py` |
| 설비 API | `src/app/api/v1/endpoints/equipments.py` |
| AAS 동기화 서비스 | `src/app/services/sync_service.py` |
| AAS 폴링 서비스 | `src/app/services/polling_service.py` |
| Lot-Size 1 디스패치 | `src/app/services/dispatch_service.py` |
| n8n 시나리오 변환 | `src/app/services/scenario_converter.py` |
| NLM 자연어 처리 | `src/app/api/v1/endpoints/nlm.py` |
| 데이터 집계 | `src/app/services/aggregation_service.py` |
| 미들웨어 클라이언트 | `src/clients/middleware_client.py` |
| 설비 모델 | `src/app/models/equipment.py` |
| 생산 모델 | `src/app/models/production.py` |
| 품질 모델 | `src/app/models/quality.py` |
| 마스터 모델 | `src/app/models/master.py` |
| 프론트 레이아웃 | `frontend/app/(main)/layout.tsx` |
| 인증 스토어 | `frontend/stores/authStore.ts` |
| 채팅 스토어 | `frontend/stores/chatStore.ts` |
| 동적 UI 렌더러 | `frontend/components/dynamic/DynamicRenderer.tsx` |
| 시나리오 에디터 | `frontend/components/scenario-editor/ScenarioCanvas.tsx` |
| 간트 차트 | `frontend/components/dynamic/GanttChart.tsx` |
