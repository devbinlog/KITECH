# 가상장비 구분 동기화 구현 계획

작성일: 2026-08-05

## 1. 목표

미들웨어 AASX에 가상장비를 추가했을 때, Cell-MES가 미들웨어 `/api/aas/view`에서 장비 목록을 동기화하면서 해당 장비가 **실제장비인지 가상장비인지 구분해서 저장**할 수 있도록 한다.

현재 Cell-MES와 미들웨어 연동은 실제 운전에서 정상 동작 중이므로, 이번 변경의 최우선 원칙은 다음과 같다.

- 기존 실제장비 동기화 동작을 깨지 않는다.
- 기존 미들웨어 Gateway, Status, Commands, Queries 구조를 건드리지 않는다.
- 기존 실제장비 AASX에는 가능하면 변경을 최소화한다.
- 가상장비 여부는 실시간 상태가 아니라 정적 메타데이터로 처리한다.
- DB 변경이 필요한 경우에도 non-destructive migration으로 진행한다.

---

## 2. 현재 구조 확인

### 2.1 미들웨어 AAS View 동작

미들웨어 `/api/aas/view`는 AASX를 사람이 보기 쉬운 구조로 변환해 반환한다.

중요한 동작은 다음과 같다.

| Submodel 유형 | `/api/aas/view` 반환 정책 |
|---|---|
| Gateway submodel (`CncGateway`, `RobotGateway`, `HttpGateway` 등) | `IsConnected`, `Status`만 반환 |
| 일반 submodel | 전체 Property/Collection 반환 |

따라서 가상장비 여부를 Gateway `Status`에 넣는 것은 적절하지 않다.

`Status`는 door, battery, slot, loader count처럼 계속 바뀌는 실시간 값에 사용하는 영역이고, 가상장비 여부는 장비의 정적 속성이기 때문이다.

### 2.2 MES 장비 동기화 동작

Cell-MES 장비 동기화 흐름은 다음과 같다.

```text
POST /api/v1/masters/equipments/sync
  ↓
sync_equipments_from_middleware()
  ↓
middleware_client.fetch_all_assets()
  ↓
GET {MIDDLEWARE_URL}/api/aas/view
  ↓
scheduler_spec_from_asset(asset)
  ↓
Equipment 생성/수정
```

현재 MES는 AAS asset의 `schedulerInfo` submodel을 읽어 `Equipment.spec_data`에 저장할 수 있다.

관련 파일:

- `src/app/services/sync_service.py`
- `src/app/services/aas_scheduler_info.py`
- `src/app/models/equipment.py`
- `src/app/schemas/equipment.py`

### 2.3 현재 Equipment 저장 구조

현재 `equipments` 테이블은 다음 JSON 컬럼을 가지고 있다.

| 컬럼 | 역할 |
|---|---|
| `connection_config` | 연결 정보 |
| `spec_data` | 정적 장비 제원/스펙 |
| `last_data` | 실시간 상태 snapshot |

가상장비 여부는 정적 장비 속성이므로 `spec_data`에 저장하기 적합하다.

다만 화면 필터, 검색, 통계, 쿼리 조건으로 자주 사용하려면 별도 boolean 컬럼이 더 적합하다.

---

## 3. AASX 설계 방안

### 3.1 권장 위치

가상장비 여부는 AASX의 `schedulerInfo` submodel에 추가한다.

```text
AssetAdministrationShell
└─ schedulerInfo
   ├─ machineType
   ├─ isVirtual
   ├─ equipmentSource
   └─ virtualizationType
```

### 3.2 권장 Property

| Property | 타입 | 예시 | 필수 여부 | 설명 |
|---|---|---|---|---|
| `isVirtual` | `xs:boolean` | `true` | 필수 | MES가 가상장비 여부를 판단하는 1차 기준 |
| `equipmentSource` | `xs:string` | `VIRTUAL` | 선택 | 사람이 보기 쉬운 장비 출처 |
| `virtualizationType` | `xs:string` | `SIMULATION` | 선택 | 가상장비 유형. `SIMULATION`, `DIGITAL_TWIN`, `MOCK` 등 |
| `physicalAssetRef` | `xs:string` | `NX5500` | 선택 | 대응되는 실제장비가 있을 경우 참조 |

### 3.3 실제장비에는 값을 넣어야 하는가?

1차 안전 구현에서는 **가상장비에만 `isVirtual=true`를 추가**한다.

