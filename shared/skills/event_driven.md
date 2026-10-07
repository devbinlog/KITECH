# Event-Driven Architecture

이벤트 기반 비동기 통신 패턴과 agents-workspace에서의 적용.

## Critical Rules

1. **이벤트는 과거형으로 명명** - `OrderCreated`, `StatusChanged`
2. **이벤트는 불변** - `frozen=True` 사용
3. **발행자는 구독자를 모름** - 느슨한 결합
4. **이벤트 유실에 대비** - 멱등성 보장

## 이벤트 모델

### Base Event

```python
# shared/events/base.py
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field

class EventMetadata(BaseModel):
    """모든 이벤트에 포함되는 메타데이터."""
    
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_service: str = ""
    correlation_id: Optional[str] = None  # 연관 이벤트 추적
    causation_id: Optional[str] = None    # 원인 이벤트


class Event(BaseModel):
    """이벤트 기본 클래스."""
    
    model_config = ConfigDict(frozen=True)  # 불변
    
    event_type: str = "base.event"
    metadata: EventMetadata = Field(default_factory=EventMetadata)
    
    def to_channel(self) -> str:
        """Redis 채널명 생성."""
        return f"events:{self.event_type}"
```

### Domain Events

```python
# shared/events/production.py

class WorkOrderCreatedEvent(Event):
    """작업지시 생성 이벤트."""
    
    model_config = ConfigDict(frozen=True)
    event_type: str = "work_order.created"
    
    work_order_id: int
    lot_no: str
    product_id: int
    target_qty: int
    priority: int = 50


class WorkOrderStatusChangedEvent(Event):
    """작업지시 상태 변경 이벤트."""
    
    model_config = ConfigDict(frozen=True)
    event_type: str = "work_order.status_changed"
    
    work_order_id: int
    lot_no: str
    previous_status: str
    new_status: str
```

## Event Bus

### Redis Pub/Sub 기반

```python
# shared/events/bus.py
import redis.asyncio as redis

class EventBus:
    """Redis 기반 이벤트 버스."""
    
    def __init__(self, redis_url: str, source_service: str = ""):
        self.redis_url = redis_url
        self.source_service = source_service
        self._handlers: Dict[str, List[Callable]] = {}
    
    async def connect(self) -> None:
        """Redis 연결."""
        self._client = redis.from_url(self.redis_url)
        self._pubsub = self._client.pubsub()
        await self._client.ping()
    
    async def publish(self, event: Event) -> int:
        """이벤트 발행."""
        if self.source_service:
            event = event.with_source(self.source_service)
        
        channel = event.to_channel()
        message = event.model_dump_json()
        return await self._client.publish(channel, message)
    
    def subscribe(self, event_type: str, handler: Callable) -> None:
        """이벤트 구독."""
        channel = f"events:{event_type}"
        if channel not in self._handlers:
            self._handlers[channel] = []
        self._handlers[channel].append(handler)
    
    async def start_listening(self) -> None:
        """이벤트 리스닝 시작."""
        channels = list(self._handlers.keys())
        await self._pubsub.subscribe(*channels)
        
        async for message in self._pubsub.listen():
            if message["type"] == "message":
                await self._handle_message(message)
```

## 이벤트 발행 패턴

### Entity에서 이벤트 수집

```python
# domain/production/entities.py

@dataclass
class WorkOrderEntity:
    _domain_events: List = field(default_factory=list, repr=False)
    
    def start(self) -> None:
        old_status = self.status
        self.status = WorkOrderStatus.RUNNING
        
        # 이벤트 추가
        self._domain_events.append(WorkOrderStatusChangedEvent(
            work_order_id=self.id,
            lot_no=str(self.lot_no),
            previous_status=old_status.value,
            new_status=self.status.value,
        ))
    
    def collect_events(self) -> List[Event]:
        """이벤트 수집 후 클리어."""
        events = self._domain_events.copy()
        self._domain_events.clear()
        return events
```

### Handler에서 이벤트 발행

