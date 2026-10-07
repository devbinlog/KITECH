# Cell-MES 기능명세서

> 작성일: 2026-08-06  
> 대상: Cell-MES  
> 작성 기준: 현재 구현된 화면, API, 서비스 기능 기준  
> 문서 목적: 외부 연계/개발 업체 전달용 기능 범위 공유

## 1. 개요

본 문서는 Cell-MES에서 현재 제공하는 기능을 화면 메뉴와 API 기준으로 정리한 기능명세서이다. 신규 요구사항이나 향후 개발 예정 기능이 아니라, 현재 시스템에서 확인 가능한 기능을 기준으로 작성했다.

`메뉴 ID`는 별도 화면설계서에서 부여하는 식별자가 아니라, 본 기능명세서에서 메뉴와 기능을 추적하기 위해 URL 기준으로 부여한 관리 식별자이다.

## 2. 메뉴 구조

| 대분류 | 메뉴 | 메뉴 ID | URL | 주요 기능 |
| --- | --- | --- | --- | --- |
| 인증 | 로그인 | MN-AUTH-010 | `/login` | 사용자 로그인, 토큰 발급 |
| 공통 | 대시보드 | MN-DASH-010 | `/` | 생산/설비/품질/AI 요약 현황 |
| 기준정보 | 표준공정 | MN-MST-010 | `/master/processes` | 표준공정 CRUD |
| 기준정보 | 제품관리 | MN-MST-020 | `/master/products` | 제품 CRUD, DT 프로젝트 연결 |
| 기준정보 | 라우팅설계 | MN-MST-030 | `/master/routings` | 품목별 공정 라우팅 및 파일 매핑 |
| 기준정보 | 물류시나리오 | MN-MST-040 | `/master/scenarios` | 시나리오 CRUD, 편집, 테스트 |
| 기준정보 | 설비관리 | MN-MST-050 | `/master/equipments` | 설비 CRUD, AAS 동기화, 가상 설비 복제 |
| 기준정보 | n8n 에디터 | MN-MST-060 | 외부 URL | n8n 워크플로우 에디터 연결 |
| 생산관리 | 작업지시 | MN-PRD-010 | `/production/orders` | 작업지시 CRUD, 시작, 상태 변경, Unit 관리 |
| 생산관리 | 생산실적 | MN-PRD-020 | `/production/results` | 생산 실적 조회/등록 |
| 생산관리 | 다운타임 | MN-PRD-030 | `/downtime` | 다운타임 사유/이력 관리 |
| 생산관리 | 알람관리 | MN-PRD-040 | `/alarms` | 알람 정의/발생/확인/해제 관리 |
| 스케줄러 | 스케줄 현황 | MN-SCH-010 | `/scheduler` | 현재 스케줄, 설비별 작업 현황 |
| 스케줄러 | 스케줄 실행 | MN-SCH-020 | `/scheduler/execute` | 스케줄 생성, 솔버 실행, 결과 승인 |
| 스케줄러 | 솔버 설정 | MN-SCH-030 | `/scheduler/settings` | 솔버 유형 및 파라미터 설정 |
| 품질관리 | 품질 대시보드 | MN-QLT-010 | `/quality` | 검사/불량/NCR 요약 |
| 품질관리 | 검사계획 | MN-QLT-020 | `/quality/inspection-plans` | 검사계획 CRUD |
| 품질관리 | 측정결과 | MN-QLT-030 | `/quality/inspection-results` | 검사 결과 조회/등록 |
| 품질관리 | SPC 차트 | MN-QLT-040 | `/quality/spc` | SPC 관리차트 및 공정능력 분석 |
| 품질관리 | NCR 관리 | MN-QLT-050 | `/quality/ncr` | 부적합 보고서 관리 |
| 분석리포트 | 분석 대시보드 | MN-ANL-010 | `/analytics` | KPI, OEE, 생산/품질 트렌드 |
| 분석리포트 | 설비 가동률 | MN-ANL-020 | `/analytics/equipment` | 설비별 가동률/효율/다운타임 분석 |
| 분석리포트 | Lot 추적 | MN-ANL-030 | `/analytics/lot-trace` | Lot별 생산/품질 추적 |
| AI/NL | 채팅 | MN-NLM-010 | `/chat` | 자연어 질의, 질의 이력, 즐겨찾기 |

## 3. 기능 목록