실제장비는 기존 AASX를 가능한 한 건드리지 않고, MES에서 값이 없으면 `false`로 해석한다.

| 장비 종류 | AASX 값 | MES 해석 |
|---|---|---|
| 가상장비 | `schedulerInfo.isVirtual = true` | `is_virtual = true` |
| 실제장비 | 값 없음 | `is_virtual = false` |
| 실제장비 | `schedulerInfo.isVirtual = false` | `is_virtual = false` |

장기적으로 AASX 관리 기준을 통일하고 싶다면 실제장비에도 `isVirtual=false`를 명시할 수 있다.

하지만 현재 실제 운전이 잘 되고 있으므로, 초기에는 기존 실제장비 AASX를 건드리지 않는 것이 더 안전하다.

### 3.4 넣지 말아야 할 위치

| 위치 | 비추천 이유 |
|---|---|
| Gateway `Status` | 실시간 상태값 영역이다. 가상장비 여부는 정적 메타데이터다. |
| Gateway `Queries` | 레시피/온디맨드 조회용이다. MES 장비 분류값으로 쓰기 부적절하다. |
| Gateway `Commands` | 동작 명령 영역이다. |
| `DtSimulationProfile` | P4R 시뮬레이션 기준값 영역이다. MES 장비 출처 분류값과 목적이 다르다. |

---

## 4. MES 저장 전략

### 4.1 선택지 비교

| 방식 | 장점 | 단점 | 위험도 |
|---|---|---|---|
| `spec_data["isVirtual"]`만 저장 | DB migration 없음. 가장 안전함. | 목록 필터/검색/통계에서 불편함. | 낮음 |
| `equipments.is_virtual` 컬럼 추가 | 명확한 저장, 빠른 필터, UI 표시 쉬움. | migration 필요. | 중간 |
| 별도 `equipment_metadata` 테이블 추가 | 확장성 높음. | 현재 요구 대비 과함. 구현 범위 큼. | 높음 |

### 4.2 최종 권장안

가장 좋은 구조는 **이중 저장**이다.

```text
원본/확장값: equipments.spec_data["isVirtual"]
자주 쓰는 구분값: equipments.is_virtual
```

즉, AAS에서 넘어온 정적 메타데이터는 `spec_data`에 그대로 보존하고, MES 화면/필터/쿼리에 자주 필요한 `isVirtual`만 별도 컬럼으로 승격한다.

다만 현재 실제 운전 안정성이 중요하므로 구현은 2단계로 나눈다.

---

## 5. 안전한 단계별 구현안

### Phase 1. DB 변경 없는 저위험 반영

목표:

- 기존 동기화 동작을 유지한다.
- 가상장비 여부를 `Equipment.spec_data`에 저장한다.
- 실제장비에는 아무 값이 없어도 `false`로 판단할 수 있게 한다.

구현 내용:

1. AASX 가상장비에 `schedulerInfo.isVirtual=true` 추가
2. MES `scheduler_spec_from_asset()`는 현재처럼 `schedulerInfo`를 flatten
3. `sync_service.py`에서 `scheduler_spec`을 `spec_data`에 병합
4. 가상장비 여부 판단 helper 추가

예시:

```python
def is_virtual_equipment(scheduler_spec: dict) -> bool:
    source = str(scheduler_spec.get("equipmentSource") or "").upper()
    return bool(
        scheduler_spec.get("isVirtual")
        or scheduler_spec.get("is_virtual")
        or source == "VIRTUAL"
    )
```

Phase 1에서는 DB 컬럼을 추가하지 않고, 다음처럼 `spec_data`에 저장한다.

```json
{
  "isVirtual": true,
  "equipmentSource": "VIRTUAL",
  "virtualizationType": "SIMULATION"
}
```

장점:

- DB migration이 없다.
- 현재 컨테이너/DB에 미치는 영향이 가장 작다.
- 기존 실제장비는 값이 없으므로 기존 동작을 유지한다.

한계:

- 장비 목록 필터에서 `is_virtual` 조건을 DB 레벨로 걸기 어렵다.
- 프론트에서 매번 `spec_data.isVirtual`을 해석해야 한다.

### Phase 2. `equipments.is_virtual` 컬럼 추가

목표:

- MES가 가상장비 여부를 정식 필드로 저장한다.
- 장비 목록, 필터, 검색, 스케줄링 제외/포함 조건 등에 쉽게 사용할 수 있게 한다.

DB 변경:

