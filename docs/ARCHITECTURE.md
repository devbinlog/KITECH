# agents-workspace 아키텍처

## 개요

agents-workspace는 CNC 가공 분석 및 스케줄링을 위한 멀티 에이전트 시스템입니다.
마이크로서비스 아키텍처와 이벤트 기반 통신을 사용하여 느슨하게 결합된 서비스들로 구성됩니다.

## 시스템 구조

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
│   Cell-MES    │         │   NL-Router   │         │ Cell-Scheduler│
│   (8000)      │◄───────►│   (8001)      │         │   (8002)      │
│               │         │               │         │               │
│ • REST API    │         │ • 자연어 처리  │         │ • 스케줄링    │
│ • 인증 (JWT)  │         │ • Intent 분류 │         │ • OR-Tools    │
│ • DB 접근     │         │ • UI 생성     │         │ • GA/SA/TABU  │
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

## 서비스 역할

### Cell-MES (Port 8000)
Manufacturing Execution System - 생산 관리의 핵심

- **작업지시 관리**: 생산 작업 생성, 상태 추적, 완료 처리
- **생산실적 기록**: OK/NG 수량, 사이클 타임, 불량 코드
- **설비 관리**: 설비 상태 모니터링, 가동률 분석
- **품질 관리**: 검사 기록, NCR 관리
- **분석/KPI**: 생산 현황, 수율, 가동률 대시보드

### NL-Router (Port 8001)
Natural Language Router - 자연어 인터페이스

- **Intent 분류**: 사용자 질의 의도 파악
- **Entity 추출**: LOT 번호, 날짜, 설비명 등 추출
- **API 오케스트레이션**: MES API 호출 조합
- **UI 스키마 생성**: 동적 UI 컴포넌트 생성

### Cell-Scheduler (Port 8002)
Production Scheduler - 생산 스케줄링

- **멀티 솔버 지원**: OR-Tools, GA, SA, TABU
- **제약 조건 처리**: 선행공정, 설비 호환성, 셋업 시간
- **최적화 목표**: Makespan 최소화, 납기 준수, 가동률 최대화
- **Gantt 차트 데이터**: 시각화용 스케줄 데이터 생성

## 서비스 간 통신

### 동기 통신 (REST API)

```
NL-Router ──────► Cell-MES
   │                 │
   │  X-Internal-    │
   │  Service-Key    │
   └─────────────────┘

Cell-MES ──────► Cell-Scheduler
   │                 │
   │  /api/v1/       │
   │  schedule/solve │
   └─────────────────┘
```

**내부 서비스 인증:**
- `X-Internal-Service-Key` 헤더 사용
- JWT 인증 우회 (서비스 간 신뢰)

### 비동기 통신 (Redis Event Bus)

```
┌─────────────┐     publish     ┌─────────────┐
│  Cell-MES   │───────────────►│    Redis    │
└─────────────┘                 │  Pub/Sub    │
                                └──────┬──────┘
                                       │ subscribe
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
              ┌─────┴─────┐      ┌─────┴─────┐      ┌─────┴─────┐
              │ Dashboard │      │ Analytics │      │ Scheduler │
              └───────────┘      └───────────┘      └───────────┘
```

**이벤트 흐름:**
1. Cell-MES에서 작업지시 생성 → `work_order.created` 이벤트 발행
2. Scheduler가 구독하여 재스케줄링 트리거
3. Dashboard가 구독하여 실시간 업데이트

## 이벤트 카탈로그

### Production Events
| Event | Publisher | Consumers | Description |
|-------|-----------|-----------|-------------|
| `work_order.created` | Cell-MES | Scheduler, Dashboard | 작업지시 생성 |
| `work_order.status_changed` | Cell-MES | Dashboard, Analytics | 상태 변경 |
| `production.recorded` | Cell-MES | Analytics, Quality | 생산실적 기록 |

### Scheduling Events
| Event | Publisher | Consumers | Description |
|-------|-----------|-----------|-------------|
| `schedule.requested` | Cell-MES | Scheduler | 스케줄링 요청 |
| `schedule.completed` | Scheduler | Cell-MES, Dashboard | 스케줄링 완료 |
| `equipment.availability_changed` | Cell-MES | Scheduler | 설비 가용성 변경 |

### Quality Events
| Event | Publisher | Consumers | Description |
|-------|-----------|-----------|-------------|
| `inspection.completed` | Cell-MES | Analytics, NCR | 검사 완료 |
| `ncr.created` | Cell-MES | Quality, Dashboard | NCR 생성 |

## DDD 레이어 구조 (Cell-MES)