| No | 요구사항 ID | 메뉴 ID | 메뉴/화면명 | 기능 ID | 기능명 | 기능상세 | 권한 | 구현 범위 | 관련 API | 비고 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | REQ-AUTH-001 | MN-AUTH-010 | 로그인 | FN-AUTH-001 | 로그인 | 사용자 ID/비밀번호로 인증하고 JWT access token을 발급한다. | 전체 | 화면/API/DB | `POST /api/v1/auth/login` |  |
| 2 | REQ-AUTH-001 | MN-AUTH-010 | 로그인 | FN-AUTH-002 | 사용자 등록 | 신규 사용자를 등록하고 역할 정보를 저장한다. | 관리자 | API/DB | `POST /api/v1/auth/register` | 운영 정책에 따라 노출 제한 필요 |
| 3 | REQ-AUTH-001 | 공통 | 공통 | FN-AUTH-003 | 내 정보 조회 | 현재 로그인 사용자의 계정 및 권한 정보를 조회한다. | 로그인 사용자 | API/DB | `GET /api/v1/auth/me` |  |
| 4 | REQ-COM-001 | MN-DASH-010 | 대시보드 | FN-DASH-001 | 종합 현황 조회 | KPI, 설비 상태, 작업 현황, 품질 요약을 대시보드에 표시한다. | 로그인 사용자 | 화면/API/DB | `GET /api/v1/analytics/kpis`, `GET /api/v1/analytics/daily-status` |  |
| 5 | REQ-COM-001 | MN-DASH-010 | 대시보드 | FN-DASH-002 | AI 인사이트 표시 | 생산/설비/품질 현황을 요약한 AI 인사이트 위젯을 표시한다. | 로그인 사용자 | 화면/API | `POST /api/v1/nlm/query` |  |
| 6 | REQ-MST-001 | MN-MST-010 | 표준공정 | FN-MST-001 | 표준공정 조회 | 표준공정 목록 및 상세 정보를 조회한다. | 로그인 사용자 | 화면/API/DB | `GET /api/v1/masters/std-processes`, `GET /api/v1/masters/std-processes/{process_id}` |  |
| 7 | REQ-MST-001 | MN-MST-010 | 표준공정 | FN-MST-002 | 표준공정 등록 | 공정 코드, 공정명, 카테고리, 설비 유형, 사이클/셋업 시간을 등록한다. | 관리자 | 화면/API/DB | `POST /api/v1/masters/std-processes` |  |
| 8 | REQ-MST-001 | MN-MST-010 | 표준공정 | FN-MST-003 | 표준공정 수정 | 기존 표준공정의 명칭, 설명, 설비 유형, 후보 설비, 기준 시간을 수정한다. | 관리자 | 화면/API/DB | `PATCH /api/v1/masters/std-processes/{process_id}` |  |
| 9 | REQ-MST-001 | MN-MST-010 | 표준공정 | FN-MST-004 | 표준공정 삭제 | 미사용 표준공정을 삭제한다. | 관리자 | 화면/API/DB | `DELETE /api/v1/masters/std-processes/{process_id}` |  |
| 10 | REQ-MST-002 | MN-MST-010 | 표준공정 | FN-MST-005 | 공정 카테고리 관리 | 공정 카테고리 목록 조회, 등록, 상세 조회, 삭제를 수행한다. | 관리자 | API/DB | `/api/v1/masters/process-categories` |  |
| 11 | REQ-MST-003 | MN-MST-020 | 제품관리 | FN-MST-006 | 제품 조회 | 제품 목록 및 상세 정보를 조회하고 삭제 포함 여부를 선택한다. | 로그인 사용자 | 화면/API/DB | `GET /api/v1/masters/products`, `GET /api/v1/masters/products/{product_id}` |  |
| 12 | REQ-MST-003 | MN-MST-020 | 제품관리 | FN-MST-007 | 제품 등록 | 제품 코드, 제품명, 단위, DT 프로젝트 연결 정보를 등록한다. | 관리자 | 화면/API/DB | `POST /api/v1/masters/products` |  |
| 13 | REQ-MST-003 | MN-MST-020 | 제품관리 | FN-MST-008 | 제품 수정/삭제 | 제품 기본 정보를 수정하거나 소프트 삭제한다. | 관리자 | 화면/API/DB | `PATCH /api/v1/masters/products/{product_id}`, `DELETE /api/v1/masters/products/{product_id}` |  |
| 14 | REQ-DT-001 | MN-MST-020 | 제품관리 | FN-DT-001 | DT 프로젝트 연결 | 제품에 Digital Thread 프로젝트 참조를 연결, 조회, 해제한다. | 관리자 | 화면/API/DB/외부연계 | `GET/PUT/DELETE /api/v1/masters/products/{product_id}/dt-project` |  |
| 15 | REQ-DT-001 | MN-MST-020 | 제품관리 | FN-DT-002 | DT NC 파일 조회 | 제품 및 workplan 기준으로 DT 플랫폼의 NC 파일 참조 목록을 조회한다. | 로그인 사용자 | 화면/API/DB/외부연계 | `GET /api/v1/masters/products/{product_id}/dt-nc-files` |  |
| 16 | REQ-DT-001 | MN-MST-020 | 제품관리 | FN-DT-003 | DTP 프로젝트 검색 | DTP 프로젝트 목록 및 프로젝트 트리를 조회한다. | 로그인 사용자 | API/외부연계 | `GET /api/v1/integrations/dtp/projects`, `GET /api/v1/integrations/dtp/projects/tree` |  |
| 17 | REQ-MST-004 | MN-MST-030 | 라우팅설계 | FN-MST-009 | 라우팅 조회 | 제품별 공정 라우팅, 순서, 리비전, 연결 파일을 조회한다. | 로그인 사용자 | 화면/API/DB | `GET /api/v1/masters/products/{product_id}/routings` |  |
| 18 | REQ-MST-004 | MN-MST-030 | 라우팅설계 | FN-MST-010 | 라우팅 저장 | 제품별 공정 순서, 셋업 ID, 후보 설비, DT workplan, 파일 목록을 일괄 저장한다. | 관리자 | 화면/API/DB | `PUT /api/v1/masters/products/{product_id}/routings` |  |
| 19 | REQ-MST-004 | MN-MST-030 | 라우팅설계 | FN-MST-011 | 라우팅 파일 업로드/다운로드 | NC 등 라우팅 파일을 업로드하고 저장된 파일을 다운로드한다. | 관리자 | 화면/API/파일 | `POST /api/v1/masters/files/upload`, `GET /api/v1/masters/files/{file_id}/download` |  |
| 20 | REQ-MST-005 | MN-MST-040 | 물류시나리오 | FN-MST-012 | 시나리오 조회 | 제품별 또는 활성 상태 기준으로 시나리오 목록/상세를 조회한다. | 로그인 사용자 | 화면/API/DB/파일 | `GET /api/v1/masters/scenarios`, `GET /api/v1/masters/scenarios/{scenario_id}` |  |
| 21 | REQ-MST-005 | MN-MST-040 | 물류시나리오 | FN-MST-013 | 시나리오 등록/수정/삭제 | 시나리오 코드, 명칭, 제품, YAML 파일 경로, 활성 여부를 관리한다. | 관리자 | 화면/API/DB/파일 | `POST/PATCH/DELETE /api/v1/masters/scenarios` |  |
| 22 | REQ-MST-005 | MN-MST-040 | 물류시나리오 | FN-MST-014 | 시나리오 콘텐츠 관리 | YAML 시나리오 내용을 조회, 저장, 다운로드한다. | 관리자 | 화면/API/파일 | `GET /api/v1/masters/scenarios/{scenario_id}/content`, `PUT /content`, `GET /download` |  |
| 23 | REQ-MST-005 | MN-MST-040 | 물류시나리오 | FN-MST-015 | 시나리오 편집기 | 노드 기반 시나리오 캔버스, 파라미터 패널, YAML 미리보기, 변수 탐색을 제공한다. | 관리자 | 화면/API/파일 | `POST /api/v1/converters/yaml-to-n8n`, `POST /api/v1/converters/n8n-to-yaml` |  |
| 24 | REQ-MST-005 | MN-MST-040 | 물류시나리오 | FN-MST-016 | 시나리오 테스트 실행 | 시나리오 테스트 실행을 생성하고 상태 조회 및 취소를 수행한다. | 관리자 | 화면/API/외부연계 | `POST /api/v1/masters/scenarios/{scenario_id}/test-runs`, `GET /test-runs/{run_id}`, `POST /test-runs/{run_id}/cancel` |  |
| 25 | REQ-MST-006 | MN-MST-050 | 설비관리 | FN-MST-017 | 설비 조회 | 설비 목록, 상세, 미들웨어 상태, 실시간 상태를 조회한다. | 로그인 사용자 | 화면/API/DB/외부연계 | `GET /api/v1/masters/equipments`, `GET /{equipment_id}`, `GET /{equipment_id}/status` |  |
| 26 | REQ-MST-006 | MN-MST-050 | 설비관리 | FN-MST-018 | 설비 등록/삭제 | 수동 설비 등록 및 설비 삭제를 수행한다. | 관리자 | 화면/API/DB | `POST /api/v1/masters/equipments`, `DELETE /api/v1/masters/equipments/{equipment_id}` |  |
| 27 | REQ-MST-006 | MN-MST-050 | 설비관리 | FN-MST-019 | AAS 설비 동기화 | 미들웨어/AAS 서버에서 설비 정보를 동기화하고 orphan 삭제 옵션을 처리한다. | 관리자 | 화면/API/DB/외부연계 | `POST /api/v1/masters/equipments/sync`, `GET /middleware-health` |  |
| 28 | REQ-MST-006 | MN-MST-050 | 설비관리 | FN-MST-020 | 가상 설비 복제 | 실장비 정보를 기준으로 MES 가상 설비를 복제 생성한다. | 관리자 | 화면/API/DB | `POST /api/v1/masters/equipments/{equipment_id}/virtual-copies` |  |
| 29 | REQ-MST-006 | MN-MST-050 | 설비관리 | FN-MST-021 | 설비 상태 이력 | 설비 상태 변경 이력과 상태 요약을 조회/등록한다. | 로그인 사용자 | 화면/API/DB | `GET /status-history`, `POST /status-history`, `GET /status-summary` |  |
| 30 | REQ-MST-007 | MN-MST-050 | 설비관리 | FN-MST-022 | 셀 관리 | 제조 셀 목록, 등록, 상세 조회, 삭제를 수행한다. | 관리자 | API/DB | `/api/v1/masters/cells` |  |
| 31 | REQ-PRD-001 | MN-PRD-010 | 작업지시 | FN-PRD-001 | 작업지시 조회 | 상태, 기간, 보기 조건, 페이지 조건으로 작업지시 목록/상세를 조회한다. | 로그인 사용자 | 화면/API/DB | `GET /api/v1/production/orders`, `GET /orders/{order_id}` |  |
| 32 | REQ-PRD-001 | MN-PRD-010 | 작업지시 | FN-PRD-002 | 작업지시 등록/삭제 | Lot 번호, 제품, 시나리오, 수량, 우선순위, 납기, 비고로 작업지시를 등록/삭제한다. | 관리자 | 화면/API/DB | `POST /api/v1/production/orders`, `DELETE /orders/{order_id}` |  |
| 33 | REQ-PRD-001 | MN-PRD-010 | 작업지시 | FN-PRD-003 | 작업지시 상태 변경 | 작업지시 시작 및 상태 전이를 처리한다. | 관리자/운영자 | 화면/API/DB | `POST /orders/{order_id}/start`, `PATCH /orders/{order_id}/status` |  |
| 34 | REQ-PRD-002 | MN-PRD-010 | 작업지시 | FN-PRD-004 | Unit 큐 조회 | 작업지시별 Unit 목록과 READY Unit 큐를 조회한다. | 로그인 사용자 | 화면/API/DB | `GET /orders/{order_id}/units`, `GET /orders/ready-units` |  |
| 35 | REQ-PRD-002 | MN-PRD-010 | 작업지시 | FN-PRD-005 | Unit 실행 패키지 조회 | 미들웨어 실행에 필요한 작업정보, 시나리오, 라우팅 파일, 리소스 정보를 묶어 제공한다. | 미들웨어/운영자 | API/DB/파일/외부연계 | `GET /orders/ready-units/execution-package`, `GET /middleware/work-info` |  |
| 36 | REQ-PRD-002 | MN-PRD-010 | 작업지시 | FN-PRD-006 | Unit claim/complete | Unit을 실행 중으로 점유하고 완료 처리한다. | 미들웨어/운영자 | API/DB | `POST /orders/units/claim`, `POST /orders/units/complete`, `POST /orders/{order_id}/units/{unit_id}/claim`, `POST /complete` |  |
| 37 | REQ-PRD-002 | MN-PRD-010 | 작업지시 | FN-PRD-007 | Unit 정지/재개/알람 해제 | Unit 실행 중 정지, 재개, 알람 해제를 처리한다. | 운영자 | 화면/API/DB/외부연계 | `POST /units/{unit_id}/stop`, `POST /resume`, `POST /clear-alarm` |  |
| 38 | REQ-PRD-002 | MN-PRD-010 | 작업지시 | FN-PRD-008 | Unit 시나리오 변경 | 대기 Unit의 시나리오 hold, 변경, release를 처리한다. | 운영자 | 화면/API/DB | `POST /scenario-hold`, `PATCH /scenario`, `POST /scenario-release` |  |
| 39 | REQ-PRD-002 | MN-PRD-010 | 작업지시 | FN-PRD-009 | 미들웨어 상태/명령 | 작업지시의 미들웨어 상태를 조회하고 Unit 명령/재개 명령을 전달한다. | 운영자/미들웨어 | 화면/API/외부연계 | `GET /middleware-state`, `POST /middleware/units/{unit_no}/commands/{action}`, `POST /middleware/units/{unit_no}/resume` |  |
| 40 | REQ-PRD-003 | MN-PRD-020 | 생산실적 | FN-PRD-010 | 생산실적 조회 | 작업지시 기준으로 생산실적을 페이지 조회한다. | 로그인 사용자 | 화면/API/DB | `GET /api/v1/production/results` |  |
| 41 | REQ-PRD-003 | MN-PRD-020 | 생산실적 | FN-PRD-011 | 생산실적 등록 | 작업지시, 공정, 설비, 양품/불량 수량으로 생산 실적을 등록한다. | 운영자 | 화면/API/DB | `POST /api/v1/production/results` |  |
| 42 | REQ-PRD-004 | MN-PRD-030 | 다운타임 | FN-PRD-012 | 다운타임 사유 관리 | 다운타임 사유 목록 조회 및 등록을 수행한다. | 관리자 | 화면/API/DB | `GET /api/v1/downtime/reasons`, `POST /reasons` |  |
| 43 | REQ-PRD-004 | MN-PRD-030 | 다운타임 | FN-PRD-013 | 다운타임 이력 관리 | 다운타임 목록 조회, 시작, 수정, 종료, 요약 조회를 수행한다. | 운영자 | 화면/API/DB | `GET/POST/PATCH /api/v1/downtime`, `POST /{downtime_id}/end`, `GET /summary` |  |
| 44 | REQ-PRD-005 | MN-PRD-040 | 알람관리 | FN-PRD-014 | 알람 정의 관리 | 알람 코드, 심각도, 분류, 권장 조치, 자동 정지 여부를 관리한다. | 관리자 | 화면/API/DB | `GET/POST /api/v1/alarms/definitions` |  |
| 45 | REQ-PRD-005 | MN-PRD-040 | 알람관리 | FN-PRD-015 | 알람 발생 조회/등록 | 알람 목록, 활성 알람, 활성 알람 요약을 조회하고 신규 알람을 등록한다. | 운영자/시스템 | 화면/API/DB | `GET /api/v1/alarms`, `GET /active`, `GET /active/summary`, `POST /api/v1/alarms` |  |
| 46 | REQ-PRD-005 | MN-PRD-040 | 알람관리 | FN-PRD-016 | 알람 확인/해제 | 활성 알람을 확인 처리하거나 해제 처리하고 조치 메모를 저장한다. | 운영자 | 화면/API/DB | `POST /api/v1/alarms/{alarm_id}/acknowledge`, `POST /resolve` |  |
| 47 | REQ-SCH-001 | MN-SCH-010 | 스케줄 현황 | FN-SCH-001 | 현재 스케줄 조회 | 기준일과 실행 중 작업 포함 여부로 설비별 스케줄 현황을 조회한다. | 로그인 사용자 | 화면/API/DB | `GET /api/v1/scheduler/current-schedule` |  |
| 48 | REQ-SCH-001 | MN-SCH-010 | 스케줄 현황 | FN-SCH-002 | 설비 가용성 조회 | 스케줄러가 사용할 설비 가용 시간, 설비 유형, 셋업 정보를 조회한다. | 로그인 사용자 | 화면/API/DB | `GET /api/v1/scheduler/equipment-availability` |  |
| 49 | REQ-SCH-002 | MN-SCH-020 | 스케줄 실행 | FN-SCH-003 | 스케줄 대상 작업 조회 | READY 등 지정 상태의 작업지시를 스케줄링 입력으로 조회한다. | 로그인 사용자 | 화면/API/DB | `GET /api/v1/scheduler/work-orders` |  |
| 50 | REQ-SCH-002 | MN-SCH-020 | 스케줄 실행 | FN-SCH-004 | 스케줄 요청 생성 | 작업지시, 설비, machine type parameter를 스케줄러 요청 JSON으로 생성한다. | 운영자 | 화면/API/DB | `POST /api/v1/scheduler/create-request` |  |
| 51 | REQ-SCH-002 | MN-SCH-020 | 스케줄 실행 | FN-SCH-005 | 솔버 실행 | 솔버 유형, 시간 제한, horizon, lot size 등 조건으로 스케줄을 계산한다. | 운영자 | 화면/API/외부연계 | `POST /api/v1/scheduler/solve` |  |
| 52 | REQ-SCH-002 | MN-SCH-020 | 스케줄 실행 | FN-SCH-006 | 스케줄 결과 승인/반영 | 계산된 스케줄 결과를 작업지시 및 생산계획에 반영한다. | 운영자 | 화면/API/DB | `POST /api/v1/scheduler/process-result` |  |
| 53 | REQ-SCH-003 | MN-SCH-030 | 솔버 설정 | FN-SCH-007 | 솔버 파라미터 조회/설정 | machine type parameter와 솔버 기본 옵션을 조회하고 화면에서 설정한다. | 운영자 | 화면/API | `GET /api/v1/scheduler/machine-type-params` | 설정 저장은 프론트 설정값 기준 |
| 54 | REQ-QLT-001 | MN-QLT-010 | 품질 대시보드 | FN-QLT-001 | 품질 요약 조회 | 검사 수, 합격률, 불합격률, NCR 현황 등 품질 요약을 조회한다. | 로그인 사용자 | 화면/API/DB | `GET /api/v1/quality/dashboard/summary` |  |
| 55 | REQ-QLT-002 | MN-QLT-020 | 검사계획 | FN-QLT-002 | 검사계획 조회 | 검사 유형, 품목, 페이지 조건으로 검사계획을 조회한다. | 로그인 사용자 | 화면/API/DB | `GET /api/v1/quality/inspection-plans`, `GET /inspection-plans/{product_id}` |  |
| 56 | REQ-QLT-002 | MN-QLT-020 | 검사계획 | FN-QLT-003 | 검사계획 등록/수정/삭제 | 품목, 공정, PMI, 특성, 기준값, USL/LSL, SPC 설정을 관리한다. | 품질관리자 | 화면/API/DB | `POST/PUT/DELETE /api/v1/quality/inspection-plans` |  |
| 57 | REQ-QLT-003 | MN-QLT-030 | 측정결과 | FN-QLT-004 | 검사결과 조회 | 작업지시, 검사계획, 기간 조건으로 측정 결과를 조회한다. | 로그인 사용자 | 화면/API/DB | `GET /api/v1/quality/inspection-results` |  |
| 58 | REQ-QLT-003 | MN-QLT-030 | 측정결과 | FN-QLT-005 | 검사결과 등록 | 측정값, 측정 장비, 측정 소스, 적합 여부, 메타데이터를 등록한다. | 품질관리자/검사자 | 화면/API/DB | `POST /api/v1/quality/inspection-results`, `POST /batch` |  |
| 59 | REQ-QLT-004 | MN-QLT-040 | SPC 차트 | FN-QLT-006 | SPC 차트 조회 | 검사 특성별 SPC 차트와 데이터 포인트를 조회한다. | 로그인 사용자 | 화면/API/DB | `GET /api/v1/quality/spc/charts/{characteristic}` |  |
| 60 | REQ-QLT-004 | MN-QLT-040 | SPC 차트 | FN-QLT-007 | 공정능력 분석 | SPC 데이터 기반 공정능력 지표를 조회하고 차트 분석을 수행한다. | 품질관리자 | 화면/API/DB | `GET /api/v1/quality/spc/capability`, `POST /spc/charts/{chart_id}/analyze` |  |
| 61 | REQ-QLT-005 | MN-QLT-050 | NCR 관리 | FN-QLT-008 | NCR 조회/등록 | 부적합 보고서를 조회하고 검사결과 또는 수동 입력 기준으로 등록한다. | 품질관리자/운영자 | 화면/API/DB | `GET /api/v1/quality/ncr`, `POST /api/v1/quality/ncr` |  |
| 62 | REQ-QLT-005 | MN-QLT-050 | NCR 관리 | FN-QLT-009 | NCR 수정/상태변경 | 부적합 내용, 원인, 조치, 담당자, 상태를 수정한다. | 품질관리자 | 화면/API/DB | `PUT /api/v1/quality/ncr/{ncr_id}`, `PATCH /status` |  |
| 63 | REQ-QLT-006 | MN-QLT-030 | 측정결과 | FN-QLT-010 | 품질 추적성 조회 | 개별 serial number 기준으로 품질 추적 정보를 조회한다. | 로그인 사용자 | API/DB | `GET /api/v1/quality/traceability/{serial_no}` |  |
| 64 | REQ-ANL-001 | MN-ANL-010 | 분석 대시보드 | FN-ANL-001 | KPI/OEE 분석 | OEE, availability, performance, quality, 생산량, 불량률, 다운타임을 조회한다. | 로그인 사용자 | 화면/API/DB | `GET /api/v1/analytics/kpi/summary`, `GET /api/v1/analytics/kpis` |  |
| 65 | REQ-ANL-001 | MN-ANL-010 | 분석 대시보드 | FN-ANL-002 | 생산 트렌드 분석 | 기간별 생산량, 품질, 사이클타임 트렌드를 조회한다. | 로그인 사용자 | 화면/API/DB | `GET /api/v1/analytics/production/trends`, `GET /api/v1/analytics/trends` |  |
| 66 | REQ-ANL-001 | MN-ANL-010 | 분석 대시보드 | FN-ANL-003 | 리소스 분석 | 설비/인력/자재 사용률을 조회한다. | 로그인 사용자 | 화면/API/DB | `GET /api/v1/analytics/resources` |  |
| 67 | REQ-ANL-002 | MN-ANL-020 | 설비 가동률 | FN-ANL-004 | 설비 가동률 조회 | 설비별 가동률, 기간별 utilization을 조회한다. | 로그인 사용자 | 화면/API/DB | `GET /api/v1/analytics/equipment/utilization`, `GET /equipment-utilization` |  |
| 68 | REQ-ANL-002 | MN-ANL-020 | 설비 가동률 | FN-ANL-005 | 설비 효율 상세 분석 | 선택 설비의 계획/실제 시간, 다운타임 breakdown, 효율 추세, 정비 계획을 조회한다. | 로그인 사용자 | 화면/API/DB | `GET /api/v1/analytics/equipment/efficiency` |  |
| 69 | REQ-ANL-003 | MN-ANL-030 | Lot 추적 | FN-ANL-006 | Lot 추적 목록 | 기간 조건으로 Lot 추적 목록을 조회한다. | 로그인 사용자 | 화면/API/DB | `GET /api/v1/analytics/lot-trace` |  |
| 70 | REQ-ANL-003 | MN-ANL-030 | Lot 추적 | FN-ANL-007 | Lot 상세 추적 | Lot 번호 기준으로 공정 흐름, 설비, 품질 체크포인트, 이력을 조회한다. | 로그인 사용자 | 화면/API/DB | `GET /api/v1/analytics/lot-trace/{lot_no}`, `GET /history`, `GET /traceability/{lot_no}` |  |
| 71 | REQ-NLM-001 | MN-NLM-010 | 채팅 | FN-NLM-001 | 자연어 질의 | 자연어 질문을 MES 데이터 조회 의도로 해석하고 결과를 반환한다. | 로그인 사용자 | 화면/API/DB/AI | `POST /api/v1/nlm/query` |  |
| 72 | REQ-NLM-001 | MN-NLM-010 | 채팅 | FN-NLM-002 | 질의 이력 조회 | 사용자의 자연어 질의 이력을 조회한다. | 로그인 사용자 | 화면/API | `GET /api/v1/nlm/history` |  |
| 73 | REQ-NLM-001 | MN-NLM-010 | 채팅 | FN-NLM-003 | 즐겨찾기 질의 관리 | 자주 쓰는 자연어 질의를 즐겨찾기에 등록, 삭제, 조회한다. | 로그인 사용자 | 화면/API | `POST/DELETE/GET /api/v1/nlm/favorites` |  |
| 74 | REQ-NLM-001 | MN-NLM-010 | 채팅 | FN-NLM-004 | 사용량 조회 | 자연어 질의 사용량/쿼터 정보를 조회한다. | 로그인 사용자 | 화면/API | `GET /api/v1/nlm/quota` |  |
| 75 | REQ-INT-001 | MN-MST-060 | n8n 에디터 | FN-INT-001 | n8n 에디터 연결 | 별도 n8n 편집기 URL을 새 탭으로 연결한다. | 관리자 | 화면/외부연계 | `NEXT_PUBLIC_N8N_EDITOR_URL` | 외부 시스템 |
| 76 | REQ-INT-002 | 시스템 | API | FN-INT-002 | P4R payload 미리보기 | Lot/작업/시나리오 기준 P4R 연계 payload를 미리 생성해 확인한다. | 로그인 사용자 | API/외부연계 | `GET /api/v1/integrations/dtp/p4r-payload/preview` |  |

