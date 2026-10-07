# MES 수동 병합 계획서

작성일: 2026-06-01  
우리 프로젝트: `/Users/beomhwanham/Desktop/kitech/robot/agents-workspace_260506/agents-workspace_260409`  
병합 대상 프로젝트: `/Users/beomhwanham/Desktop/kitech/robot/agents-workspace_260521/agents-workspace_260521`

## 1. 목적

다른 작업자가 개발한 MES/스케줄러 개선 기능을 우리 프로젝트에 반영한다.

단, 우리 프로젝트에서 실테스트까지 진행하며 맞춰둔 기능과 화면이 깨지면 안 된다. 이번 병합은 파일 덮어쓰기가 아니라, 우리 프로젝트를 기준으로 필요한 기능을 수동 이식하는 방식으로 진행한다.

## 2. 최우선 보호 대상

아래 기능은 현재 우리 프로젝트에서 이미 동작 확인 또는 실테스트 기준으로 맞춰둔 기능이다. 병합 과정에서 회귀가 발생하면 안 된다.

- 작업지시 생성 로직
  - SQLite 환경에서 `WorkOrder.id`를 백엔드가 안전하게 생성하는 로직 유지
  - 미들웨어가 꺼져 있어도 작업지시 생성 가능
- 작업지시 생성/삭제 시 미들웨어 Lot Push/Delete 제거 상태 유지
- 라우팅 설계 파일 처리
  - NC 파일 업로드 시 원본 파일명 `original_filename` 저장
  - 라우팅에서 휴지통 버튼으로 파일 삭제 후 저장하면 기존 DB row도 제거
  - ready-unit 응답에서 NC 파일 이름에 확장자 포함
- 파일 본문 조회 API
  - scenario yaml은 yaml 본문으로 조회
  - NC 파일은 NC 본문으로 조회
  - octet-stream 다운로드 강제 방식으로 되돌리지 않음
- ready-unit API
  - `GET /api/v1/production/orders/ready-units`
  - 응답에 scenario/yaml URL, NC 파일 URL, required resources 포함
  - `unit_no`는 `"1"` 형태의 텍스트로 유지
  - `required_resources`는 첫 점유 step 기준으로 생성
- execution package API
  - `GET /api/v1/production/orders/ready-units/execution-package`
- lot/unit 기반 API
  - claim API
  - complete API
  - `lot_no` + 텍스트 `unit_no` 기준 호출 유지
- 시나리오 yaml 변경 사항
  - `scenario_1.yaml`에 추가한 step 및 step id 재정렬 유지
- 보고용 문서/HTML
  - `CHANGES.md`
  - `scenario_1_flow.html`

## 3. 병합 대상 기능

다른 프로젝트에서 가져올 핵심 기능은 아래로 한정한다.

- 표준공정/라우팅 기반 장비 후보 관리
  - `StdProcess.required_machines`
  - `ProcessRouting.setup_id`
  - `ProcessRouting.required_machines`
  - `ProcessRoutingFile.compatible_machines`
- 스케줄러 payload 고도화
  - 라우팅별 장비 후보
  - NC 파일별 호환 장비
  - setup id
  - lot splitting
  - AMR transfer time
- cell-scheduler 기능 확장
  - multi-machine 후보 처리
  - setup/changeover 처리
  - AMR 이동 시간 반영
  - output saver 및 gantt 이미지 출력
  - AAS loader 관련 기능
- 프론트 화면 개선
  - 표준공정 장비 후보 복수 선택
  - 라우팅별 장비 후보 override
  - NC 파일별 호환 장비 후보 입력
  - scheduler 실행 화면의 lot size / AMR 이동 시간 입력
  - EquipmentCard AAS 좌표 문자열 숫자 변환

## 4. 병합 제외 대상

아래 파일/디렉터리는 병합 대상에서 제외한다.

- SQLite DB 파일
  - `agents/cell-mes/data/*.db`
  - 다른 프로젝트의 DB를 복사하지 않는다.
- 빌드/캐시/로그
  - `.next`
  - `.venv`
  - `__pycache__`
  - `.pytest_cache`
  - 로그 파일
- `agents/cell-schedule-visualizer`
  - 양쪽 프로젝트 비교 결과 실제 코드 차이가 없다.
  - git diff에 보이는 변경은 CRLF/LF 줄바꿈 차이로 판단한다.
  - 병합하지 않는다.
