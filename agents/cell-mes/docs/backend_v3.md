# [MES] 백엔드 설계 명세서 (v3.0)

> **📌 Historical document (2026-05-03)**
>
> 본 문서는 v3.0 시점(초기 설계)의 스냅샷입니다. 현재 코드베이스는 service-oriented 단일 layer로
> 운영 중이며, DDD `domain/` / `application/` / `infrastructure/` 디렉토리는 사용된 적이 없거나
> commit `7ae4c39`에서 제거되었습니다.
>
> 현재 services/ 디렉토리는 본 문서의 2개에서 ~15개로 확장:
> `aggregation_service`, `dispatch_service`, `polling_service`, `sync_service`, `quality_service`,
> `scenario_converter`, `scheduler_integration`, `n8n_runner`, `event_publisher`, `nlm_retriever/`, etc.
>
> 최신 구조는 `agents/cell-mes/src/app/` 디렉토리 직접 탐색 권고.

## 1. 개요 (Overview)
* **Version:** 3.0
* **Framework:** Python 3.10+ / FastAPI
* **Database:** PostgreSQL (Async SQLAlchemy + Alembic)
* **Deployment:** Windows Native (Standalone / Docker Support)
* **설계 목표:** AAS 기반의 유연한 장비 연동(Plug & Play)과 표준 공정 기반의 정밀 생산 관리를 지원하는 고성능 백엔드 구축.
* **핵심 기능:**
    * **AAS 기반 장비 동기화:** 미들웨어로부터 장비 리스트를 받아와 DB를 자동 갱신(Asset Discovery).
    * **데이터 구조 유연화:** `JSONB` 타입을 도입하여 CNC, 로봇, PLC 등 이기종 장비 데이터 통합 관리.
    * **NC 파일 다중 처리:** 1개 공정에 다중 파일(NC, 도면) 매핑 지원.
    * **물류 시나리오 분리:** 가공(Routing)과 물류(Scenario) 로직의 명확한 분리 및 통합 지시.
    * **테스트 주도 안정성:** 상태 머신, 데이터 파싱, 동기화 로직에 대한 정밀 유닛 테스트 수행.

---

## 2. 프로젝트 구조 (Directory Structure)

```text
backend/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/       # API 라우터 (Controller)
│   │   │   │   ├── auth.py      # 로그인, 토큰 관리
│   │   │   │   ├── users.py     # 사용자 관리 (CRUD)
│   │   │   │   ├── system.py    # 미들웨어 설정 관리
│   │   │   │   ├── masters.py   # 품목, 공정, 설비(Sync) 관리
│   │   │   │   ├── routings.py  # 공정 라우팅 및 파일 매핑
│   │   │   │   ├── scenarios.py # 물류/로봇 시나리오 관리
│   │   │   │   └── production.py # 작업지시, 실적, 장비폴링
│   │   │   └── api.py           # 라우터 통합 설정
│   ├── core/
│   │   ├── config.py            # 환경변수 로드 (.env)
│   │   └── security.py          # JWT 생성 및 Hashing
│   ├── db/
│   │   ├── session.py           # DB Session (Async)
│   │   └── base.py              # Base Model
│   ├── models/                  # DB Models (SQLAlchemy)
│   │   ├── user.py
│   │   ├── system.py
│   │   ├── master.py            # 기준정보 (AAS Equipment, RoutingFile)
│   │   └── production.py        # 생산실적 및 지시
│   ├── schemas/                 # Pydantic Schemas
│   │   ├── common.py            # 공통 Response 형태
│   │   ├── token.py             # Auth Token
│   │   ├── master.py            # 기준정보 스키마 (JSONB 포함)
│   │   └── production.py        # 생산 관련 스키마
│   ├── services/                # Business Logic (Core)
│   │   ├── machine_service.py   # AAS 동기화, 폴링, 데이터 파싱
│   │   └── order_service.py     # 작업지시 상태 전이, Payload 조립
│   └── main.py                  # App Entry Point
├── tests/                       # Unit Tests
│   ├── __init__.py
│   ├── conftest.py              # Pytest Fixtures
│   ├── test_orders.py           # 작업지시 상태/Payload 검증
│   ├── test_parsing.py          # 장비 데이터 파싱 로직 검증
│   └── test_sync.py             # AAS 동기화 로직 검증
├── alembic/                     # DB Migrations
├── requirements.txt
└── .env

```