## 4. 외부 시스템 연계

| 연계 대상 | 연계 방향 | 주요 기능 | 관련 기능 ID | 비고 |
| --- | --- | --- | --- | --- |
| 미들웨어/AAS | MES -> Middleware/AAS | 설비 동기화, 상태 조회, 작업 실행 패키지 제공, Unit 명령 전달 | FN-MST-017, FN-MST-019, FN-PRD-005, FN-PRD-009 | 설비/생산 실행 연계 |
| Cell Scheduler | MES -> Scheduler | 스케줄 요청 생성, 솔버 실행, 결과 반영 | FN-SCH-003 ~ FN-SCH-006 | 스케줄 계산 서비스 |
| Digital Thread Platform | MES -> DTP | 프로젝트 검색, 프로젝트 트리 조회, NC 파일 참조, P4R payload preview | FN-DT-001 ~ FN-DT-003, FN-INT-002 | DT 프로젝트/파일 연계 |
| n8n | MES -> n8n | 시나리오 편집기 변환, 외부 에디터 연결 | FN-MST-015, FN-INT-001 | YAML/n8n JSON 변환 |
| AI/NLM | MES -> AI/NLM | 자연어 질의, 질의 이력, 즐겨찾기, 쿼터 조회 | FN-NLM-001 ~ FN-NLM-004 | MES 데이터 질의 보조 |