```python
# application/production/handlers.py

class CreateWorkOrderHandler:
    def __init__(
        self,
        repository: WorkOrderRepository,
        event_bus: EventBus,
    ):
        self.repository = repository
        self.event_bus = event_bus
    
    async def handle(self, command: CreateWorkOrderCommand) -> WorkOrderEntity:
        # 엔티티 생성 및 저장
        entity = WorkOrderEntity(...)
        saved = await self.repository.save(entity)
        
        # 이벤트 발행
        event = WorkOrderCreatedEvent(
            work_order_id=saved.id,
            lot_no=str(saved.lot_no),
            product_id=saved.product_id,
            target_qty=saved.target_qty.value,
        )
        await self.event_bus.publish(event)
        
        return saved
```

### Fire-and-Forget 패턴

```python
# services/event_publisher.py

class EventPublisher:
    """비동기 이벤트 발행 (요청 블로킹 없음)."""
    
    def publish_fire_and_forget(self, event: Event) -> None:
        """이벤트 발행을 백그라운드로 스케줄."""
        try:
            asyncio.create_task(self._publish_async(event))
        except RuntimeError:
            # 이벤트 루프 없음 (무시)
            pass
    
    async def _publish_async(self, event: Event) -> None:
        try:
            await self.event_bus.publish(event)
        except Exception as e:
            logger.warning(f"Failed to publish event: {e}")
            # 발행 실패 시 로깅만 (요청 실패 안 함)
```

## 이벤트 구독 패턴

### 이벤트 핸들러

```python
# application/event_handlers.py

class ScheduleOnWorkOrderCreated:
    """작업지시 생성 시 재스케줄링 트리거."""
    
    def __init__(self, scheduler_client: SchedulerClient):
        self.scheduler_client = scheduler_client
    
    async def handle(self, event: WorkOrderCreatedEvent) -> None:
        logger.info(f"New work order: {event.lot_no}")
        await self.scheduler_client.trigger_reschedule()


class UpdateDashboardOnStatusChange:
    """상태 변경 시 대시보드 업데이트."""
    
    async def handle(self, event: WorkOrderStatusChangedEvent) -> None:
        # WebSocket으로 클라이언트에 알림
        await self.broadcast({
            "type": "status_change",
            "lot_no": event.lot_no,
            "new_status": event.new_status,
        })
```

### 구독 설정

```python
# main.py

async def setup_event_handlers(event_bus: EventBus):
    """이벤트 핸들러 등록."""
    
    # 작업지시 생성 이벤트
    event_bus.subscribe(
        "work_order.created",
        ScheduleOnWorkOrderCreated(scheduler_client).handle
    )
    
    # 상태 변경 이벤트
    event_bus.subscribe(
        "work_order.status_changed",
        UpdateDashboardOnStatusChange().handle
    )
    
    # 패턴 구독 (모든 work_order 이벤트)
    event_bus.subscribe_pattern(
        "work_order.*",
        AuditLogger().handle
    )
```

## 이벤트 흐름

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│   Cell-MES    │     │     Redis     │     │   Scheduler   │
└───────┬───────┘     └───────┬───────┘     └───────┬───────┘
        │                     │                     │
        │ 1. Create WO        │                     │
        ├────────────────────►│                     │
        │                     │                     │
        │ 2. publish          │                     │
        │ work_order.created  │                     │
        ├────────────────────►│                     │
        │                     │ 3. notify           │
        │                     ├────────────────────►│
        │                     │                     │
        │                     │ 4. trigger          │
        │                     │    reschedule       │
        │                     │◄────────────────────┤
        │                     │                     │
        │ 5. schedule.completed                     │
        │◄────────────────────┼─────────────────────┤
        │                     │                     │
```

## 이벤트 스키마 버전 관리

```python
class Event(BaseModel):
    metadata: EventMetadata = Field(default_factory=EventMetadata)

class EventMetadata(BaseModel):
    version: int = 1  # 스키마 버전