---

## 3. 데이터베이스 모델 (SQLAlchemy Models)

### 3.1. 시스템 및 사용자 (`app/models/user.py`, `system.py`)

```python
# app/models/user.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.db.base import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="OPERATOR") # ADMIN, OPERATOR
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

# app/models/system.py
class MiddlewareConfig(Base):
    __tablename__ = "middleware_config"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    ip_address = Column(String(50), nullable=False)
    port = Column(Integer, nullable=False)
    is_connected = Column(Boolean, default=False)

```

### 3.2. 기준 정보 (`app/models/master.py`)

```python
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class StdProcess(Base):
    __tablename__ = "std_processes"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    unit = Column(String(10), default="EA")
    
    routings = relationship("ProcessRouting", back_populates="product", cascade="all, delete-orphan")
    scenarios = relationship("Scenario", back_populates="product")

class ProcessRouting(Base):
    __tablename__ = "process_routings"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    std_process_id = Column(Integer, ForeignKey("std_processes.id"), nullable=False)
    sequence = Column(Integer, nullable=False)
    
    product = relationship("Product", back_populates="routings")
    std_process = relationship("StdProcess")
    files = relationship("ProcessRoutingFile", back_populates="routing", cascade="all, delete-orphan")
    
    __table_args__ = (UniqueConstraint('product_id', 'sequence', name='uq_routing_seq'),)

class ProcessRoutingFile(Base):
    __tablename__ = "process_routing_files"
    id = Column(Integer, primary_key=True, index=True)
    process_routing_id = Column(Integer, ForeignKey("process_routings.id"), nullable=False)
    file_type = Column(String(20), default="NC") # NC, IMG, PDF
    file_path = Column(String(255), nullable=False)
    sort_order = Column(Integer, default=1)
    
    routing = relationship("ProcessRouting", back_populates="files")

class Scenario(Base):
    __tablename__ = "scenarios"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    name = Column(String(100), nullable=False)
    file_path = Column(String(255), nullable=False) # 로봇 제어용 YAML
    is_active = Column(Boolean, default=True)
    
    product = relationship("Product", back_populates="scenarios")

class Equipment(Base):
    """설비 관리 (AAS & JSONB 적용)"""
    __tablename__ = "equipments"
    id = Column(Integer, primary_key=True, index=True)
    aas_id = Column(String(100), unique=True, nullable=True) # AAS 식별자
    eq_name = Column(String(100), nullable=False)
    model_name = Column(String(100), nullable=True)
    equipment_type = Column(String(20), nullable=False, default="CNC")
    
    connection_config = Column(JSONB, nullable=False, default={}) # IP, Port
    spec_data = Column(JSONB, default={})        # 고정 스펙 (제조사, 축 수 등)
    last_data = Column(JSONB, default={})        # 실시간 데이터
    
    current_status = Column(String(20), default="STOP")
    last_connected_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False)

```

### 3.3. 생산 관리 (`app/models/production.py`)

```python
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class WorkOrder(Base):
    __tablename__ = "work_orders"
    id = Column(BigInteger, primary_key=True, index=True)
    lot_no = Column(String(50), unique=True, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"))
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))
    target_qty = Column(Integer, nullable=False)
    status = Column(String(20), default="READY")
    created_at = Column(DateTime, server_default=func.now())

    product = relationship("Product")
    scenario = relationship("Scenario")
    prod_results = relationship("ProdResult", back_populates="work_order")

class ProdResult(Base):
    __tablename__ = "prod_results"
    id = Column(BigInteger, primary_key=True, index=True)
    work_order_id = Column(BigInteger, ForeignKey("work_orders.id"))
    equipment_id = Column(Integer, ForeignKey("equipments.id"))
    process_routing_id = Column(Integer, ForeignKey("process_routings.id"))
    
    ok_qty = Column(Integer, default=0)
    ng_qty = Column(Integer, default=0)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)

    work_order = relationship("WorkOrder", back_populates="prod_results")
    equipment = relationship("Equipment")

```