## 5. 주요 상태값

| 구분 | 상태값 | 설명 |
| --- | --- | --- |
| 작업지시 | `READY` | 생성 후 실행 대기 |
| 작업지시 | `SCHEDULED` | 스케줄러 배정 완료 |
| 작업지시 | `RUNNING` | 생산 실행 중 |
| 작업지시 | `PAUSE` | 일시정지 |
| 작업지시 | `DONE` | 완료 |
| 작업지시 | `ERROR` | 오류 |
| 작업지시 | `CANCEL` | 취소 |
| Unit | `READY` | Unit 큐 대기 |
| Unit | `RUNNING` | Unit 실행 중 |
| Unit | `DONE` | Unit 완료 |
| Unit | `ERROR` | Unit 오류 |
| Unit | `SCENARIO_HOLD` | 시나리오 변경 대기 |
| 설비 | `RUN`, `IDLE`, `STOP`, `SETUP`, `ERROR`, `MAINTENANCE` | 설비 가동/대기/정지/셋업/오류/보전 상태 |
| 알람 | `ACTIVE`, `ACKNOWLEDGED`, `RESOLVED` | 발생/확인/해제 |
| 다운타임 | `PLANNED`, `UNPLANNED`, `SETUP` | 계획 정지/비계획 정지/셋업 |
| 검사 | `INCOMING`, `IN_PROCESS`, `FINAL`, `PERIODIC` | 입고/공정/최종/정기 검사 |
| NCR | `OPEN`, `IN_PROGRESS`, `CLOSED`, `VERIFIED`, `CANCELLED` | 부적합 처리 상태 |

