# Clean Architecture

의존성 규칙과 레이어 분리를 통한 유지보수 가능한 아키텍처 설계.

## Critical Rules

1. **의존성은 항상 안쪽(Domain)을 향함** - 바깥 레이어가 안쪽에 의존
2. **Domain은 외부 프레임워크에 의존하지 않음** - 순수 Python
3. **인터페이스로 의존성 역전** - 구현은 Infrastructure에서
4. **레이어 경계 넘을 때 DTO 사용** - 직접 Entity 노출 지양

## 레이어 구조

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                       │
│                    (Controllers, API, UI)                    │
├─────────────────────────────────────────────────────────────┤
│                    Application Layer                         │
│                 (Use Cases, Commands, Queries)               │
├─────────────────────────────────────────────────────────────┤
│                      Domain Layer                            │
│            (Entities, Value Objects, Domain Events)          │
├─────────────────────────────────────────────────────────────┤
│                   Infrastructure Layer                       │
│              (Database, External APIs, Messaging)            │
└─────────────────────────────────────────────────────────────┘
         ▲                                              │
         │              의존성 방향                      │
         └──────────────────────────────────────────────┘
```

## 의존성 규칙

### Domain Layer (Core)

```python
# domain/production/entities.py
# ✅ 순수 Python, 외부 의존성 없음

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class WorkOrderEntity:
    id: Optional[int] = None
    lot_no: str = ""
    status: str = "READY"
    
    def start(self) -> None:
        if self.status != "READY":
            raise ValueError("Cannot start")
        self.status = "RUNNING"
```

**Domain에서 금지:**
- SQLAlchemy, FastAPI 등 프레임워크 import
- 외부 API 호출
- 파일 시스템 접근
- 환경변수 직접 읽기

### Application Layer

```python
# application/production/handlers.py
# ✅ Domain만 의존, Infrastructure 인터페이스 사용

from domain.production import WorkOrderEntity, WorkOrderRepository

class CreateWorkOrderHandler:
    def __init__(self, repository: WorkOrderRepository):  # 인터페이스!
        self.repository = repository
    
    async def handle(self, command: CreateWorkOrderCommand) -> WorkOrderEntity:
        entity = WorkOrderEntity(lot_no=command.lot_no)
        return await self.repository.save(entity)
```

### Infrastructure Layer

```python
# infrastructure/persistence/sqlalchemy/repositories.py
# ✅ Domain 인터페이스 구현

from sqlalchemy.ext.asyncio import AsyncSession
from domain.production import WorkOrderRepository, WorkOrderEntity