```text
equipments.is_virtual BOOLEAN NOT NULL DEFAULT FALSE
```

모델 변경:

```python
is_virtual: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
```

스키마 변경:

```python
is_virtual: bool = False
```

동기화 변경:

```python
is_virtual = is_virtual_equipment(scheduler_spec)

if existing:
    existing.is_virtual = is_virtual
else:
    equipment = Equipment(..., is_virtual=is_virtual)
```

주의:

- migration은 컬럼 추가만 수행한다.
- 기존 row는 모두 `false`가 기본값이므로 실제장비 동작에 영향이 없다.
- 기존 API 응답에 boolean 필드가 하나 추가되는 변경이므로 프론트 타입도 맞춰야 한다.

### Phase 3. 화면/필터 반영

목표:

- 장비 목록 화면에서 실제장비/가상장비를 구분해서 볼 수 있게 한다.

구현 후보:

- 장비 목록 테이블에 `가상장비` badge 표시
- 필터 추가: `전체`, `실제장비`, `가상장비`
- 장비 상세에 `장비 출처: 실제 / 가상` 표시

주의:

- 초기에는 표시만 하고, 스케줄링/작업지시 배정 로직에서 자동 제외하지 않는다.
- 실제 운영 로직에 영향을 주는 필터링은 별도 요구사항으로 분리한다.

---

## 6. 구현 상세

### 6.1 AASX 가상장비 예시

가상장비에는 다음처럼 `schedulerInfo`를 추가한다.

```json
{
  "idShort": "schedulerInfo",
  "submodelElements": [
    {
      "idShort": "machineType",
      "valueType": "xs:string",
      "value": "CNC"
    },
    {
      "idShort": "isVirtual",
      "valueType": "xs:boolean",
      "value": "true"
    },
    {
      "idShort": "equipmentSource",
      "valueType": "xs:string",
      "value": "VIRTUAL"
    },
    {
      "idShort": "virtualizationType",
      "valueType": "xs:string",
      "value": "SIMULATION"
    }
  ]
}
```

실제장비에는 아무 값도 추가하지 않아도 된다.

### 6.2 대소문자 안전성 보강

현재 `sync_service.py`의 장비 타입 판정은 `cncGateway`, `robotGateway`, `httpGateway`처럼 소문자 key를 기준으로 검사한다.

하지만 미들웨어 `/api/aas/view`는 `CncGateway`, `RobotGateway`, `HttpGateway`처럼 대문자로 시작하는 key를 반환할 수 있다.

가상장비 동기화 구현 시 다음 보강을 같이 하는 것이 좋다.

```python
submodel_keys = {str(key).lower() for key in submodels.keys()}

if "cncgateway" in submodel_keys:
    eq_type = "CNC"
elif "robotgateway" in submodel_keys:
    eq_type = "ROBOT"
elif "httpgateway" in submodel_keys:
    eq_type = "RACK"
```

이 변경은 기존 기능을 해치는 변경이 아니라, 현재 미들웨어 응답 형태를 더 정확히 받아들이는 보정이다.

### 6.3 가상장비 여부 판단 우선순위

MES는 다음 우선순위로 가상장비 여부를 판단한다.

1. `schedulerInfo.isVirtual`
2. `schedulerInfo.is_virtual`
3. `schedulerInfo.equipmentSource == "VIRTUAL"`
4. 값이 없으면 `false`

값 변환 규칙:

| 입력값 | 해석 |
|---|---|
| `true` | true |
| `"true"` | true |
| `1` | true |
| `"1"` | true |
| `"Y"` | true |
| `"YES"` | true |
| `"VIRTUAL"` in `equipmentSource` | true |
| 값 없음 | false |

---

## 7. 테스트 계획

### 7.1 단위 테스트

대상:

- `aas_scheduler_info.py`
- `sync_service.py`

테스트 케이스:

| 테스트 | 기대 결과 |
|---|---|
| `schedulerInfo.isVirtual=true` | `spec_data["isVirtual"] == true` |
| `schedulerInfo.isVirtual` 없음 | 실제장비로 판단 |
| `equipmentSource="VIRTUAL"` | 가상장비로 판단 |
| 기존 schedulerInfo 구조 | 기존 flatten 결과 유지 |
| 기존 실제장비 mock asset | 기존 동기화 결과 유지 |
| `CncGateway` 대문자 key | `equipment_type == "CNC"` |
| `RobotGateway` 대문자 key | `equipment_type == "ROBOT"` |