## 6. 권한 기준

| 권한 | 설명 | 주요 사용 기능 |
| --- | --- | --- |
| 전체 | 로그인 전 접근 가능 | 로그인 |
| 로그인 사용자 | 인증된 일반 사용자 | 조회, 대시보드, 분석, 품질/생산 현황 확인 |
| 운영자 | 생산 현장 작업자 또는 운영 담당자 | 작업지시 시작, Unit 제어, 생산실적 등록, 알람 확인/해제 |
| 품질관리자 | 품질 업무 담당자 | 검사계획, 검사결과, SPC 분석, NCR 관리 |
| 관리자 | 기준정보 및 시스템 설정 담당자 | 마스터 CRUD, 설비 동기화, 시나리오 편집, 사용자 등록 정책 |
| 미들웨어 | 시스템 간 API 호출 주체 | Unit claim/complete, 작업정보 조회, 실행 패키지 조회 |

## 7. 작성 범위 및 제외 사항

| 구분 | 내용 |
| --- | --- |
| 포함 | 현재 메뉴에 노출된 화면 기능, 현재 API 라우터에 구현된 기능, 외부 연계용 시스템 API |
| 제외 | 향후 개발 예정 기능, 현재 화면/API로 제공되지 않는 기능, 내부 구현 이력 |
| 문서 형식 | 외부 업체 전달을 위해 메뉴/화면명, 기능명, 기능상세, 관련 API 중심으로 정리 |