```
agents/cell-mes/src/
├── domain/                    # 핵심 도메인 (의존성 없음)
│   └── production/
│       ├── entities.py        # WorkOrderEntity, ProductionResultEntity
│       ├── value_objects.py   # LotNumber, Quantity, Priority, YieldRate
│       ├── repository.py      # Repository 인터페이스 (ABC)
│       └── events.py          # 도메인 이벤트
│
├── application/               # 유스케이스 (domain만 의존)
│   └── production/
│       ├── commands.py        # CreateWorkOrder, StartWorkOrder 등
│       ├── queries.py         # GetWorkOrder, ListWorkOrders 등
│       └── handlers.py        # 명령/쿼리 핸들러
│
├── infrastructure/            # 외부 의존성 (domain, application 구현)
│   ├── persistence/
│   │   └── sqlalchemy/
│   │       ├── models.py      # ORM 모델
│   │       └── repositories.py # Repository 구현체
│   └── messaging/
│       └── redis_event_bus.py
│
└── app/                       # 프레젠테이션 (FastAPI)
    ├── api/v1/endpoints/      # REST 엔드포인트
    ├── schemas/               # Pydantic 스키마
    └── services/              # 애플리케이션 서비스
```

### 의존성 방향

```
┌─────────────────────────────────────────────────────────┐
│                    Presentation (API)                    │
│                           │                              │
│                           ▼                              │
│  ┌─────────────────────────────────────────────────┐    │
│  │                Application (Use Cases)           │    │
│  │                           │                      │    │
│  │                           ▼                      │    │
│  │  ┌─────────────────────────────────────────┐    │    │
│  │  │              Domain (Core)              │    │    │
│  │  │    (Entities, Value Objects, Events)    │    │    │
│  │  └─────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────┘    │
│                           ▲                              │
│                           │                              │
│  ┌─────────────────────────────────────────────────┐    │
│  │           Infrastructure (외부 의존성)           │    │
│  │      (Database, Redis, External APIs)           │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

**핵심 원칙:**
- Domain 레이어는 외부 의존성이 없음 (순수 Python)
- Infrastructure는 Domain 인터페이스를 구현
- 의존성은 항상 안쪽(Domain)을 향함

## 환경 설정

### 환경변수 구조

```
프로젝트 루트/
├── .env.example     # 템플릿 (커밋)
├── .env.dev         # 개발 환경 (커밋)
├── .env.prod        # 운영 환경 (커밋 제외 권장)
└── services.env     # 포트 설정 (start-services.sh용)
```

### 주요 환경변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `ENV` | 환경 (development/production) | development |
| `CELL_MES_URL` | MES 서비스 URL | http://localhost:8000 |
| `NL_ROUTER_URL` | NL Router URL | http://localhost:8001 |
| `CELL_SCHEDULER_URL` | Scheduler URL | http://localhost:8002 |
| `REDIS_URL` | Redis 연결 URL | redis://localhost:6379 |
| `DATABASE_URL` | DB 연결 URL | sqlite+aiosqlite:///./data/mes.db |
| `INTERNAL_SERVICE_KEY` | 내부 서비스 인증 키 | (변경 필수) |

## 데이터베이스 스키마

### 주요 테이블

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    products     │     │   work_orders   │     │  prod_results   │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ id (PK)         │◄────│ product_id (FK) │◄────│ work_order_id   │
│ code            │     │ lot_no          │     │ equipment_id    │
│ name            │     │ target_qty      │     │ ok_qty          │
│ description     │     │ status          │     │ ng_qty          │
└─────────────────┘     │ priority        │     │ start_time      │
                        │ due_date        │     │ end_time        │
                        └─────────────────┘     └─────────────────┘

┌─────────────────┐     ┌─────────────────┐
│   equipments    │     │  std_processes  │
├─────────────────┤     ├─────────────────┤
│ id (PK)         │     │ id (PK)         │
│ eq_name         │     │ code            │
│ equipment_type  │     │ name            │
│ current_status  │     │ equipment_type  │
└─────────────────┘     │ cycle_time_sec  │
                        └─────────────────┘
```

## 보안 고려사항

### 인증/인가

1. **외부 사용자**: JWT 토큰 기반 인증
2. **내부 서비스**: `X-Internal-Service-Key` 헤더
3. **프로덕션**: 반드시 SECRET_KEY, INTERNAL_SERVICE_KEY 변경

### 네트워크

1. 서비스는 `0.0.0.0`에 바인딩 (컨테이너 환경)
2. 프로덕션에서는 리버스 프록시 사용 권장
3. CORS는 환경변수로 허용 origin 제한

## 확장성 고려사항

### 수평 확장

- **Cell-MES**: DB 연결 풀링, 읽기 전용 복제본 지원
- **Cell-Scheduler**: 작업 큐 기반 분산 처리 가능
- **Redis**: 클러스터 모드 지원

### 이벤트 기반 확장

새 서비스 추가 시:
1. Redis 이벤트 구독으로 기존 서비스에 영향 없이 연동
2. 이벤트 스키마는 `shared/events/`에서 공유

## 모니터링

### Health Check 엔드포인트

- Cell-MES: `GET /health`
- NL-Router: `GET /health`
- Cell-Scheduler: `GET /health`

### 로깅

- 구조화된 로깅 (JSON 포맷 권장)
- 로그 레벨: `LOG_LEVEL` 환경변수로 제어
- 서비스명, 요청 ID 포함

## 관련 문서

- [서비스 관리](../shared/skills/service_management.md)
- [설정 관리](../shared/skills/config_management.md)
- [DDD 패턴](../shared/skills/ddd_patterns.md)
- [이벤트 기반 아키텍처](../shared/skills/event_driven.md)
