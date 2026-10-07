# agents-workspace TODO

> 생성일: 2026-02-04
> 마지막 업데이트: 2026-02-18

---

## ✅ 완료된 항목 (2026-02-18)

### Bug Safari - 전체 23페이지 수동/코드 인스펙션 (2026-02-18) ✅
- [x] Batch 1: Login + Dashboard (2 pages) — BUG #1 console.log 발견/수정
- [x] Batch 2: Master Data (5 pages) — 이상 없음
- [x] Batch 3: Production + Downtime + Alarms (4 pages) — BUG #2 downtime duration, BUG #3 alarm borderLeftColor 수정
- [x] Batch 4: Scheduler (3 pages) — 이상 없음
- [x] Batch 5: Quality (5 pages) — BUG #4-6 dynamic Tailwind, console.warn, SPC division by zero 수정
- [x] Batch 6: Analytics + Chat (4 pages) — BUG #7-11 dynamic Tailwind, Recharts recursive shape, console.error, null safety, negative duration 수정
- [x] **총 11개 버그 발견 및 수정, 452 unit tests 통과 확인**

### Frontend Unit Test 확장 (2026-02-17~18) ✅
- [x] 5파일(66개) → 33파일(452개) 확장 완료
- [x] Services: alarm, auth, quality, equipment, master, production, downtime, scheduler, analytics, nlm (10파일)
- [x] Stores: chatStore, authStore (2파일)
- [x] Lib/Config: errorHandler, axios, constants (3파일)
- [x] Hooks: useScheduler, useSchedulerConstants (2파일)
- [x] Components: LoadingState, ErrorBoundary, ConnectionBadge, SortableHeader, ConnectionStatus, QuickActions, JsonModal, KPICard(dynamic), DynamicDataTable, StatusGrid, StatusCards, DynamicRenderer, KPICard(analytics), EquipmentCard, scheduler-utils, errorMessages (16파일)

### W1-W6 워크플로우 버그 수정 (2026-02-17) ✅
- [x] W1: Stale data after cross-page mutations — 쿼리 무효화 추가
- [x] W2: Missing loading/error states
- [x] W3: Timezone/locale inconsistency
- [x] W4: Accessibility improvements
- [x] W5: Form validation gaps
- [x] W6: Console.log cleanup

### Production Management Enhancement (2026-02-17) ✅
- [x] Work Order Detail Modal (Eye icon → 상세 모달)
- [x] Progress Bar in Orders List (진척률 표시)
- [x] WO Filter on Results Page (작업지시별 필터)

## ✅ 완료된 항목 (2026-02-08)

### 코드베이스 감사 (2026-02-08) ✅
- [x] Ruff 린팅: All checks passed
- [x] bare except → Exception 수정 (2곳)
- [x] E402 noqa 처리 (3곳)
- [x] 전체 테스트: 1,034 passed, 35 skipped
- [x] CHANGELOG.md 생성
- [x] 문서 날짜 업데이트

## ✅ 완료된 항목 (2026-02-07)

### SPC 기능 ✅
- [x] `SPCChart` 모델 (chart_type, subgroup_size, ucl, cl, lcl, cp, cpk)
- [x] `SPCDataPoint` 모델 (subgroup_no, x_bar, r_value, is_out_of_control)
- [x] `spc_service.py` (X-bar R 차트 계산, 관리한계, Cp/Cpk)
- [x] Western Electric Rules 8가지 전부 구현
- [x] SPC API 엔드포인트

### QMS 기능 ✅
- [x] `InspectionPlan` 모델
- [x] `InspectionResult` 모델
- [x] `NonConformance` (NCR) 모델
- [x] `quality_service.py` - 검사/NCR 관리
- [x] Quality API 엔드포인트 15+개

### Frontend UI ✅
- [x] Quality 대시보드, 검사계획, 측정결과, SPC 차트, NCR 관리
- [x] Analytics KPI 대시보드, 설비 가동률, Lot 추적
- [x] React 최적화 (memo, useCallback, useMemo)
- [x] ErrorBoundary, LoadingState, ConnectionStatus 컴포넌트
- [x] MES UX 패턴 적용

### 코드 정리 ✅
- [x] MES v5 스키마 마이그레이션 (job_id 제거)
- [x] Ruff lint/format
- [x] Pydantic v2 마이그레이션
- [x] 문서 정리 (docs/ 폴더)

---

## 1. 🐳 컨테이너화

- [ ] `services/mes/Dockerfile` 작성
- [ ] `services/gateway/Dockerfile` 작성
- [ ] `services/scheduler/Dockerfile` 작성
- [ ] `services/collector/Dockerfile` 작성
- [ ] `docker-compose.yml` 작성
- [ ] `docker-compose.dev.yml` (개발용 오버라이드)
- [ ] 볼륨 마운트 설정 (libs/, shared/)
- [ ] 헬스체크 설정
- [ ] 서비스간 네트워크 (agents-net)

---

## 2. 📁 프로젝트 구조 마이그레이션

### Services (컨테이너)
- [ ] `agents/cell-mes/` → `services/mes/`
- [ ] `agents/nl-router/` → `services/gateway/`
- [ ] `agents/cell-scheduler/` → `services/scheduler/`
- [ ] (신규) `services/collector/` 생성