class SQLAlchemyWorkOrderRepository(WorkOrderRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save(self, entity: WorkOrderEntity) -> WorkOrderEntity:
        model = self._to_model(entity)
        self.session.add(model)
        await self.session.commit()
        return self._to_entity(model)
```

### Presentation Layer

```python
# api/v1/endpoints/production.py
# ✅ Application, Domain 의존, Infrastructure 주입 받음

from fastapi import APIRouter, Depends
from application.production import CreateWorkOrderHandler, CreateWorkOrderCommand

router = APIRouter()

@router.post("/orders")
async def create_order(
    request: WorkOrderCreateRequest,  # API 스키마
    handler: CreateWorkOrderHandler = Depends(get_handler),
):
    command = CreateWorkOrderCommand(
        lot_no=request.lot_no,
        product_id=request.product_id,
    )
    entity = await handler.handle(command)
    return WorkOrderResponse.from_entity(entity)  # DTO로 변환
```

## 포트와 어댑터 (Hexagonal Architecture)

```
                    ┌─────────────────────────────────────┐
                    │                                     │
   Primary          │          Application Core           │          Secondary
   Adapters         │                                     │          Adapters
                    │  ┌─────────────────────────────┐    │
┌─────────┐         │  │                             │    │         ┌─────────┐
│ REST API│─────────┼─►│       Domain Logic          │◄───┼─────────│Database │
└─────────┘         │  │                             │    │         └─────────┘
                    │  └─────────────────────────────┘    │
┌─────────┐         │               ▲                     │         ┌─────────┐
│   CLI   │─────────┼───────────────┼─────────────────────┼─────────│  Redis  │
└─────────┘         │               │                     │         └─────────┘
                    │          Ports                      │
┌─────────┐         │      (Interfaces)                   │         ┌─────────┐
│ GraphQL │─────────┼─────────────────────────────────────┼─────────│ Ext API │
└─────────┘         │                                     │         └─────────┘
                    └─────────────────────────────────────┘
```

### Port (Interface)

```python
# domain/production/repository.py - Port
from abc import ABC, abstractmethod

class WorkOrderRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[WorkOrderEntity]:
        pass
    
    @abstractmethod
    async def save(self, entity: WorkOrderEntity) -> WorkOrderEntity:
        pass
```

### Adapter (Implementation)

```python
# infrastructure/persistence/sqlalchemy/repositories.py - Adapter
class SQLAlchemyWorkOrderRepository(WorkOrderRepository):
    # 구현...

# infrastructure/persistence/in_memory/repositories.py - 테스트용 Adapter
class InMemoryWorkOrderRepository(WorkOrderRepository):
    def __init__(self):
        self._store: Dict[int, WorkOrderEntity] = {}
    
    async def get_by_id(self, id: int) -> Optional[WorkOrderEntity]:
        return self._store.get(id)
    
    async def save(self, entity: WorkOrderEntity) -> WorkOrderEntity:
        if entity.id is None:
            entity.id = len(self._store) + 1
        self._store[entity.id] = entity
        return entity
```

## 의존성 주입

```python
# api/deps.py

from functools import lru_cache
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

# Repository 생성
def get_work_order_repository(
    db: AsyncSession = Depends(get_db)
) -> WorkOrderRepository:
    return SQLAlchemyWorkOrderRepository(db)

# Handler 생성
def get_create_handler(
    repository: WorkOrderRepository = Depends(get_work_order_repository)
) -> CreateWorkOrderHandler:
    return CreateWorkOrderHandler(repository)

# 테스트에서 교체
def override_repository():
    return InMemoryWorkOrderRepository()

app.dependency_overrides[get_work_order_repository] = override_repository
```

## DTO (Data Transfer Object)

레이어 경계에서 데이터 변환.

```python
# api/schemas/production.py - API 스키마

from pydantic import BaseModel

class WorkOrderCreateRequest(BaseModel):
    """API 요청 스키마."""
    lot_no: str
    product_id: int
    target_qty: int

class WorkOrderResponse(BaseModel):
    """API 응답 스키마."""
    id: int
    lot_no: str
    status: str
    progress_percent: float
    
    @classmethod
    def from_entity(cls, entity: WorkOrderEntity) -> "WorkOrderResponse":
        return cls(
            id=entity.id,
            lot_no=str(entity.lot_no),
            status=entity.status.value,
            progress_percent=entity.progress_percent,
        )
```

## 테스트 전략

### Unit Tests (Domain)

```python
# tests/domain/test_entities.py
# 외부 의존성 없이 순수 로직 테스트

def test_work_order_start():
    wo = WorkOrderEntity(lot_no=LotNumber("LOT-001"))
    
    wo.start()
    
    assert wo.status == WorkOrderStatus.RUNNING
```

### Integration Tests (Application)

```python
# tests/application/test_handlers.py
# In-Memory Repository로 테스트

@pytest.fixture
def repository():
    return InMemoryWorkOrderRepository()

@pytest.fixture
def handler(repository):
    return CreateWorkOrderHandler(repository)

async def test_create_work_order(handler):
    command = CreateWorkOrderCommand(lot_no="LOT-001", product_id=1, target_qty=100)
    
    result = await handler.handle(command)
    
    assert result.id is not None
    assert str(result.lot_no) == "LOT-001"
```

### E2E Tests (API)

```python
# tests/api/test_production.py
# 실제 HTTP 요청 테스트

async def test_create_order_api(client, db_session):
    response = await client.post("/api/v1/production/orders", json={
        "lot_no": "LOT-001",
        "product_id": 1,
        "target_qty": 100,
    })
    
    assert response.status_code == 201
    assert response.json()["lot_no"] == "LOT-001"
```

## 디렉토리 구조

```
src/
├── domain/                    # Core Business Logic
│   ├── production/
│   │   ├── entities.py        # WorkOrderEntity
│   │   ├── value_objects.py   # LotNumber, Quantity
│   │   ├── repository.py      # Repository Interface (Port)
│   │   └── events.py          # Domain Events
│   └── quality/
│       └── ...
│
├── application/               # Use Cases
│   ├── production/
│   │   ├── commands.py        # CreateWorkOrder, StartWorkOrder
│   │   ├── queries.py         # GetWorkOrder, ListWorkOrders
│   │   └── handlers.py        # Command/Query Handlers
│   └── ...
│
├── infrastructure/            # External Concerns
│   ├── persistence/
│   │   ├── sqlalchemy/
│   │   │   ├── models.py      # ORM Models
│   │   │   └── repositories.py # Repository Implementation
│   │   └── in_memory/
│   │       └── repositories.py # Test Implementation
│   └── messaging/
│       └── redis_event_bus.py
│
└── api/                       # Presentation
    ├── v1/
    │   ├── endpoints/
    │   │   └── production.py  # REST Endpoints
    │   └── schemas/           # Pydantic Schemas (DTOs)
    └── deps.py                # Dependency Injection
```

## Anti-patterns

```python
# ❌ Domain에서 Infrastructure 의존
from sqlalchemy.orm import Session
class WorkOrderEntity:
    def save(self, session: Session):  # SQLAlchemy 직접 사용
        pass

# ❌ Application에서 HTTP 클라이언트 직접 사용
class CreateOrderHandler:
    async def handle(self, cmd):
        response = await httpx.get("...")  # 외부 의존성
        
# ❌ Entity를 API 응답으로 직접 반환
@router.get("/orders/{id}")
async def get_order(id: int):
    return entity  # 내부 구조 노출

# ❌ 레이어 건너뛰기
@router.post("/orders")
async def create_order(db: Session):
    # API에서 직접 DB 접근 (Application 레이어 스킵)
    db.add(WorkOrder(...))
```

## 점진적 마이그레이션

1. **Domain 레이어 추출**: Value Object, Entity 정의
2. **Repository 인터페이스**: 기존 쿼리를 인터페이스로 추상화
3. **Application 레이어**: 엔드포인트 로직을 Handler로 이동
4. **Infrastructure 분리**: ORM 모델과 Entity 분리
5. **테스트 리팩토링**: In-Memory Repository로 단위 테스트

## 관련 스킬

- [ddd_patterns.md](ddd_patterns.md) - DDD 패턴
- [event_driven.md](event_driven.md) - 이벤트 기반 아키텍처
- [test_implementation.md](test_implementation.md) - 테스트 작성
