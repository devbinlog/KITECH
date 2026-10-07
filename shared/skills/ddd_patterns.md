# DDD (Domain-Driven Design) Patterns

도메인 주도 설계의 핵심 패턴과 agents-workspace에서의 적용 방법.

## Critical Rules

1. **Domain 레이어는 외부 의존성 없음** - 순수 Python만 사용
2. **Entity는 ID로 식별, Value Object는 값으로 식별**
3. **Repository는 인터페이스(ABC)로 정의, Infrastructure에서 구현**
4. **도메인 이벤트는 과거형으로 명명** - `WorkOrderCreated`, `StatusChanged`

## 레이어 구조

```
src/
├── domain/           # 핵심 비즈니스 로직 (의존성 없음)
├── application/      # 유스케이스 (domain만 의존)
├── infrastructure/   # 외부 의존성 구현
└── api/             # 프레젠테이션 (FastAPI)
```

## Value Object

불변, 값으로 비교되는 객체. 비즈니스 규칙을 캡슐화.

```python
from dataclasses import dataclass
from typing import Optional
import re

@dataclass(frozen=True)  # frozen=True로 불변성 보장
class LotNumber:
    """LOT 번호 값 객체."""
    
    value: str
    
    def __post_init__(self):
        """생성 시 유효성 검사."""
        if not self.value:
            raise ValueError("LOT number cannot be empty")
        if len(self.value) > 50:
            raise ValueError("LOT number too long")
        if not re.match(r'^[A-Za-z0-9\-_]+$', self.value):
            raise ValueError("Invalid characters in LOT number")
    
    def __str__(self) -> str:
        return self.value
    
    def __eq__(self, other) -> bool:
        if isinstance(other, LotNumber):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other
        return False


@dataclass(frozen=True)
class Quantity:
    """수량 값 객체 (음수 불가)."""
    
    value: int
    
    def __post_init__(self):
        if self.value < 0:
            raise ValueError("Quantity cannot be negative")
    
    def __add__(self, other: "Quantity") -> "Quantity":
        return Quantity(self.value + other.value)
    
    @classmethod
    def zero(cls) -> "Quantity":
        return cls(0)
```

**Value Object 사용 시점:**
- 비즈니스 규칙이 있는 값 (LOT 번호 형식, 수량 범위)
- 동등성이 값 기반 (두 LOT 번호가 같으면 같은 객체)
- 불변성이 필요한 경우

## Entity

ID로 식별되는 객체. 생명주기와 상태 변화가 있음.

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

@dataclass
class WorkOrderEntity:
    """작업지시 엔티티 (Aggregate Root)."""
    
    # Identity
    id: Optional[int] = None
    lot_no: LotNumber = field(default_factory=lambda: LotNumber("NEW"))
    
    # State
    status: WorkOrderStatus = WorkOrderStatus.READY
    target_qty: Quantity = field(default_factory=lambda: Quantity(1))
    completed_qty: Quantity = field(default_factory=Quantity.zero)
    
    # Domain events
    _domain_events: List = field(default_factory=list, repr=False)
    
    # =========================================================================
    # Business Methods (도메인 로직 캡슐화)
    # =========================================================================
    
    def start(self) -> None:
        """작업 시작."""
        if not self.status.can_transition_to(WorkOrderStatus.RUNNING):
            raise ValueError(f"Cannot start from {self.status}")
        
        old_status = self.status
        self.status = WorkOrderStatus.RUNNING
        self.start_time = datetime.now(timezone.utc)
        
        # 도메인 이벤트 발행
        self._add_event(WorkOrderStatusChanged(
            work_order_id=self.id,
            old_status=old_status.value,
            new_status=self.status.value,
        ))
    
    def record_production(self, ok_qty: int, ng_qty: int = 0) -> None:
        """생산 실적 기록."""
        self.completed_qty = Quantity(self.completed_qty.value + ok_qty)
        
        # 자동 완료 로직
        if self.completed_qty.value >= self.target_qty.value:
            if self.status == WorkOrderStatus.RUNNING:
                self.complete()
    
    # =========================================================================
    # Computed Properties
    # =========================================================================
    
    @property
    def progress_percent(self) -> float:
        """완료율 계산."""
        if self.target_qty.value == 0:
            return 0.0
        return (self.completed_qty.value / self.target_qty.value) * 100
    
    # =========================================================================
    # Domain Events
    # =========================================================================
    
    def _add_event(self, event) -> None:
        self._domain_events.append(event)
    
    def collect_events(self) -> List:
        """이벤트 수집 후 클리어."""
        events = self._domain_events.copy()
        self._domain_events.clear()
        return events
```

**Entity 설계 원칙:**
- 비즈니스 메서드로 상태 변경 (setter 대신)
- 불변식(invariant) 보장 (항상 유효한 상태)
- 도메인 이벤트로 부수 효과 알림

## Repository Interface

영속성 추상화. Domain에서 인터페이스 정의, Infrastructure에서 구현.

```python
from abc import ABC, abstractmethod
from typing import Optional, List

class WorkOrderRepository(ABC):
    """작업지시 Repository 인터페이스."""
    
    @abstractmethod
    async def get_by_id(self, work_order_id: int) -> Optional[WorkOrderEntity]:
        """ID로 조회."""
        pass
    
    @abstractmethod
    async def get_by_lot_no(self, lot_no: LotNumber) -> Optional[WorkOrderEntity]:
        """LOT 번호로 조회."""
        pass
    
    @abstractmethod
    async def save(self, work_order: WorkOrderEntity) -> WorkOrderEntity:
        """저장 (생성 또는 업데이트)."""
        pass
    
    @abstractmethod
    async def find_by_status(
        self,
        status: WorkOrderStatus,
        limit: int = 100,
    ) -> List[WorkOrderEntity]:
        """상태별 조회."""
        pass
    
    @abstractmethod
    async def exists_lot_no(self, lot_no: LotNumber) -> bool:
        """LOT 번호 존재 여부."""
        pass
