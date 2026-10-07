# 개발 작업 일지 (Cell-MES & 미들웨어 연동)

**작업 일시**: 2026-03-05 ~ 2026-03-06  
**작업자**: Antigravity (AI Assistant)  
**작업 영역**: Cell-MES 백엔드 / 프론트엔드 / 미들웨어 연동 API

---

## 이전 QA 이력 (QA_Report_20260225.md 참조)

> ※ 본 일지는 2026-02-25 기존 통합 QA 리포트를 기반으로 오늘 작업 내용을 추가 기록한 것입니다.

### [2026-02-25] QA 통과 이슈 목록

| 번호 | 이슈 | 원인 | 조치 결과 |
|------|------|------|-----------|
| 1 | 포트 충돌 / 404 Not Found | 미들웨어와 Cell-MES가 동일 포트(8000) 사용 | Cell-MES 포트를 8080으로 변경, NL-Router 환경변수 명시 |
| 2 | 401 Unauthorized | 내부 서비스 인증 헤더 누락 | `X-Internal-Service-Key` 헤더 주입 처리 |
| 3 | 500 Internal Server Error | Alembic 마이그레이션 중복 컬럼 충돌 | 004 마이그레이션 스크립트 중복 제거 후 DB 초기화 및 재마이그레이션 |

**최종 QA 통과**: `test_nlrouter_mes_integration.py` 9개 항목 모두 통과 (`9 passed in 4.14s`)

### [2026-03-04] 외부 미들웨어 실장 연동 완료

| 항목 | 내용 |
|------|------|
| 외부 미들웨어 연결 | `http://10.10.10.126:8000` 설정 일원화 및 헬스 체크 안정화 |
| 실시간 폴링 도입 | asyncio 백그라운드 태스크로 3초 주기 데이터 수집 (`polling_service.py`) |
| 상태 매핑 교정 | `BUSY`, `WORKING`, `ACTIVE` → UI '가동중(RUN)' 매핑 로직 추가 |
| AAS ID 무결성 | DB 설비 ID를 실제 미들웨어 URI 체계로 일괄 갱신 |

---

## 오늘 작업 내역 (2026-03-05 ~ 2026-03-06)

### 1. 생산 API 아키텍처 리팩토링: 작업 지시 시작 시 NC 파일 연동

**배경**: 기존에는 작업 지시 시작 시 수동으로 NC 파일을 업로드해야 했음.

**변경 사항**:
- **백엔드**: `POST /api/v1/production/orders/{id}/start` 신규 엔드포인트 구현
- **백엔드**: NC 파일을 `multipart/form-data` 형식으로 미들웨어에 전달하는 로직 구현
- **프론트엔드**: 작업 시작 버튼 클릭 시 NC 파일 업로드 다이얼로그 추가

---

### 2. 라우팅 마스터 기반 다중 NC 자동 연동 고도화

**배경**: 매번 시작 시마다 파일을 올리는 방식 → 사전에 마스터로 등록된 파일을 자동 연동하는 방식으로 전환

| 수정 파일 | 변경 내용 |
|-----------|-----------|
| `production.py` | 작업 지시 시작 시 라우팅 마스터 파일 자동 조회 및 배열 구성 후 미들웨어 하달 |
| `masters.py` | `POST /api/v1/masters/files/upload` 전용 NC 파일 업로드 API 신설 |
| `routings/page.tsx` | 파일 선택기 UI 추가 및 선택 즉시 서버 업로드 연동 |
| `orders/page.tsx` | 시작 모달 간소화 (파일 폼 제거, 안내 메시지로 대체) |

---

### 3. 확장자 없는 NC 파일(O0002 등) 업로드 오류 해결

**문제**: 브라우저 파일 선택기의 `accept` 속성 제한으로 인해 확장자 없는 파일 선택 불가

**수정**:
- `routings/page.tsx` 파일 입력의 `accept` 속성 제거
- `production/orders/page.tsx` 모달 파일 입력의 `accept` 속성 제거

---

### 4. 프론트엔드 파일 업로드 API 경로 오탈자 수정 (404 Not Found)