### 7.2 통합 테스트

1. 로컬 미들웨어 AASX에 가상장비 1개 추가
2. Cell-MES가 로컬 미들웨어를 바라보도록 `MIDDLEWARE_URL=http://host.docker.internal:8100` 설정
3. Cell-MES 컨테이너 recreate
4. `POST /api/v1/masters/equipments/sync` 호출
5. 장비 목록 조회
6. 가상장비가 생성/갱신되었는지 확인
7. 실제장비가 기존처럼 유지되는지 확인

### 7.3 회귀 테스트

기존 실제 운전 기능을 해치지 않았는지 확인한다.

| 확인 항목 | 기대 결과 |
|---|---|
| 미들웨어 AAS view 조회 | 정상 |
| 기존 실제장비 sync | 정상 |
| 기존 장비 status polling | 정상 |
| 작업지시 미들웨어 투입 | 정상 |
| Unit 상태 조회/제어 | 정상 |
| P4R preview 생성 | 정상 |

---

## 8. 배포 전략

### 8.1 가장 안전한 배포 순서

1. 문서/설계 확정
2. AASX 가상장비에만 `schedulerInfo.isVirtual=true` 추가
3. 로컬 미들웨어에서 `/api/aas/view` 응답 확인
4. MES Phase 1 구현: `spec_data` 저장 및 helper/test 추가
5. 기존 장비 sync 회귀 테스트
6. 필요 시 Phase 2 migration 적용
7. 프론트 표시/필터 적용

### 8.2 운영 중 주의사항

- 이미 실제 운전 중인 Cell-MES 컨테이너에 backend 코드를 수정하면 auto reload가 발생할 수 있다.
- DB migration은 실행 시점을 명확히 잡고 적용해야 한다.
- 실장비 AASX는 초기에는 건드리지 않는다.
- `delete_orphans=true` sync는 가상장비 테스트 중 사용하지 않는다.
- 가상장비 추가 후 sync 결과에서 실제장비가 soft-delete되지 않는지 확인한다.

---

## 9. 최종 권장 결론

현재 실제 미들웨어 연동이 정상 운영 중이므로, 가장 좋은 방안은 다음이다.

1. AASX의 가상장비에만 `schedulerInfo.isVirtual=true`를 추가한다.
2. 실제장비 AASX는 건드리지 않는다.
3. MES는 값이 없으면 실제장비(`false`)로 해석한다.
4. 1차 구현은 `spec_data` 저장 중심으로 안전하게 검증한다.
5. 화면 필터/검색/정식 관리가 필요해지는 시점에 `equipments.is_virtual` 컬럼을 추가한다.
6. 컬럼 추가 시에도 기존 row는 모두 `false` default로 두어 기존 실제장비 동작을 유지한다.

이 방식은 현재 정상 동작 중인 MES-미들웨어 실운전 흐름을 최대한 보존하면서, 가상장비 구분 기능을 단계적으로 확장할 수 있다.

---

## 10. MES 내부 복사 기반 가상장비 관리 추가 계획

### 10.1 배경

AASX에 가상장비를 직접 추가하는 방식은 미들웨어/AAS 모델 기준으로는 일관성이 좋지만, 운영 관점에서는 다음 불편이 있다.

- AASX 파일을 수정해야 한다.
- 미들웨어 재시작 또는 AASX 재로드가 필요할 수 있다.
- 가상장비 수량이나 스케줄러 기준값을 바꿀 때마다 MES 밖의 파일을 수정해야 한다.
- 스케줄링 실험을 빠르게 반복하기 어렵다.

따라서 장기적으로는 **AASX 기반 가상장비**와 별개로, MES 화면에서 기존 장비를 복사해 **MES 내부 스케줄링용 가상장비**를 만들고 수정할 수 있게 하는 것이 더 좋다.

이 기능의 목적은 실제 미들웨어 실행 자산을 늘리는 것이 아니라, 스케줄러가 사용할 수 있는 후보 설비를 MES 안에서 빠르게 늘리고 조정하는 것이다.

### 10.2 핵심 원칙