- 다른 프로젝트의 `007_add_work_order_operations.py`
  - 문서상 `WorkOrderOperation`은 추가 후 제거된 흐름이다.
  - 현재 요구사항과 직접 관련이 없고, 우리 migration 번호와 충돌한다.
- generated 파일
  - `frontend/src/generated`
  - `frontend/openapi.json`
  - 필요 시 백엔드 병합 후 재생성한다.

## 5. 충돌 위험 요약

| 영역 | 충돌 위험 | 처리 방침 |
| --- | --- | --- |
| `production.py` | 매우 높음 | 우리 파일을 베이스로 유지하고 필요한 장비 후보 fallback만 추가 |
| `routings.py` | 높음 | 우리 파일 삭제/원본명 로직 유지 + setup/required/compatible 필드 추가 |
| `models/master.py` | 높음 | `original_filename` 유지 + 다른 프로젝트의 장비 필드 추가 |
| `schemas/master.py` | 높음 | `original_filename` validator 유지 + 새 장비 필드 추가 |
| frontend 라우팅 화면 | 높음 | 다른 프로젝트 화면을 덮지 않고 우리 화면에 필드만 이식 |
| frontend 표준공정 화면 | 중간 | `equipment_type` 단일 입력에서 `required_machines` 복수 입력으로 전환 또는 호환 |
| cell-scheduler | 중간~높음 | MES projector/scheduler schema와 함께 적용 |
| cell-schedule-visualizer | 낮음 | 병합 제외 |

## 6. 병합 원칙

1. 우리 프로젝트 파일을 기준으로 한다.
2. 다른 프로젝트 파일을 통째로 복사하지 않는다.
3. 같은 파일에서 충돌이 나면 우리 기능을 먼저 보존한다.
4. DB migration은 복사하지 않고 우리 프로젝트 기준으로 새로 작성한다.
5. 병합은 기능 단위로 작게 나누어 진행한다.
6. 각 단계마다 테스트를 실행하고, 실패하면 다음 단계로 넘어가지 않는다.
7. UI가 깨지거나 기존 화면에서 저장/조회가 안 되면 병합 완료로 보지 않는다.
8. 미들웨어 연동용 API 응답 구조는 변경 전후 샘플을 비교한다.

## 7. 사전 작업

### 7.1 현재 상태 기록

병합 전 아래 정보를 저장한다.

```bash
git status --short
git diff --stat
```

확인 대상:

- 우리 쪽 미커밋 변경
- 다른 작업자가 수정한 파일과 겹치는 파일
- 이미 생성된 migration 번호
- 실테스트에 사용 중인 Docker/DB 상태

### 7.2 비교 기준 문서 확인

다른 프로젝트의 수정 요약 문서는 아래 파일을 기준으로 한다.

- `/Users/beomhwanham/Desktop/kitech/robot/agents-workspace_260521/agents-workspace_260521/revise.md`
- `/Users/beomhwanham/Desktop/kitech/robot/agents-workspace_260521/agents-workspace_260521/merge_guide.md`

`revised.md`가 아니라 `revise.md`가 실제 파일명이다.

## 8. 병합 단계

## Phase 1. DB 모델/스키마 병합

### 대상 파일

- `agents/cell-mes/src/app/models/master.py`
- `agents/cell-mes/src/app/schemas/master.py`
- `agents/cell-mes/frontend/types/index.ts`
- `agents/cell-mes/frontend/services/master.ts`

### 반영 내용

`StdProcess`:

- 기존 `equipment_type` 처리 방식을 바로 제거하지 않는다.
- 새 필드 `required_machines`를 추가한다.
- 기존 데이터 호환을 위해 migration에서 `equipment_type` 값이 있으면 `required_machines` 초기값으로 이전하는 것을 검토한다.

`ProcessRouting`:

- `setup_id` 추가
- `required_machines` 추가

`ProcessRoutingFile`:

- 기존 `original_filename` 유지
- `compatible_machines` 추가

### 완료 기준

- 기존 NC 원본 파일명 저장 로직 유지
- 새 장비 후보 필드가 API read/create/update schema에 포함
- 타입스크립트 타입에 동일하게 반영

## Phase 2. Migration 정리

### 처리 방침

우리 프로젝트의 migration 번호를 기준으로 새 migration을 작성한다.

권장 구조:

- 기존 우리 migration `007_add_original_filename_to_routing_files.py` 유지
- 새 migration `008_add_machine_matching_fields.py` 추가

`008`에서 추가할 컬럼:

- `std_processes.required_machines`
- `process_routings.setup_id`
- `process_routings.required_machines`
- `process_routing_files.compatible_machines`

### 주의사항

- 다른 프로젝트의 DB 파일을 복사하지 않는다.
- 다른 프로젝트의 `007_add_work_order_operations.py`를 가져오지 않는다.
- migration downgrade도 작성한다.
- SQLite 기준으로 JSON 컬럼 동작을 확인한다.

### 완료 기준

```bash
uv run pytest agents/cell-mes/tests/test_api/test_routings.py -q
```

가능하면 컨테이너 DB에서도 migration 적용 후 라우팅 저장/조회 확인.

## Phase 3. 라우팅 API 병합

### 대상 파일

- `agents/cell-mes/src/app/api/v1/endpoints/routings.py`

### 유지할 우리 기능

- 라우팅 저장 시 기존 routing file row 명시 삭제
- 파일 업로드 후 `original_filename` 저장
- 파일 직접 입력 시 `original_filename` 초기화 흐름 유지

### 추가할 기능

- 라우팅 저장 payload에 `setup_id`
- 라우팅 저장 payload에 `required_machines`
- 라우팅 파일 저장 payload에 `compatible_machines`

### 완료 기준

- 라우팅 신규 저장 가능
- 기존 라우팅 수정 가능
- NC 파일 업로드 후 원본 파일명 표시 가능
- 휴지통 삭제 후 저장 시 삭제된 파일 row가 DB에서 제거
- `compatible_machines` 저장/조회 가능

## Phase 4. Production API 보호 병합

### 대상 파일

- `agents/cell-mes/src/app/api/v1/endpoints/production.py`
- `agents/cell-mes/src/app/schemas/production.py`

### 원칙

`production.py`는 우리 파일을 베이스로 한다. 다른 프로젝트의 파일로 교체하지 않는다.

### 유지할 기능

- manual work order id 생성 보정
- ready-units 응답 고도화
- execution-package API
- lot/unit 기반 claim API
- lot/unit 기반 complete API
- unit_no 텍스트 응답
- scenario/yaml/NC URL 포함 응답
- 첫 점유 step 기준 `required_resources`

### 추가할 기능

장비 후보 fallback 순서를 확장한다.

권장 순서:

1. yaml 첫 점유 step에서 추출한 자산
2. `ProcessRouting.required_machines`
3. `StdProcess.required_machines`
4. 기존 호환용 `StdProcess.equipment_type`

### 완료 기준

- `GET /api/v1/production/orders/ready-units` 응답이 기존 미들웨어 계약을 깨지 않음
- `unit_no`가 숫자가 아니라 텍스트로 유지
- `nc_files.name`에 확장자 포함
- `recipe.url`, `nc_files[].url`이 protocol/host 포함 absolute URL
- claim/complete가 `lot_no` + `"1"` 형태의 unit_no로 동작

## Phase 5. 파일 본문 API 보호

### 대상 파일

- `agents/cell-mes/src/app/api/v1/endpoints/masters.py`
- `agents/cell-mes/src/app/api/v1/endpoints/scenarios.py`

### 유지할 기능

- scenario yaml 본문 조회
- NC 파일 본문 조회
- octet-stream 다운로드 강제 방식으로 되돌리지 않음
- 브라우저에서 URL 접속 시 본문 확인 가능

### 완료 기준

- scenario URL 접속 시 yaml 본문 표시
- NC URL 접속 시 NC 본문 표시
- 응답 헤더가 미들웨어 본문 읽기 흐름에 적합

## Phase 6. Scheduler Projector / Protocol 병합

### 대상 파일

- `agents/cell-mes/src/app/services/scheduling/projector.py`
- `agents/cell-mes/src/protocols/scheduler_protocol.py`
- `agents/cell-mes/src/app/api/v1/endpoints/scheduler.py`
- `agents/cell-mes/src/app/services/scheduler_integration.py`

### 추가할 기능

- routing 기준 required machine 후보 생성
- std process 기본 required machines 반영
- NC 파일 compatible machines 반영
- setup_id 반영
- scheduler 요청에 `lot_size`
- scheduler 요청에 `amr_transfer_time_sec`

### 주의사항

- MES가 보내는 payload와 cell-scheduler schema를 같은 단계에서 맞춘다.
- projector만 먼저 바꾸거나 scheduler만 먼저 바꾸면 422 또는 스케줄 실패가 날 수 있다.

### 완료 기준