---

## 4. Pydantic 스키마 (Schemas)

### 4.1. 공통 및 기준 정보

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# Common
class ResponseSchema(BaseModel):
    success: bool = True
    message: str = ""
    data: Optional[Any] = None

# Routing File
class RoutingFileSchema(BaseModel):
    file_type: str
    file_path: str
    sort_order: int

# Routing (Nested)
class RoutingSchema(BaseModel):
    std_process_id: int
    sequence: int
    files: List[RoutingFileSchema] = []

# Scenario
class ScenarioSchema(BaseModel):
    name: str
    file_path: str
    is_active: bool

# Equipment (AAS)
class EquipmentSchema(BaseModel):
    aas_id: Optional[str]
    eq_name: str
    model_name: Optional[str]
    equipment_type: str
    connection_config: Dict[str, Any]
    spec_data: Dict[str, Any]

class EquipmentResponse(EquipmentSchema):
    id: int
    current_status: str
    last_data: Optional[Dict[str, Any]]
    last_connected_at: Optional[datetime]
    class Config:
        from_attributes = True

```

---

## 5. API 명세 (API Endpoints) - [상세 명세]

### 5.1. 인증 및 사용자 (Auth & Users)

* **POST** `/api/v1/auth/login`: 사용자 로그인 (JWT Access Token 발급).
* **POST** `/api/v1/users/`: 신규 사용자 등록 (Admin Only).
* **GET** `/api/v1/users/`: 전체 사용자 목록 조회.
* **PATCH** `/api/v1/users/{user_id}/role`: 사용자 권한(Role) 변경.

### 5.2. 시스템 설정 (System)

* **GET** `/api/v1/system/middleware`: 등록된 미들웨어 서버 목록 조회.
* **POST** `/api/v1/system/middleware`: 신규 미들웨어 서버 정보 등록.
* **POST** `/api/v1/system/middleware/{id}/test`: 미들웨어 연결 테스트 (Ping).

### 5.3. 기준 정보 - 품목 및 라우팅 (Masters)

* **GET** `/api/v1/masters/products`: 전체 품목 목록 조회.
* **POST** `/api/v1/masters/products`: 신규 품목 등록.
* **GET** `/api/v1/masters/products/{id}/routings`: 특정 품목의 **공정 라우팅 및 파일 리스트** 조회.
* **PUT** `/api/v1/masters/products/{id}/routings`: 특정 품목의 라우팅 정보 **일괄 수정**.
* *Payload:* `[ { "std_process_id": 1, "sequence": 10, "files": [...] }, ... ]`
* *Note:* 기존 라우팅을 삭제하고 새로 입력된 순서대로 재생성 (Transaction).



### 5.4. 기준 정보 - 시나리오 (Scenarios)

* **GET** `/api/v1/masters/scenarios`: 전체 시나리오 목록 조회 (품목 필터링 가능).
* **POST** `/api/v1/masters/scenarios`: 신규 물류 시나리오 등록.
* *Payload:* `{ "product_id": 1, "name": "AGV Route A", "file_path": "/robot/path_a.yaml" }`


* **PATCH** `/api/v1/masters/scenarios/{id}/active`: 시나리오 활성/비활성 토글.

### 5.5. 기준 정보 - 설비 (Equipments)

* **GET** `/api/v1/masters/equipments`: 설비 목록 조회 (실시간 상태 `last_data` 포함).
* **POST** `/api/v1/masters/equipments/sync`: **[New] 장비 동기화 (Asset Discovery)**.
* *Action:* 미들웨어에 전체 자산 리스트 요청 -> DB 자동 갱신.


* **GET** `/api/v1/masters/equipments/{id}/status`: 특정 설비 상태 즉시 폴링 (Refresh).
* **PUT** `/api/v1/masters/equipments/{id}`: 설비 정보(이름, 위치 등) 수동 수정.

### 5.6. 생산 관리 (Production)

* **POST** `/api/v1/production/orders`: 작업 지시 생성.
* *Payload:* `{ "lot_no": "LOT-100", "product_id": 1, "scenario_id": 3, "target_qty": 50 }`


* **GET** `/api/v1/production/orders`: 작업 지시 목록 조회 (상태 필터링).
* **PATCH** `/api/v1/production/orders/{id}/status`: 지시 상태 변경 (START / PAUSE / STOP).
* *Logic:* START 시 미들웨어로 Payload 전송.


* **GET** `/api/v1/production/middleware/work-info`: **[Machine 연동용]** 작업 정보 조회.
* *Params:* `lot_no`
* *Response:* 가공(Routing+Files) + 물류(Scenario) 통합 JSON.


* **GET** `/api/v1/production/results`: 생산 실적 및 Traceability 로그 조회.

---

## 6. 핵심 비즈니스 로직 (Services Implementation Logic)

### 6.1. AAS 장비 동기화 (`services/machine_service.py`)

```python
async def sync_machines_from_middleware(db: AsyncSession):
    # 1. 미들웨어 API 호출 (전체 자산 리스트)
    # response example: [{"id": "urn:cnc:01", "name": "Milling #1", "spec": {...}}, ...]
    assets = await middleware_client.fetch_all_assets()
    
    synced_count = 0
    for asset in assets:
        # 2. AAS ID로 DB 조회
        stmt = select(Equipment).where(Equipment.aas_id == asset['id'])
        result = await db.execute(stmt)
        existing_eq = result.scalar_one_or_none()
        
        if existing_eq:
            # 3-1. 존재 시: 스펙 및 연결 정보 업데이트 (Update)
            existing_eq.model_name = asset.get('model')
            existing_eq.spec_data = asset.get('spec')
            existing_eq.connection_config = asset.get('connection')
            existing_eq.last_connected_at = func.now()
        else:
            # 3-2. 미존재 시: 신규 장비 등록 (Insert)
            new_eq = Equipment(
                aas_id=asset['id'],
                eq_name=asset['name'],
                equipment_type=asset.get('type', 'CNC'),
                spec_data=asset.get('spec', {}),
                connection_config=asset.get('connection', {}),
                last_connected_at=func.now()
            )
            db.add(new_eq)
        synced_count += 1
    
    await db.commit()
    return {"synced_count": synced_count}