**문제**: `master.ts` 서비스에서 호출 URL에 오탈자 발생 (`/master` → `/masters`)

**수정**:
```typescript
// 수정 전 (오류)
await api.post("/api/v1/master/files/upload", ...)

// 수정 후 (정상)
await api.post("/api/v1/masters/files/upload", ...)
```

---

### 5. 로트 생성/시작 분리 아키텍처 전환 ⭐

**배경**: 사용자 요청에 따라 작업지시 생성 시 로트 생성, 시작 시 로트 시작만 수행하는 구조로 완전 분리

| 단계 | API | 미들웨어 연동 |
|------|-----|---------------|
| 작업지시 생성 | `POST /orders` | `POST /api/lots` → NC 파일 배열 전송 |
| 작업지시 시작 | `POST /orders/{id}/start` | `POST /api/lots/{lot_no}/start` 만 핑 |

**검증**: 통합 테스트 스크립트로 HTTP 201 → 200 → 미들웨어 파일 조회(200) 모두 확인 완료

---

### 6. 작업지시 삭제 기능 및 미들웨어 로트 연동 신설

**배경**: 테스트용 작업지시 삭제 기능 부재 문제

**구현 내역**:

| 수정 파일 | 변경 내용 |
|-----------|-----------|
| `production.py` | `DELETE /orders/{id}` 엔드포인트 신설 |
| `production.ts` | `deleteOrder(id)` 서비스 함수 추가 |
| `orders/page.tsx` | 🗑️ 휴지통 버튼 + `ConfirmDeleteModal` 컴포넌트 추가 |
| `types/index.ts` | WorkOrder 타입에 `CANCEL` 상태 추가 |

**삭제 연동 로직**:
1. RUNNING 상태 작업지시 삭제 요청 → 즉시 거부 (400 에러)
2. 미들웨어 `DELETE /api/lots/{lot_no}` 선행 호출
3. 미들웨어 승인(200/204) 또는 이미 없음(404) → MES DB에서 삭제
4. 미들웨어 거절 시 사유를 포함한 에러 메시지 반환

---

### 7. LOT 중지/재시작 미들웨어 연동

**배경**: 일시정지/재시작 버튼이 MES 상태만 변경하고 미들웨어 신호를 보내지 않던 문제

**수정 (`update_work_order_status` 함수)**:

| MES 상태 전이 | 미들웨어 API 호출 |
|---------------|------------------|
| RUNNING → PAUSE | `POST /api/lots/{lot_no}/stop` |
| RUNNING → DONE | `POST /api/lots/{lot_no}/stop` |
| RUNNING → CANCEL | `POST /api/lots/{lot_no}/stop` |
| PAUSE → RUNNING | `POST /api/lots/{lot_no}/resume` |

> 미들웨어 연동 실패 시 경고 로그만 기록(MES 상태 변경은 이미 완료된 상태이므로 고객 UI에 에러 반환하지 않음)

---

### 8. 시나리오 수정 기능 누락 버그 수정

**문제**: 백엔드에 시나리오 PATCH 수정 엔드포인트가 존재하지 않아 수정 요청 시 404 에러 발생

**수정**:

| 수정 파일 | 변경 내용 |
|-----------|-----------|
| `schemas/master.py` | `ScenarioUpdate` Pydantic 스키마 신설 |
| `endpoints/scenarios.py` | `PATCH /{scenario_id}` 수정 라우터 추가 |

---

### 9. 미들웨어 대시보드 통합 기능 이식 (2026-03-05 ~ 03-06) 신규 추가 사항

**배경**: 미들웨어 자체 대시보드에서 제공하던 '로트 진행 상태 상세 확인', '알람 제어 및 유닛 재시작', '설비 상태 모니터링' 기능들을 MES 프론트엔드 시스템으로 통합 내재화.

**주요 구현 내역**:
- **로트 진행 상태 상세 모니터링 (Lot Monitoring Modal)**
  - 백엔드: 미들웨어 `GET /api/lots/{lot_no}`에서 로트 진행 및 Unit 단계 진행 정보를 정제해 전달하는 `GET /api/v1/production/orders/{order_id}/monitoring` API 신설.
  - 프론트엔드: 작업지시 목록(`orders/page.tsx`) 내에 타임라인 기반 형태의 상세 보기 모달 컴포넌트(`LotMonitoringModal.tsx`) 신설 및 연동.