| 원칙 | 설명 |
|---|---|
| AAS 동기화와 분리 | MES 내부 가상장비는 미들웨어 `/api/aas/view`에서 가져온 자산이 아니다. |
| DB migration 없이 1차 구현 | 기존 `spec_data` JSON에 가상장비 메타데이터를 저장한다. |
| 기존 실장비 보호 | 원본 장비의 `aas_id`, `last_data`, `connection_config`를 그대로 복사하지 않는다. |
| 미들웨어 실행과 분리 | MES 내부 가상장비는 작업지시 실행/Unit 제어 대상이 아니다. |
| 스케줄링 후보로만 사용 | 초기 목적은 스케줄러 capacity 실험과 계획 수립이다. |
| 삭제 안전성 보장 | AAS sync의 `delete_orphans=true`가 MES 내부 가상장비를 지우면 안 된다. |

### 10.3 AASX 기반 가상장비와 MES 내부 가상장비 비교

| 구분 | AASX 기반 가상장비 | MES 내부 복사 가상장비 |
|---|---|---|
| 소유 시스템 | 미들웨어/AASX | Cell-MES DB |
| 생성 방식 | AASX 수정 후 미들웨어 재시작/재로드 | MES UI에서 원본 장비 복사 |
| `aas_id` | 있음 | `null` 또는 `mes-virtual://...` |
| 실시간 상태 | AAS view/polling 대상일 수 있음 | 원칙적으로 polling 대상 아님 |
| 스케줄러 사용 | 가능 | 가능 |
| 작업지시 실행 | 원칙적으로 불가 | 불가 |
| 수정 편의성 | 낮음 | 높음 |
| 운영 위험 | AASX/미들웨어에 영향 가능 | MES 내부로 영향 범위 제한 |

### 10.4 최종 권장 구조

1차 구현에서는 DB 컬럼을 추가하지 않고 다음 형태로 저장한다.

```json
{
  "isVirtual": true,
  "equipmentSource": "MES",
  "virtualizationType": "SCHEDULING_COPY",
  "physicalEquipmentId": 18,
  "physicalAssetRef": "https://example.com/ids/aas/DH400",
  "virtualEquipmentGroup": "DH400",
  "machineType": "VMC_3AXIS_PALLET",
  "machineTypeParams": {
    "loadingType": "pallet_single",
    "amrTransportQty": 1,
    "exchangeTimeSec": 0,
    "loadUnloadTimeSec": 30
  }
}
```

권장 DB 저장값:

| 필드 | 값 |
|---|---|
| `eq_name` | `DH400_VIRTUAL_MES_01` 등 사용자가 수정 가능 |
| `eq_code` | `EQ-VIRTUAL-CNC-DH400-01` 등 자동 생성 |
| `aas_id` | 1차 구현에서는 `null` 권장 |
| `equipment_type` | 원본의 상위 타입 복사. 예: `CNC` |
| `model_name` | 원본 model_name 또는 가상장비명 |
| `connection_config` | `{}` |
| `spec_data` | 원본 `spec_data` 복사 후 가상장비 메타데이터 override |
| `last_data` | `{}` |
| `current_status` | `STOP` 또는 `IDLE`. 현재 스케줄러는 `STOP`을 `AVAILABLE`로 본다. |
| `is_deleted` | `false` |

`aas_id`는 nullable unique이므로 SQLite/PostgreSQL 모두 여러 `null`을 허용한다. 따라서 1차 구현에서는 `aas_id=null`이 가장 안전하다. 나중에 외부 시스템 식별자가 필요해지면 `spec_data.virtualId` 또는 별도 컬럼으로 승격한다.

### 10.5 왜 기존 `POST /equipments`만 쓰지 않는가?

현재 수동 등록 API는 임의 장비 생성에는 사용할 수 있지만, 다음을 보장하지 않는다.

- 원본 장비의 스케줄러 관련 필드만 안전하게 복사
- `last_data`, `connection_config`, `aas_id` 같은 실장비 연결값 복사 방지
- 가상장비 이름/코드 중복 방지
- `physicalEquipmentId`, `physicalAssetRef` 자동 기록
- 수량 기반 일괄 생성

따라서 새 기능은 별도 전용 API를 두는 것이 좋다.

### 10.6 백엔드 구현 계획

#### 10.6.1 추가 API

```text
POST /api/v1/masters/equipments/{equipment_id}/virtual-copies
```

역할:

- 원본 장비 1개를 기준으로 MES 내부 가상장비를 1개 이상 생성한다.
- Admin 권한만 허용한다.
- DB migration 없이 기존 `equipments` 테이블에 row를 추가한다.

Request 예시:

```json
{
  "count": 3,
  "name_prefix": "DH400_SIM",
  "machineType": "VMC_3AXIS_PALLET",
  "overrides": {
    "setupChangeTimeMin": 5,
    "machineTypeParams": {
      "loadingType": "pallet_single",
      "amrTransportQty": 1
    }
  }
}
```

Response 예시:

```json
{
  "created_count": 3,
  "created": [
    {
      "id": 31,
      "eq_name": "DH400_SIM_01",
      "equipment_type": "CNC",
      "spec_data": {
        "isVirtual": true,
        "equipmentSource": "MES",
        "physicalEquipmentId": 18
      }
    }
  ]
}
```

#### 10.6.2 추가 Schema

`src/app/schemas/equipment.py`에 추가한다.

```python
class EquipmentVirtualCopyCreate(BaseModel):
    count: int = Field(default=1, ge=1, le=20)
    name_prefix: Optional[str] = Field(default=None, max_length=60)
    machineType: Optional[str] = Field(default=None, max_length=50)
    overrides: Dict[str, Any] = Field(default_factory=dict)


class EquipmentVirtualCopyResult(BaseModel):
    created_count: int
    created: List[EquipmentRead]
```

초기 `count` 상한은 20 정도로 둔다. UI 실수로 수백 개 장비가 생기는 것을 막기 위해서다.

#### 10.6.3 서비스 함수

`src/app/services/equipment_virtual_service.py`를 새로 만든다.

주요 함수:

```python
async def create_virtual_copies(
    db: AsyncSession,
    source_equipment_id: int,
    payload: EquipmentVirtualCopyCreate,
) -> list[Equipment]:
    ...
```

처리 순서:

1. 원본 장비 조회
2. 원본이 없거나 `is_deleted=true`면 404
3. 원본이 이미 가상장비여도 허용할지 정책 결정
   - 1차 권장: 허용하지 않음
   - 이유: 가상장비의 가상장비 복사는 추적이 복잡해진다.
4. 원본 `spec_data` deep copy
5. `overrides`를 허용된 key에만 적용
6. 가상장비 메타데이터 강제 설정
7. `eq_name`, `eq_code` 중복 회피
8. 새 Equipment row 생성
9. commit 후 생성 목록 반환

#### 10.6.4 복사/제외 필드

| 필드 | 처리 |
|---|---|
| `equipment_type` | 원본 복사 |
| `model_name` | 원본 복사 또는 새 이름 |
| `location` | 원본 복사 가능 |
| `cell_id` | 원본 복사 가능 |
| `spec_data` | deep copy 후 override |
| `aas_id` | 복사하지 않음. `null` |
| `connection_config` | 복사하지 않음. `{}` |
| `last_data` | 복사하지 않음. `{}` |
| `last_connected_at` | 복사하지 않음. `null` |
| `current_status` | `STOP` |
| `is_deleted` | `false` |

#### 10.6.5 override 허용 key

초기에는 스케줄러에 필요한 정적 필드만 허용한다.

| Key | 허용 여부 | 이유 |
|---|---|---|
| `machineType` | 허용 | 스케줄러 설비 타입 |
| `setupChangeTimeMin` | 허용 | 셋업 시간 |
| `currentSetupId` | 허용 | 현재 셋업 |
| `machineTypeParams` | 허용 | 로딩/운반 파라미터 |
| `calendar` | 허용 | 근무 가능 시간 |
| `capacity` / `buffer` | 허용 | 버퍼/슬롯 용량 |
| `isVirtual` | 무시/강제 true | 사용자가 false로 바꾸면 안 됨 |
| `equipmentSource` | 무시/강제 MES | 출처 보호 |
| `physicalEquipmentId` | 무시/서버 설정 | 추적 보호 |
| `physicalAssetRef` | 무시/서버 설정 | 추적 보호 |

### 10.7 프론트 구현 계획

#### 10.7.1 진입점

설비 상세 모달의 기본 정보 탭에 다음 버튼을 추가한다.

```text
가상장비 복사
```

표시 조건:

- 선택 장비가 실장비일 때 우선 표시
- 선택 장비가 MES 내부 가상장비이면 1차 구현에서는 숨김
- AASX 기반 가상장비도 복사 원본으로 쓰지 않는 것이 안전하다.

#### 10.7.2 모달 입력 항목

| 항목 | 기본값 |
|---|---|
| 생성 수량 | 1 |
| 이름 Prefix | `{원본 eq_name}_MES_VIRTUAL` |
| Scheduler Machine Type | 원본 `spec_data.machineType` |
| setupChangeTimeMin | 원본 값 |
| loadingType | 원본 `machineTypeParams.loadingType` |
| amrTransportQty | 원본 값 |
| exchangeTimeSec | 원본 값 |
| loadUnloadTimeSec | 원본 값 |

