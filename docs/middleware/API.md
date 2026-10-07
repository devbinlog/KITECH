# AM-Middleware API Specification

**Base URL:** `http://<HOST>:<PORT>` (Default: `http://0.0.0.0:8000`)

## 공통 응답 형식

모든 API는 아래 JSON 형식으로 응답합니다.

**성공:**
```json
{ "status": "success", "data": { ... } }
```

**오류:**
```json
{ "status": "error", "error": "ERROR_CODE", "message": "설명" }
```

---

## 1. AAS API (`/api`)

AAS(Asset Administration Shell) 데이터를 조회합니다.

### 1.1 GET `/api/aas`

전체 AAS 데이터를 BaSyx JSON 형식으로 반환합니다.

**Response:**
```json
{
  "status": "success",
  "data": { /* BaSyx AAS JSON */ }
}
```

### 1.2 GET `/api/aas/view`

AAS 데이터를 사람이 보기 쉬운 계층 구조로 반환합니다.
게이트웨이 서브모델은 `isConnected`와 `status`만 포함됩니다.

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "urn:aas:KCNC",
      "idShort": "KCNC",
      "submodels": {
        "cncGateway": { "isConnected": true, "status": { ... } },
        "otherSubmodel": { ... }
      }
    }
  ]
}
```

---

## 2. File API (`/api`)

AASX 패키지에 포함된 보조 파일을 서빙합니다.

### 2.1 GET `/api/files/{path}`

AASX 내 보조 파일을 바이너리로 반환합니다.

**Parameters:**
| 이름 | 위치 | 설명 |
|------|------|------|
| `path` | path | AASX 내부 파일 경로 |

**Response:** 바이너리 데이터 (Content-Type 자동 설정)

---

## 3. Recipe API (`/api`)

YAML 레시피 파일을 관리합니다.

### 3.1 GET `/api/recipes`

레시피 파일 목록을 반환합니다.

**Response:**
```json
{
  "status": "success",
  "data": {
    "total_count": 2,
    "recipes": ["sample.yaml", "sample2.yaml"]
  }
}
```

### 3.2 GET `/api/recipes/{filename}`

레시피 YAML 파일 원본을 `text/plain`으로 반환합니다.

**Parameters:**
| 이름 | 위치 | 설명 |
|------|------|------|
| `filename` | path | 레시피 파일명 (`.yaml` 또는 `.yml`) |

**Response:** YAML 텍스트 (`Content-Type: text/plain`)

### 3.3 POST `/api/recipes`

새 레시피 파일을 업로드합니다. YAML 문법, 스키마, 의미적 검증을 수행합니다.

**Request Body:**
```json
{
  "filename": "new_recipe.yaml",
  "content": "name: My Recipe\nsteps:\n  ..."
}
```

**Error Codes:** `INVALID_FILENAME`, `FILE_EXISTS`, `YAML_PARSE_ERROR`, `SCHEMA_ERROR`, `RECIPE_VALIDATION_FAILED`

### 3.4 POST `/api/recipes/{filename}/validate`

저장된 레시피 파일을 검증합니다 (수정 없음).

**Response (성공):**
```json
{ "status": "success", "data": { "message": "검증 통과" } }
```

### 3.5 DELETE `/api/recipes/{filename}`

레시피 파일을 삭제합니다.

---

## 4. LOT API (`/api/lots`)

LOT(생산 지시)을 생성, 제어, 조회합니다.

### 4.1 POST `/api/lots`

LOT를 생성합니다.

**Content-Type:** `multipart/form-data`

**Form Fields:**
| 이름 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `meta` | JSON string | O | `LotCreateRequest` JSON |
| `files` | File[] | X | 첨부 파일 (NC 파트 프로그램 등) |

**LotCreateRequest:**
```json
{
  "lot_no": "LOT-001",
  "target_qty": 10,
  "recipe_filename": "sample.yaml",
  "files": [
    { "filename": "program.nc", "asset": "KCNC", "desc": "" }
  ]
}
```
- `recipe_filename` 또는 `recipe_content` 중 하나만 제공
- `files` 배열의 각 `filename`은 업로드된 파일명과 정확히 일치해야 함

**Response (성공):**
```json
{
  "status": "success",
  "data": {
    "message": "LOT LOT-001 생성 완료",
    "lot_no": "LOT-001",
    "recipe_name": "sample",
    "target_qty": 10,
    "saved_files": [{ "filename": "program.nc", "asset": "KCNC" }]
  }
}
```

**Error Codes:** `LOT_FOLDER_EXISTS`, `LOT_ALREADY_ACTIVE`, `FILE_UPLOAD_MISSING`, `FILE_META_MISSING`, `VALIDATION_ERROR`, `INTERNAL_ERROR`

### 4.2 GET `/api/lots`

모든 활성 LOT의 번호와 상태를 조회합니다.

**Response:**
```json
{
  "status": "success",
  "data": {
    "LOT-001": "RUNNING",
    "LOT-002": "READY"
  }
}
```

### 4.3 GET `/api/lots/alarms`

전체 LOT의 알람 현황을 조회합니다.

**Response:**
```json
{
  "status": "success",
  "data": {
    "total_lots": 3,
    "lots_with_alarms": 1,
    "total_failed_units": 2,
    "lots": [
      {
        "lot_no": "LOT-001",
        "lot_status": "RUNNING",
        "recipe_name": "sample",
        "failed_count": 2,
        "alarms": [
          {
            "unit_no": "UNIT-003",
            "status": "ALARM",
            "alarm_step_id": "step_2",
            "alarm_message": "CNC 응답 없음",
            "current_step_id": "step_2"
          }
        ]
      }
    ]
  }
}
```

### 4.4 GET `/api/lots/{lot_no}`

특정 LOT의 상세 상태를 조회합니다 (유닛별 진행 상황 포함).

### 4.5 POST `/api/lots/{lot_no}/start`

READY 상태의 LOT를 시작합니다.

**Query Parameters:**
| 이름 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `start_step_id` | string | null | 시작 스텝 ID (생략 시 첫 번째 스텝) |
| `manual_mode` | bool | false | 수동 투입 모드 (유닛 개별 시작) |

### 4.6 POST `/api/lots/{lot_no}/stop`

실행 중인 LOT를 정지합니다.

### 4.7 POST `/api/lots/{lot_no}/resume`

정지된 LOT를 재개합니다.

### 4.8 DELETE `/api/lots/{lot_no}`

LOT를 삭제합니다. 디스크 파일도 함께 삭제됩니다.
실행 중인 LOT(RUNNING)는 삭제할 수 없습니다.

### 4.9 GET `/api/lots/{lot_no}/alarms`

특정 LOT 내 알람 발생 유닛 목록을 조회합니다.

### 4.10 GET `/api/lots/{lot_no}/units/{unit_no}/log`

유닛의 실행 로그를 조회합니다.

**Response:**
```json
{
  "status": "success",
  "data": {
    "lot_no": "LOT-001",
    "unit_no": "UNIT-001",
    "lines": ["2024-01-22 12:00:00 [step_1] 시작", "..."]
  }
}
```

### 4.11 GET `/api/lots/{lot_no}/files`

LOT 폴더의 파일 목록을 자산별로 반환합니다.

**Response:**
```json
{
  "status": "success",
  "data": {
    "lot_no": "LOT-001",
    "assets": [
      {
        "asset": "KCNC",
        "files": [{ "filename": "program.nc", "size": 1024 }]
      }
    ]
  }
}
```

### 4.12 POST `/api/lots/{lot_no}/upload-files`

LOT 폴더의 파일들을 해당 CNC 자산에 업로드합니다.
기존 파일은 삭제 후 재업로드합니다.

### 4.13 POST `/api/lots/{lot_no}/units/{unit_no}/start`

READY 상태의 개별 유닛을 시작합니다 (디스패처 우회).

**Query Parameters:**
| 이름 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `start_step_id` | string | null | 시작 스텝 ID |

### 4.14 POST `/api/lots/{lot_no}/units/{unit_no}/stop`

실행 중인 유닛을 즉시 정지합니다 (Hard Stop).

### 4.15 POST `/api/lots/{lot_no}/units/{unit_no}/stop-after-step`

현재 스텝 완료 후 유닛을 정지합니다 (Soft Stop).

### 4.16 POST `/api/lots/{lot_no}/units/{unit_no}/cancel-pending-stop`

정지 예약(Soft Stop)을 취소합니다.

### 4.17 POST `/api/lots/{lot_no}/units/{unit_no}/resume`

STOPPED 상태의 유닛을 재개합니다.
ALARM 상태는 먼저 `clear-alarm`으로 해제 필요.

**Query Parameters:**
| 이름 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `resume_step_id` | string | null | 재개 스텝 ID (skip_step보다 우선) |
| `skip_step` | bool | false | 현재 스텝 건너뛰기 |
| `clear_retry` | bool | true | 재시도 카운트 초기화 |

### 4.18 POST `/api/lots/{lot_no}/units/{unit_no}/clear-alarm`

ALARM 상태의 유닛에서 알람을 해제합니다.
해제 후 STOPPED 상태가 되며, `resume`으로 재개 가능.

### 4.19 POST `/api/lots/{lot_no}/units/{unit_no}/release-resources`

유닛이 점유한 자원을 수동 해제합니다.
ALARM 또는 STOPPED 상태에서만 사용 가능.

---

## 5. Resource API (`/api/resources`)

자원 점유 상태와 게이트웨이 연결 상태를 조회합니다.

### 5.1 GET `/api/resources/status`

모든 등록 자원의 점유 상태를 반환합니다.

### 5.2 GET `/api/resources/gateways`

자산별 게이트웨이 연결 상태를 반환합니다.

**Response:**
```json
{
  "status": "success",
  "data": {
    "assets": [
      {
        "asset_id": "KCNC",
        "gateways": [
          {
            "gateway_type": "CncGateway",
            "gateway": "192.168.0.100:8080",
            "machine_id": "1",
            "is_connected": true
          }
        ]
      }
    ]
  }
}
```

---

## 6. Debug API (`/debug`)

AAS 속성 읽기/쓰기 및 게이트웨이 디버깅용 API입니다.

### 6.1 GET `/debug/status`

AAS 속성 값을 경로로 조회합니다.

**Query Parameters:**
| 이름 | 타입 | 설명 |
|------|------|------|
| `path` | string | AAS 경로 (예: `KCNC/status/doorState`) |

### 6.2 POST `/debug/commands`

AAS Operation을 실행합니다.

**Request Body:**
```json
{
  "path": "KCNC/cncGateway/commands/MoveTo",
  "input": { "axis": "X", "value": 100.5 }
}
```

### 6.3 GET `/debug/gateways`

등록된 게이트웨이 목록을 반환합니다.

**Response:**
```json
{
  "status": "success",
  "data": {
    "gateways": [
      {
        "key": "192.168.0.100:8080",
        "type": "CncGateway",
        "host": "192.168.0.100",
        "port": "8080",
        "machine_ids": ["1"]
      }
    ]
  }
}
```

### 6.4 POST `/debug/upload-part-program`

CNC 파트 프로그램 업로드를 테스트합니다.

**Request Body:**
```json
{
  "machine_id": "1",
  "nc_path": "",
  "local_path": "C:/path/to/program.nc"
}
```
- `nc_path` 비어있으면 AAS의 `defaultTargetDirectory` 사용

### 6.5 POST `/debug/delete-part-program`

CNC 파트 프로그램 삭제를 테스트합니다.

**Request Body:**
```json
{
  "machine_id": "1",
  "nc_path": "//NC/program.nc"
}
```