- **알람 표출, 해제(Clear) 및 복구(Resume) 연동**
  - 백엔드: 미들웨어 규격에 맞추어 특정 Unit의 알람 해제 및 재시작 릴레이 API 구성 (`clear-alarm`, `resume`).
  - 프론트엔드: 모니터링 모달 내에서 ERROR 발생 즉시 빨간색으로 표출, 알람 해제 및 복구 원클릭 액션 버튼 개발.
- **설비 모니터링 대시보드 고도화**
  - 백엔드: 미들웨어 `GET /api/aas/view` 연동하여 설비 세부 상태(`submodels` - 도어상태, 바이스상태, X좌표, AGV 위치 등)를 가져와 MES DB(`last_data`)에 병합.
  - 프론트엔드: `EquipmentCard.tsx` 업데이트. 각 설비 유형과 상태에 맞는 게이지, 상태 뱃지, 도어 열림 및 바이스 상태 등의 고도화 뷰 구성.

---

### 10. 설비 데이터 깜빡임(Flickering) 현상 분석 및 원천 해결 신규 추가 사항

**문제 요약**: 프론트엔드의 `EquipmentCard` 컴포넌트에서 설비 상세 데이터 항목이 렌더링되다 사라지기를 반복하는 간헐적 깜빡임 발생.
**근본 원인 조사 및 해결**:
1. (1차 조치) 백엔드: 미들웨어가 일시적으로 비어있는 데이터(`{"status": {}}`)를 보내올 때, 얕은 복사로 기존 `last_data`를 통째로 지워버리는 것을 방지하기 위해 `_deep_merge` 재귀 병합 함수를 새로 구현하여 적용.
2. (원인 규명) 위 조치 후에도 데이터 리셋 발생 확인. 백엔드 폴링 로직 자체는 방어가 잘 되어있었으나 `psutil` 등으로 Windows 실행 프로세스를 검증한 결과 원인을 밝혀냄.
3. (해결 완료) **Uvicorn --reload 기능의 Windows 환경 특성 상 발생한 좀비 워커 프로세스 누적 버그**였음. cũ 버전 코드(얕은 복사)를 가진 구형 워커 프로세스들이 종료되지 않고 수십 개가 살아남아 새 워커와 서로 치열하게 DB 덮어쓰기 경쟁을 벌이고 있었음. 터미널 재시작 및 Kill 커맨드를 통해 완전히 찌꺼기를 날리고 렌더링 복구를 확인하여 해결.

---

## 최종 미들웨어 API 연동 현황

| 기능 | MES API | 미들웨어 API | 상태 |
|------|---------|-------------|------|
| 로트 생성 | `POST /orders` | `POST /api/lots` | ✅ 연동 |
| 로트 시작 | `POST /orders/{id}/start` | `POST /api/lots/{lot_no}/start` | ✅ 연동 |
| 로트 중지 | `PATCH /orders/{id}/status` | `POST /api/lots/{lot_no}/stop` | ✅ 연동 |
| 로트 재개 | `PATCH /orders/{id}/status` | `POST /api/lots/{lot_no}/resume` | ✅ 연동 |
| 로트 삭제 | `DELETE /orders/{id}` | `DELETE /api/lots/{lot_no}` | ✅ 연동 |
| 시나리오 수정 | `PATCH /masters/scenarios/{id}` | — | ✅ 신설 |
| 로트 진행 모니터링 | `GET /orders/{id}/monitoring` | `GET /api/lots/{lot_no}` | ✅ 신설 |
| 알람 해제 | `POST /orders/{id}/units/{no}/clear` | `POST /api/lots/{id}/units/{no}/clear...` | ✅ 신설 |
| 유닛 복구 재개 | `POST /orders/.../resume` | `POST /api/lots/{id}/units/{no}/resume` | ✅ 신설 |

---