```

**Repository 구현 (Infrastructure):**

```python
# infrastructure/persistence/sqlalchemy/repositories.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

class SQLAlchemyWorkOrderRepository(WorkOrderRepository):
    """SQLAlchemy 기반 Repository 구현."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, work_order_id: int) -> Optional[WorkOrderEntity]:
        result = await self.session.execute(
            select(WorkOrderModel).where(WorkOrderModel.id == work_order_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def save(self, entity: WorkOrderEntity) -> WorkOrderEntity:
        model = self._to_model(entity)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)
    
    def _to_entity(self, model: WorkOrderModel) -> WorkOrderEntity:
        """ORM 모델 → 도메인 엔티티."""
        return WorkOrderEntity(
            id=model.id,
            lot_no=LotNumber(model.lot_no),
            status=WorkOrderStatus(model.status),
            target_qty=Quantity(model.target_qty),
            # ...
        )
    
    def _to_model(self, entity: WorkOrderEntity) -> WorkOrderModel:
        """도메인 엔티티 → ORM 모델."""
        return WorkOrderModel(
            id=entity.id,
            lot_no=str(entity.lot_no),
            status=entity.status.value,
            target_qty=entity.target_qty.value,
            # ...
        )
```

## Domain Event

도메인에서 발생한 중요한 사건. 과거형으로 명명.

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass(frozen=True)
class WorkOrderCreated:
    """작업지시 생성 이벤트."""
    
    work_order_id: int
    lot_no: str
    product_id: int
    target_qty: int
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    @property
    def event_type(self) -> str:
        return "work_order.created"


@dataclass(frozen=True)
class ProductionRecorded:
    """생산 실적 기록 이벤트."""
    
    work_order_id: int
    ok_qty: int
    ng_qty: int
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    @property
    def event_type(self) -> str:
        return "production.recorded"
```

## Application Layer (Use Cases)

Command, Query, Handler 패턴으로 유스케이스 구현.

```python
# application/production/commands.py
@dataclass(frozen=True)
class CreateWorkOrderCommand:
    """작업지시 생성 명령."""
    
    lot_no: str
    product_id: int
    target_qty: int
    priority: int = 50
    
    def validate(self) -> None:
        if not self.lot_no:
            raise ValueError("LOT number required")
        if self.target_qty <= 0:
            raise ValueError("Target qty must be positive")


# application/production/handlers.py
class CreateWorkOrderHandler:
    """작업지시 생성 핸들러."""
    
    def __init__(self, repository: WorkOrderRepository):
        self.repository = repository
    
    async def handle(self, command: CreateWorkOrderCommand) -> WorkOrderEntity:
        command.validate()
        
        # 중복 체크
        lot_no = LotNumber(command.lot_no)
        if await self.repository.exists_lot_no(lot_no):
            raise DuplicateLotNumberError(command.lot_no)
        
        # 엔티티 생성
        work_order = WorkOrderEntity(
            lot_no=lot_no,
            product_id=command.product_id,
            target_qty=Quantity(command.target_qty),
        )
        
        # 저장
        return await self.repository.save(work_order)
```

## 의존성 주입

```python
# api/deps.py
from functools import lru_cache

def get_work_order_repository(db: AsyncSession) -> WorkOrderRepository:
    return SQLAlchemyWorkOrderRepository(db)

def get_create_handler(
    repository: WorkOrderRepository = Depends(get_work_order_repository)
) -> CreateWorkOrderHandler:
    return CreateWorkOrderHandler(repository)


# api/endpoints/production.py
@router.post("/orders")
async def create_work_order(
    command: CreateWorkOrderCommand,
    handler: CreateWorkOrderHandler = Depends(get_create_handler),
):
    return await handler.handle(command)
```

## Anti-patterns

```python
# ❌ Entity에서 직접 DB 접근
class WorkOrderEntity:
    def save(self):
        db.session.add(self)  # 안 됨!

# ❌ Domain에서 외부 라이브러리 사용
from sqlalchemy import Column  # domain에서 사용 금지

# ❌ Value Object를 mutable로 만들기
@dataclass  # frozen=True 없음!
class Quantity:
    value: int

# ❌ Anemic Domain Model (getter/setter만 있는 Entity)
class WorkOrder:
    def get_status(self): return self._status
    def set_status(self, s): self._status = s  # 비즈니스 로직 없음
```

## 마이그레이션 전략

기존 코드에서 DDD로 점진적 전환:

1. **Value Object부터 시작**: 가장 작은 단위, 테스트 용이
2. **Entity 추출**: 기존 ORM 모델과 병행 운영
3. **Repository 인터페이스**: 기존 쿼리를 인터페이스 뒤로
4. **Application Layer**: 엔드포인트 로직을 Handler로 이동
5. **기존 API 유지**: 내부 구현만 변경, 외부 인터페이스 유지

## 관련 스킬

- [clean_architecture.md](clean_architecture.md) - 클린 아키텍처 원칙
- [event_driven.md](event_driven.md) - 이벤트 기반 패턴
- [test_driven_updates.md](test_driven_updates.md) - TDD 적용