### Libraries (패키지)
- [ ] `agents/gcode-parser/` → `libs/gcode-parser/`
- [ ] `agents/cam-runner/` → `libs/cam-runner/`
- [ ] `agents/step-pmi-reader/` → `libs/step-pmi-reader/`
- [ ] `agents/monitoring-data-replayer/` → `libs/monitoring-replayer/`
- [ ] `agents/digital-thread-project-manager/` → `libs/digital-thread/`
- [ ] `agents/cell-schedule-visualizer/` → `libs/schedule-viz/`

### Shared
- [ ] `shared/models/` 공유 Pydantic 모델 분리
- [ ] `shared/config/` 공통 설정
- [ ] `shared/utils/` 유틸리티

---

## 3. 📏 measurement-collector 서비스

> OMM/Equator 등 하위단에서 데이터 수집

### OMM Collector
- [ ] DPRNT 파일 파싱 (Renishaw Inspection Plus)
- [ ] 매크로 변수 읽기 (FOCAS/MTConnect)
- [ ] 측정 결과 → MES 전송
- [ ] 자동 공구 보정 트리거

### Equator Collector
- [ ] CSV 출력 파싱
- [ ] XML 출력 파싱 (MODUS)
- [ ] Q-DAS DFQ 포맷 파싱
- [ ] EZ-IO 자동화 연동

---

## 4. 🔗 Digital Thread 연계

### PMI → 검사계획 자동생성
- [ ] `generate_inspection_plan_from_pmi()` 함수
- [ ] step-pmi-reader 결과 → InspectionPlan 자동 생성
- [ ] 공차 → USL/LSL 변환

### 전체 추적성 쿼리
- [ ] `get_full_traceability(serial_no)` 함수
- [ ] design → cam → machining → inspection → quality 연결

### API
- [ ] `POST /api/v1/quality/inspection-plans/generate-from-pmi`
- [ ] `GET /api/v1/quality/traceability/{serial_no}`

---

## 5. 📄 QIF 변환기 (선택)

### PMI → QIF 변환
- [ ] `qif_converter.py` 모듈 생성
- [ ] step-pmi-reader JSON → QIF XML 변환

### QIF 문서 타입
- [ ] QIFPlan - 검사계획 정의
- [ ] QIFResults - 측정결과
- [ ] QIFStatistics - SPC 데이터

---

## 6. 🔄 Closed-Loop 피드백

### 모델
- [ ] `ToolOffsetHistory` 모델

### OMM 자동 보정
- [ ] 편차 임계값 설정
- [ ] 자동 보정값 계산
- [ ] FOCAS/MTConnect로 오프셋 전송

### SPC 알림
- [ ] 관리 이탈 시 알림 발송
- [ ] 추세 감지 시 경고

---

## 📅 구현 우선순위

| 순서 | 항목 | 예상 기간 | 상태 |
|------|------|----------|------|
| ~~1~~ | ~~SPC/QMS 기능~~ | ~~3-4일~~ | ✅ 완료 |
| ~~2~~ | ~~Quality/Analytics UI~~ | ~~2-3일~~ | ✅ 완료 |
| ~~2.5~~ | ~~Frontend 품질 보증 (Unit Test + Bug Safari)~~ | ~~2일~~ | ✅ 완료 |
| ~~2.6~~ | ~~W1-W6 워크플로우 버그 수정~~ | ~~1일~~ | ✅ 완료 |
| ~~2.7~~ | ~~Production Enhancement (Detail Modal, Progress Bar, WO Filter)~~ | ~~1일~~ | ✅ 완료 |
| 3 | 프로젝트 구조 마이그레이션 | 1-2일 | 대기 |
| 4 | measurement-collector | 1주 | 대기 |
| 5 | Digital Thread 연계 | 3-4일 | 대기 |
| 6 | QIF 변환기 (선택) | 2-3일 | 대기 |
| 7 | Closed-Loop 피드백 | 3-4일 | 대기 |
| 8 | 컨테이너화 | 2-3일 | 대기 |

---

## 📚 참고 문서

- `DIGITAL_THREAD_SPC_QMS.md` - 기술 설계 상세
- `docs/plans/` - 설계 문서 디렉토리 (아래 참조)

---

## 📋 설계 문서 현황

| 파일 | 상태 | 내용 |
|------|------|------|
| `2026-02-15-frontend-testing-overhaul-design.md` | ✅ 구현 완료 | E2E 테스트 리팩터링 + Bug Safari 설계 |
| `2026-02-15-phase1-bug-safari.md` | ✅ 구현 완료 | Bug Safari 23페이지 실행 계획 |
| `2026-02-15-vitest-migration-design.md` | ✅ 구현 완료 | Playwright → Vitest 4.x 마이그레이션 |
| `2026-02-15-vitest-migration.md` | ✅ 구현 완료 | Vitest 마이그레이션 실행 가이드 |
| `2026-02-16-e2e-data-integrity-design.md` | 미구현 (선택) | E2E 데이터 무결성 검증 보강 |
| `2026-02-16-scheduler-workflow-design.md` | ✅ 구현 완료 | 스케줄링 수립자 워크플로우 (3모드) |
| `2026-02-17-production-enhancement-design.md` | ✅ 구현 완료 | WO Detail Modal, Progress Bar, WO Filter |
| `2026-02-17-workflow-bugs-design.md` | ✅ 구현 완료 | W1-W6 워크플로우 버그 수정 |

---

*마지막 업데이트: 2026-02-18*