초기 구현에서는 모든 `spec_data`를 편집하게 하지 않고, 자주 쓰는 필드만 form으로 노출한다. 전체 JSON 편집은 오입력 위험이 크므로 2차 기능으로 둔다.

#### 10.7.3 생성 후 UX

1. API 성공
2. `equipments` query invalidate
3. source filter를 `virtual`로 자동 변경
4. 생성된 가상장비가 보이도록 목록 갱신
5. 성공 메시지 표시

### 10.8 AAS sync와 충돌 방지

현재 `sync_service.py`의 orphan 삭제 조건은 다음과 같다.

```python
Equipment.aas_id.isnot(None)
Equipment.aas_id.notin_(middleware_aas_ids)
```

따라서 MES 내부 가상장비를 `aas_id=null`로 만들면 `delete_orphans=true`에도 삭제되지 않는다.

이것이 1차 구현에서 `aas_id=null`을 권장하는 가장 큰 이유다.

나중에 `aas_id="mes-virtual://..."` 같은 값을 쓰고 싶다면 orphan 삭제 조건을 다음처럼 보강해야 한다.

```python
not_(Equipment.aas_id.startswith("mes-virtual://"))
```

하지만 1차에서는 이 변경을 하지 않는 편이 더 안전하다.

### 10.9 스케줄러 영향 검토

현재 스케줄러 projector는 다음 조건으로 설비를 가져온다.

```python
select(Equipment).where(Equipment.is_deleted.is_(False))
```

즉 MES 내부 가상장비도 생성 즉시 스케줄러 후보가 된다.

이 동작은 이번 기능의 목적과 맞다. 다만 다음 점을 주의한다.

| 항목 | 영향 |
|---|---|
| 작업지시 실제 실행 | 영향 없음. 실행 큐는 시나리오/Unit 기반이며 장비 마스터를 직접 실행 대상으로 쓰지 않는다. |
| 스케줄링 결과 | 영향 있음. 가상장비가 후보 설비로 포함되어 capacity가 늘어난다. |
| auto_apply 결과 | 영향 있음. 스케줄링 결과를 적용하면 `ProdResult.target_equipment_id`에 가상장비 ID가 들어갈 수 있다. |
| 실적/분석 | 영향 가능. 가상장비로 잡힌 계획성 `ProdResult`가 분석에 포함될 수 있다. |

따라서 1차 구현에서는 다음 운영 원칙을 둔다.

- `auto_apply=false`로 먼저 스케줄링 결과를 확인한다.
- 가상장비가 포함된 계획을 실제 생산 계획으로 반영할지 사용자가 명시적으로 판단한다.
- 분석 화면에서 가상장비 계획 실적이 섞이는 문제가 생기면 Phase 2에서 `is_virtual` 컬럼 또는 spec helper 기반 제외 옵션을 추가한다.

### 10.10 기존 기능 영향 검토

| 기존 기능 | 영향 여부 | 검토 내용 |
|---|---|---|
| AAS 장비 동기화 | 낮음 | MES 내부 가상장비는 `aas_id=null`이라 AAS sync 대상과 충돌하지 않는다. |
| 미들웨어 상태 polling | 낮음 | `aas_id=null`, `connection_config={}`이므로 미들웨어 실시간 조회 대상에서 제외되거나 실패 가능성이 낮다. polling 로직에서 `aas_id` 없는 장비 skip 여부는 구현 전 확인 필요. |
| 작업지시 READY queue | 없음 | 작업지시 큐는 WorkOrder/Unit/Scenario/Routing 중심이며 Equipment row를 직접 사용하지 않는다. |
| Unit claim/complete | 없음 | lot_no/unit_no 기반이다. |
| 미들웨어 Unit 제어 | 없음 | middleware lot/unit API만 호출한다. |
| 스케줄러 solve | 있음 | 의도적으로 후보 설비가 늘어난다. |
| auto_apply | 있음 | 가상장비 target_equipment_id가 저장될 수 있다. |
| 설비 목록 화면 | 있음 | 가상장비가 표시/필터링된다. |
| 삭제 기능 | 낮음 | 기존 soft delete를 그대로 사용 가능하다. |