```

### 6.2. 장비 상태 폴링 및 파싱 (`services/machine_service.py`)

```python
async def poll_equipment_status(db: AsyncSession, equipment_id: int):
    # 1. 대상 설비 및 연결 정보 조회
    eq = await get_equipment(db, equipment_id)
    
    # 2. 장비(미들웨어)에 실시간 상태 요청
    raw_data = await middleware_client.get_status(eq.connection_config)
    
    # 3. 장비 타입별 파싱 전략 (Strategy Pattern)
    parsed_data = {}
    current_status = "STOP"
    
    if eq.equipment_type == "CNC":
        parsed_data = {
            "rpm": raw_data.get("spindle_rpm"),
            "load": raw_data.get("load_percent"),
            "temp": raw_data.get("temperature"),
            "alarm_code": raw_data.get("alarm")
        }
        current_status = "ERROR" if parsed_data["alarm_code"] != "0" else "RUNNING"
        
    elif eq.equipment_type == "ROBOT":
        parsed_data = {
            "joints": raw_data.get("joint_angles"), # [J1, J2, J3...]
            "battery": raw_data.get("battery_level"),
            "is_moving": raw_data.get("is_moving")
        }
        current_status = "RUNNING" if parsed_data["is_moving"] else "STOP"

    # 4. DB 상태 업데이트
    eq.last_data = parsed_data
    eq.current_status = current_status
    eq.updated_at = func.now()
    
    await db.commit()
    return eq