- scheduler request 생성 성공
- 기존 work order 기반 스케줄 실행 성공
- 장비 후보가 비어 있지 않은 케이스에서 solver가 사용 가능
- 장비 후보가 비어 있는 기존 데이터도 fallback으로 동작

## Phase 7. Frontend 병합

### 대상 파일

- `agents/cell-mes/frontend/types/index.ts`
- `agents/cell-mes/frontend/services/master.ts`
- `agents/cell-mes/frontend/hooks/useMachineTypes.ts`
- `agents/cell-mes/frontend/app/(main)/master/processes/page.tsx`
- `agents/cell-mes/frontend/app/(main)/master/routings/page.tsx`
- `agents/cell-mes/frontend/app/(main)/scheduler/execute/page.tsx`
- `agents/cell-mes/frontend/app/(main)/scheduler/settings/page.tsx`
- `agents/cell-mes/frontend/services/scheduler.ts`
- `agents/cell-mes/frontend/components/equipment/EquipmentCard.tsx`

### 표준공정 화면

추가:

- 등록된 설비에서 machine type 목록을 수집하는 `useMachineTypes`
- `required_machines` 복수 선택 UI

주의:

- 기존 `equipment_type` 기반 데이터가 있을 수 있으므로 백엔드 fallback과 함께 적용한다.

### 라우팅 화면

추가:

- `setup_id` 입력
- 라우팅별 `required_machines` override
- NC 파일별 `compatible_machines`

반드시 유지:

- `original_filename`
- 업로드 후 원본 파일명 표시
- 파일 경로 직접 수정 시 `original_filename` 초기화
- 파일 삭제 후 저장 시 삭제 반영

### Scheduler 화면

추가:

- `lot_size`
- `amr_transfer_time_sec`
- scheduler 요청 payload에 두 값 포함
- 필요 시 gantt PNG 표시

### EquipmentCard

추가:

- AAS에서 문자열로 오는 위치값을 `Number()`로 변환

### 완료 기준

- 표준공정 생성/수정 가능
- 라우팅 생성/수정 가능
- NC 파일 업로드/삭제/저장 가능
- 장비 후보 선택값 저장/조회 가능
- 작업지시 생성 화면 기존 동작 유지
- scheduler 실행 화면 기존 동작 유지

## Phase 8. cell-scheduler 병합

### 대상 파일

- `agents/cell-scheduler/src/app/schemas.py`
- `agents/cell-scheduler/src/app/services/scheduler_service.py`
- `agents/cell-scheduler/src/app/routers/scheduler.py`
- `agents/cell-scheduler/src/app/main.py`
- `agents/cell-scheduler/src/app/config.py`
- `agents/cell-scheduler/src/app/output_saver.py`
- `agents/cell-scheduler/src/app/services/aas_loader.py`
- `agents/cell-scheduler/src/solvers/*.py`
- `agents/cell-scheduler/tests/*.py`

### 추가할 기능

- multi-machine 후보 기반 solver 처리
- lot splitting
- setup/changeover
- AMR transfer time
- gantt output 저장
- AAS loader
- 관련 테스트

### 주의사항

- solver 변경은 범위가 크므로 MES API 병합 이후 진행한다.
- scheduler schema 변경과 MES scheduler request 변경을 함께 검증한다.
- 기존 단순 스케줄 요청도 계속 통과해야 한다.

### 완료 기준

```bash
uv run pytest agents/cell-scheduler/tests -q
uv run pytest agents/cell-mes/tests/test_api/test_scheduler.py -q
uv run pytest agents/cell-mes/tests/test_scheduler_integration.py -q
```

## Phase 9. 테스트 계획

### 백엔드 API 테스트

필수 확인:

- 표준공정 생성/수정/조회
- 라우팅 저장/조회
- NC 파일 업로드
- 라우팅 NC 파일 삭제 후 저장
- scenario 본문 조회
- NC 본문 조회
- 작업지시 생성
- ready-units 조회
- execution-package 조회
- lot/unit claim
- lot/unit complete
- scheduler solve

권장 명령:

```bash
uv run pytest agents/cell-mes/tests/test_api/test_routings.py -q
uv run pytest agents/cell-mes/tests/test_api/test_production.py -q
uv run pytest agents/cell-mes/tests/test_api/test_scheduler.py -q
uv run pytest agents/cell-mes/tests/test_scheduler_integration.py -q
```

### 프론트 테스트

확인 화면:

- 표준공정 관리
- 라우팅 설계
- 작업지시 생성
- 작업 시작
- scheduler 실행
- scheduler 설정
- 설비 카드

권장 확인:

```bash
npm run lint
npm run typecheck
```

프로젝트에 해당 script가 없으면 `package.json`의 실제 script 기준으로 실행한다.

### 컨테이너/실환경 테스트

가능하면 Docker 컨테이너에 떠 있는 MES에서 아래를 직접 확인한다.

1. 라우팅 설계에서 NC 파일 업로드
2. 기존 NC 파일 휴지통 삭제 후 저장
3. 작업지시 생성
4. ready-unit API 호출
5. recipe URL 브라우저 접속
6. NC URL 브라우저 접속
7. claim API 호출
8. complete API 호출
9. scheduler 실행

## 10. ready-unit 응답 검증 기준

ready-unit 응답은 미들웨어 계약에 직접 영향을 주므로 병합 후 반드시 샘플을 저장한다.

필수 필드:

```json
[
  {
    "unit_id": 6,
    "unit_no": "1",
    "scenario_id": 7,
    "scenario_filename": "cell-mes/data/scenario_1.yaml",
    "recipe": {
      "name": "cnc_lathe_single_piece_flow",
      "url": "http://localhost:8000/api/v1/masters/scenarios/7/download"
    },
    "required_resources": {
      "main": ["DOOSAN_MOMA"]
    },
    "nc_files": [
      {
        "asset": "DH400",
        "name": "sample.nc",
        "url": "http://localhost:8000/api/v1/masters/files/1/download"
      }
    ],
    "work_order_id": 100,
    "lot_no": "LOT-20260522-001",
    "product_id": 6,
    "priority": 5,
    "target_qty": 5
  }
]
```

주의:

- 위 값은 형식 예시이며, 실제 장비명/파일명은 DB와 yaml 기준으로 검증한다.
- `required_resources`는 첫 점유 step 기준이어야 한다.
- `unit_no`는 `"001"`이 아니라 `"1"`이어야 한다.

## 11. 병합 완료 판정 기준

아래 조건을 모두 만족해야 병합 완료로 본다.

- 기존 작업지시 생성이 정상 동작
- 기존 작업지시 화면이 정상 표시
- 기존 라우팅 설계 화면이 정상 표시
- NC 파일 업로드/삭제/저장이 정상 동작
- 원본 NC 파일명이 유지됨
- yaml/NC 본문 URL이 브라우저에서 확인 가능
- ready-units 응답이 미들웨어 계약을 만족
- claim/complete가 lot_no + unit_no 텍스트로 동작
- 표준공정/라우팅 장비 후보가 저장/조회됨
- scheduler 요청이 새 schema로 정상 생성됨
- cell-scheduler가 기존 케이스와 새 케이스를 모두 처리
- frontend typecheck/lint 또는 동등 검증 통과
- 백엔드 pytest 통과

## 12. 롤백 기준

아래 문제가 발생하면 즉시 해당 phase 변경만 되돌리고 원인을 분석한다.

- 작업지시 생성 실패
- ready-units 응답 구조 변경으로 미들웨어 호출 실패
- 라우팅 저장 시 기존 NC 파일이 의도치 않게 남거나 사라짐
- 원본 파일명이 사라짐
- yaml/NC 본문 조회 API가 다운로드 방식으로 바뀜
- scheduler payload가 422를 반환
- frontend에서 표준공정/라우팅 화면이 렌더링 실패

## 13. 최종 병합 순서 요약

1. 현재 상태 기록
2. 모델/스키마 병합
3. migration 추가
4. 라우팅 API 병합
5. production API 보호 병합
6. 파일 본문 API 보호 확인
7. scheduler projector/protocol 병합
8. frontend 타입/서비스 병합
9. frontend 표준공정/라우팅 화면 병합
10. frontend scheduler 화면 병합
11. cell-scheduler 병합
12. 테스트 실행
13. 컨테이너/실환경 확인
14. 결과를 `CHANGES.md`에 정리

## 14. 결론

이번 병합은 자동 merge나 폴더 덮어쓰기로 진행하면 안 된다.

우리 프로젝트의 실테스트 완료 기능을 기준으로 보존하면서, 다른 프로젝트의 장비 후보/스케줄러 고도화 기능만 수동 이식한다. 특히 `production.py`, `routings.py`, master model/schema, frontend 라우팅 화면은 반드시 수동 병합 대상으로 관리한다.