위 검토 기준으로 보면, 이 기능은 **실제 미들웨어 실행 경로에는 영향을 거의 주지 않고**, 스케줄러/계획/화면 영역에 영향을 준다. 따라서 구현 시 스케줄러 포함 여부와 auto_apply 사용 시나리오만 특히 확인하면 된다.

### 10.11 단계별 구현 순서

#### Phase 4A. 백엔드 전용 API 구현

1. `EquipmentVirtualCopyCreate`, `EquipmentVirtualCopyResult` schema 추가
2. `equipment_virtual_service.py` 추가
3. `POST /equipments/{equipment_id}/virtual-copies` endpoint 추가
4. 이름/코드 중복 회피 로직 추가
5. 단위 테스트 추가
   - 실장비 1개에서 가상장비 3개 생성
   - `aas_id=null`
   - `spec_data.isVirtual=true`
   - `equipmentSource=MES`
   - `physicalEquipmentId`/`physicalAssetRef` 저장
   - 원본 `connection_config`/`last_data` 미복사
   - 가상장비 원본 복사 시 400

#### Phase 4B. 프론트 생성 UI 구현

1. 설비 상세 모달에 `가상장비 복사` 버튼 추가
2. 복사 모달 추가
3. 생성 수량/name prefix/주요 schedulerInfo 편집 입력 추가
4. 생성 성공 시 목록 refetch
5. `가상장비` 필터로 자동 전환
6. 단위 테스트 또는 최소 타입 체크

#### Phase 4C. 스케줄러 검증

1. 가상장비 생성 전/후 scheduler preview 비교
2. `machine_type_params`에 가상장비의 machineType이 반영되는지 확인
3. `auto_apply=false`로 결과만 확인
4. 필요 시 `include_virtual` 옵션을 후속 작업으로 분리

### 10.12 테스트 계획

#### 백엔드 테스트

| 테스트 | 기대 결과 |
|---|---|
| 실장비에서 1개 복사 | 가상장비 1개 생성 |
| 실장비에서 3개 복사 | 이름 suffix가 붙은 3개 생성 |
| 원본 없음 | 404 |
| 삭제된 원본 | 404 또는 400 |
| 가상장비를 원본으로 복사 | 400 |
| count 0 또는 21 | 422 |
| override에 보호 key 포함 | 서버 값으로 강제 override |
| AAS sync delete_orphans 실행 | `aas_id=null` 가상장비 유지 |

#### 프론트 테스트

| 테스트 | 기대 결과 |
|---|---|
| 실장비 상세 | `가상장비 복사` 버튼 표시 |
| 가상장비 상세 | 복사 버튼 숨김 |
| 생성 성공 | 목록 갱신 및 가상장비 필터 표시 |
| count 입력 오류 | 제출 비활성 또는 오류 표시 |

#### 회귀 테스트

| 테스트 | 기대 결과 |
|---|---|
| 기존 AAS sync | 정상 |
| 기존 설비 목록 조회 | 정상 |
| 기존 작업지시 시작/READY unit 생성 | 정상 |
| 미들웨어 Unit 상태 조회/제어 | 정상 |
| P4R preview | 정상 |

### 10.13 구현 전 확인해야 할 사항

1. `polling_service.py`가 `aas_id=null` 장비를 확실히 건너뛰는지 확인한다.
2. 스케줄러가 `current_status=STOP` 가상장비를 의도대로 `AVAILABLE`로 보는지 확인한다.
3. 가상장비가 분석/OEE/실적 화면에 노출될 때 혼동이 없는지 확인한다.
4. 운영자가 AASX 기반 가상장비와 MES 내부 가상장비를 구분할 수 있게 `equipmentSource` 표시를 유지한다.

### 10.14 최종 권장안

최적 구현안은 다음이다.

1. AASX 기반 가상장비는 “AAS 모델 검증용/외부 자산 모델”로 유지한다.
2. MES 내부 복사 가상장비는 “스케줄링 시뮬레이션용 내부 설비”로 추가한다.
3. 1차 구현은 DB 컬럼 없이 `spec_data` 기반으로 간다.
4. `aas_id=null`로 만들어 AAS sync orphan 삭제와 충돌하지 않게 한다.
5. 실제 실행 경로에는 연결하지 않고 스케줄러 후보로만 사용한다.
6. 스케줄러 결과/분석에서 혼동이 생기면 그때 `equipments.is_virtual` 컬럼과 `include_virtual` 옵션을 추가한다.
