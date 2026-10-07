## Cell-MES ↔ 미들웨어 연동 API 가이드

### 개요: 전체 흐름

```
[MES] 작업지시 생성 → MES DB에 작업지시만 등록
[MES] 작업지시 시작 → Dispatch Daemon이 Unit 1개 생성 (READY 상태)
[미들웨어] READY Unit 목록 조회 → 가장 적합한 Unit 선택 → Claim (점유) → 가공 수행 → Complete 보고
[MES] Complete 수신 → 다음 Unit 자동 생성 (반복)
```

---

## 1단계: 작업지시 등록

MES에서 작업지시를 생성하면 MES DB에만 작업지시를 등록합니다.
기존에는 `POST {MIDDLEWARE_URL}/api/lots`로 lot/NC 파일을 push하는 레거시 연동이 있었지만,
현재 Lot-Size 1 구조에서는 미들웨어가 READY Unit을 조회한 뒤 필요한 실행 패키지와 파일 URL을 가져가는 방식으로 동작합니다.

---

## 2단계: READY Unit 목록 조회 ← 미들웨어 주기적 폴링

미들웨어는 이 API를 **주기적으로 폴링**하여 가공할 Unit이 있는지 확인합니다.

```
GET /api/v1/production/orders/ready-units
Authorization: Bearer {token}
```

**응답 예시:**
```json
[
  {
    "unit_id": 42,
    "unit_no": 3,
    "scenario_filename": "scenarios/cell1_scenario.yaml",
    "work_order_id": 7,
    "lot_no": "LOT-2026-001",
    "product_id": 2,
    "priority": 3,
    "target_qty": 10
  },
  {
    "unit_id": 55,
    "unit_no": 1,
    "scenario_filename": "scenarios/cell2_scenario.yaml",
    "work_order_id": 9,
    "lot_no": "LOT-2026-002",
    "product_id": 3,
    "priority": 5,
    "target_qty": 5
  }
]
```

**설계 포인트:**
- 응답 리스트는 **WorkOrder 우선순위(priority) 오름차순** 정렬 (숫자 낮을수록 높은 우선순위)
- RUNNING 상태인 WorkOrder당 **READY Unit이 최대 1개** 존재
- 빈 배열 `[]` 이면 현재 처리할 Unit 없음

---

## 3단계: Unit Claim (점유 선언) ← 미들웨어가 호출

가공을 시작하기 전에 반드시 Claim해야 합니다. Claim하면 Unit이 `READY → RUNNING` 으로 전환되어 다른 미들웨어 인스턴스가 중복으로 가져가지 않습니다.

```
POST /api/v1/production/orders/{work_order_id}/units/{unit_id}/claim
Authorization: Bearer {token}
```

**응답:**
```json
{ "message": "Unit claimed successfully" }
```

**에러 케이스:**
| HTTP | 상황 |
|------|------|
| `404` | unit_id 존재하지 않음 |
| `400` | unit이 해당 work_order에 속하지 않음 |
| `400` | 이미 RUNNING/DONE 상태 (다른 미들웨어가 먼저 Claim) |

---

## 4단계: Unit Complete 보고 ← 가공 완료 시 미들웨어가 호출

가공이 완전히 끝나면 Complete를 보고합니다. MES는 이 시점에 다음 Unit을 자동 생성합니다.

```
POST /api/v1/production/orders/{work_order_id}/units/{unit_id}/complete
Authorization: Bearer {token}
```

**응답:**
```json
{ "message": "Unit completed successfully" }
```

**MES 내부 동작 (미들웨어는 신경 안 써도 됨):**
- Unit 상태 `RUNNING → DONE`
- `WorkOrder.completed_qty += 1`
- `completed_qty >= target_qty` 이면 WorkOrder 자동 `DONE` 처리
- Dispatch Daemon이 다음 Unit을 READY 상태로 자동 생성

---

## 부가 API (필요 시 사용)

### 작업 정보 상세 조회
```
GET /api/v1/production/middleware/work-info?lot_no=LOT-2026-001
Authorization: Bearer {token}
```
NC 파일 경로, 공정 순서, 시나리오 파일명 등 상세 작업 정보 반환.

### Unit 일시 정지 / 재시작
```
POST /api/v1/production/orders/{order_id}/units/{unit_id}/stop
POST /api/v1/production/orders/{order_id}/units/{unit_id}/resume
```
MES에서 PAUSE 명령이 내려올 때 미들웨어가 실행 중인 Unit을 일시 중지합니다.

---

## 상태 다이어그램 요약

```
[Dispatch Daemon] 자동 생성
       ↓
    READY  ──(claim)──→  RUNNING  ──(complete)──→  DONE
              미들웨어         미들웨어
                              ↓(stop)
                           PAUSED
                              ↓(resume)
                           RUNNING
```

---

## 인증

모든 API 호출에 JWT 토큰 필요합니다.

```
POST /api/v1/auth/login
{ "username": "admin", "password": "admin123" }
→ { "access_token": "eyJ...", "token_type": "bearer" }
```

이후 모든 요청 헤더에 `Authorization: Bearer {access_token}` 포함.