# 버전별 처리
async def handle_event(event: Event):
    if event.metadata.version == 1:
        handle_v1(event)
    elif event.metadata.version == 2:
        handle_v2(event)
    else:
        logger.warning(f"Unknown version: {event.metadata.version}")
```

## 멱등성 보장

```python
class IdempotentEventHandler:
    """중복 이벤트 처리 방지."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def handle(self, event: Event) -> bool:
        """이벤트 처리 (이미 처리된 경우 스킵)."""
        event_id = event.metadata.event_id
        key = f"processed:{event_id}"
        
        # SET NX (이미 있으면 실패)
        if not await self.redis.setnx(key, "1"):
            logger.info(f"Skipping duplicate event: {event_id}")
            return False
        
        # TTL 설정 (7일 후 만료)
        await self.redis.expire(key, 7 * 24 * 3600)
        
        return True
```

## 에러 처리

### Dead Letter Queue

```python
class EventBusWithDLQ(EventBus):
    """DLQ 지원 이벤트 버스."""
    
    async def _handle_message(self, message: dict) -> None:
        channel = message["channel"]
        handlers = self._handlers.get(channel, [])
        
        for handler in handlers:
            try:
                await handler(message)
            except Exception as e:
                logger.exception(f"Handler error: {e}")
                # DLQ로 이동
                await self._send_to_dlq(message, str(e))
    
    async def _send_to_dlq(self, message: dict, error: str) -> None:
        dlq_message = {
            "original": message,
            "error": error,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await self._client.lpush("events:dlq", json.dumps(dlq_message))
```

### Retry 패턴

```python
class RetryingEventHandler:
    """재시도 로직이 있는 핸들러."""
    
    def __init__(self, max_retries: int = 3, delay: float = 1.0):
        self.max_retries = max_retries
        self.delay = delay
    
    async def handle_with_retry(self, event: Event, handler: Callable) -> None:
        for attempt in range(self.max_retries):
            try:
                await handler(event)
                return
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                logger.warning(f"Retry {attempt + 1}/{self.max_retries}: {e}")
                await asyncio.sleep(self.delay * (attempt + 1))
```

## 테스트

```python
# tests/test_event_handlers.py

class TestWorkOrderEventHandler:
    @pytest.fixture
    def mock_event_bus(self):
        return AsyncMock(spec=EventBus)
    
    async def test_publish_on_create(self, mock_event_bus):
        handler = CreateWorkOrderHandler(
            repository=InMemoryRepository(),
            event_bus=mock_event_bus,
        )
        
        await handler.handle(CreateWorkOrderCommand(...))
        
        mock_event_bus.publish.assert_called_once()
        event = mock_event_bus.publish.call_args[0][0]
        assert event.event_type == "work_order.created"
```

## 이벤트 카탈로그

| Event Type | Publisher | Consumers | Description |
|------------|-----------|-----------|-------------|
| `work_order.created` | Cell-MES | Scheduler, Dashboard | 작업지시 생성 |
| `work_order.status_changed` | Cell-MES | Dashboard, Analytics | 상태 변경 |
| `production.recorded` | Cell-MES | Analytics, Quality | 생산실적 |
| `schedule.completed` | Scheduler | Cell-MES, Dashboard | 스케줄링 완료 |
| `inspection.completed` | Cell-MES | Quality, Analytics | 검사 완료 |

## Anti-patterns

```python
# ❌ 이벤트 내용 변경
event.work_order_id = 123  # 불변이어야 함!

# ❌ 발행자가 구독자 알기
if scheduler_is_running:
    event_bus.publish(event)  # 구독자 상태 체크 안 됨

# ❌ 동기식 이벤트 처리
await event_bus.publish_and_wait(event)  # 블로킹 안 됨

# ❌ 이벤트에 너무 많은 데이터
class OrderCreated(Event):
    order: CompleteOrderWithAllRelations  # 필요한 것만!
```

## 관련 스킬

- [ddd_patterns.md](ddd_patterns.md) - 도메인 이벤트
- [clean_architecture.md](clean_architecture.md) - 레이어 분리
- [service_management.md](service_management.md) - 서비스 통신