```

### 6.3. 통합 Payload 조립 (`services/order_service.py`)

```python
async def get_work_info_for_middleware(db: AsyncSession, lot_no: str):
    # 1. 작업지시 및 시나리오 조회
    order = await get_order_by_lot(db, lot_no)
    
    # 2. 공정 라우팅 및 매핑된 파일 조회 (Sequence 순)
    routings = await get_routings_with_files(db, order.product_id)
    
    # 3. 통합 Payload 생성
    payload = {
        "job_id": order.lot_no,
        "product_code": order.product.code,
        "quantity": order.target_qty,
        "logistics": {
            "scenario_name": order.scenario.name,
            "control_file": order.scenario.file_path 
        },
        "processing_steps": []
    }
    
    for r in routings:
        step_info = {
            "sequence": r.sequence,
            "process_code": r.std_process.code,
            "files": []
        }
        # 해당 공정에 매핑된 파일 리스트 추가
        for f in r.files:
            step_info["files"].append({
                "type": f.file_type, # NC, IMG
                "path": f.file_path,
                "order": f.sort_order
            })
        payload["processing_steps"].append(step_info)
        
    return payload

```

---

## 7. 상세 테스트 전략 (Detailed Testing Strategy)

`pytest`를 사용하여 핵심 로직의 무결성을 검증합니다.

### 7.1. 작업 지시 상태 관리 테스트 (`test_orders.py`)

* **Test Case 1 (Start Order):**
* *Scenario:* `READY` 상태인 지시에 `start` 액션 요청.
* *Check:* DB 상태가 `RUNNING`으로 변경됨, `start_time` 필드에 현재 시간 기록됨.


* **Test Case 2 (Invalid Transition):**
* *Scenario:* `DONE` 상태인 지시에 `start` 액션 요청.
* *Check:* `HTTP 400 Bad Request` 에러 반환, DB 상태 변경 없음.


* **Test Case 3 (Payload Generation):**
* *Scenario:* 파일이 매핑된 품목의 작업 정보 요청.
* *Check:* 반환된 JSON의 `processing_steps` 내부에 `files` 배열이 존재하고 경로가 정확한지 확인.



### 7.2. 데이터 파싱 및 저장 테스트 (`test_parsing.py`)

* **Test Case 1 (CNC Parsing):**
* *Input:* `{"spindle_rpm": 2000, "alarm": "0"}`
* *Check:* `last_data.rpm` == 2000, `current_status` == "RUNNING".


* **Test Case 2 (Robot Error):**
* *Input:* `{"battery_level": 5, "is_moving": false}`
* *Check:* `last_data.battery` == 5, Low Battery 경고 로그 생성 여부 확인.



### 7.3. AAS 동기화 테스트 (`test_sync.py`)

* **Test Case 1 (Asset Discovery):**
* *Scenario:* DB가 비어있을 때 미들웨어 Mock이 3개의 장비 정보를 반환.
* *Check:* `equipments` 테이블 카운트가 3이어야 함. `aas_id`가 정확히 매핑되었는지 확인.


* **Test Case 2 (Spec Update):**
* *Scenario:* 기존 장비의 스펙 정보가 변경된 경우.
* *Check:* DB 레코드 수는 동일하며, 해당 장비의 `spec_data` JSON 컬럼만 업데이트되었는지 확인.



---

## 8. 배포 및 실행 (Deployment)

1. **Environment:** Python 3.10+, PostgreSQL 15+
2. **Setup:**
```bash
pip install -r requirements.txt

```


3. **Database Init:**
```bash
alembic upgrade head

```


4. **Test Execution:**
```bash
pytest -v

```


5. **Server Start:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

```
