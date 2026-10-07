# Cell-MES UI 테스트 체크리스트

> 생성일: 2026-02-07
> 마지막 업데이트: 2026-02-18
> 총 23개 페이지 | Unit: **452 passed (33 files)** | E2E: **~798 tests (58 files)**
>
> **Bug Safari (2026-02-18)**: 전체 23페이지 수동/코드 인스펙션 완료. 11개 버그 발견 및 수정.

## E2E 테스트 실행 방법

```bash
cd agents/cell-mes/frontend
npm run test:e2e          # 전체 실행
npm run test:e2e:ui       # UI 모드
npm run test:e2e:report   # HTML 리포트
```

**사전 조건**: Backend (port 8000) 실행 중이어야 함. Frontend는 Playwright가 자동 시작.

---

## 1. 대시보드 (`/`)

### 표시 항목
- [x] 전체 설비 수 표시 — `dashboard.spec.ts`, `manager-overview.spec.ts`
- [x] 가동중 설비 수 표시 — `dashboard.spec.ts`, `manager-overview.spec.ts`
- [x] 진행중 작업 수 표시 — `dashboard.spec.ts`, `manager-overview.spec.ts`
- [x] 완료 작업 수 표시 — `dashboard.spec.ts`, `manager-overview.spec.ts`
- [x] 설비 현황 카드 (각 설비별 상태) — `manager-overview.spec.ts`
- [x] 최근 작업지시 테이블 — `planner-daily.spec.ts`
- [x] AI 인사이트 섹션 — `manager-overview.spec.ts`

### 기능
- [x] 자동 갱신 표시 확인 — `manager-overview.spec.ts`
- [ ] 설비 카드 클릭 시 상세 정보
- [ ] AI 새로고침 버튼 동작

---

## 2. 표준공정 (`/master/processes`)

### 표시 항목
- [x] 공정 목록 테이블 — `master.spec.ts`
- [x] 공정 ID, 이름, 설비 타입, 사이클타임 — `master.spec.ts`

### 기능
- [x] 공정 추가 (Create) — `critical-workflows.spec.ts`
- [ ] 공정 수정 (Update)
- [x] 공정 삭제 (Delete) — `critical-workflows.spec.ts`
- [ ] 검색/필터

---

## 3. 제품관리 (`/master/products`)

### 표시 항목
- [x] 제품 목록 테이블 — `master.spec.ts`
- [x] 제품 코드, 이름, 설명 — `master.spec.ts`

### 기능
- [x] 제품 추가 (Create) — `critical-workflows.spec.ts`
- [ ] 제품 수정 (Update)
- [x] 제품 삭제 (Delete) — `critical-workflows.spec.ts`
- [ ] 검색/필터

---

## 4. 라우팅설계 (`/master/routings`)

### 표시 항목
- [x] 라우팅 목록 — `master.spec.ts`
- [x] 제품별 공정 순서 — `master.spec.ts`

### 기능
- [ ] 라우팅 추가
- [ ] 공정 순서 지정
- [ ] 라우팅 수정/삭제

---

## 5. 물류시나리오 (`/master/scenarios`)

### 표시 항목
- [x] 시나리오 목록 — `master.spec.ts`
- [x] 출발지/도착지 정보 — `master.spec.ts`

### 기능
- [ ] 시나리오 추가
- [ ] 시나리오 수정/삭제

---

## 6. 설비관리 (`/master/equipments`)

### 표시 항목
- [x] 설비 목록 테이블 — `master.spec.ts`
- [x] 설비명, 타입, 상태, AAS ID — `master.spec.ts`
- [ ] 연결 설정 정보

### 기능
- [x] 설비 추가 (Create) — `critical-workflows.spec.ts`
- [ ] 설비 수정 (Update)
- [x] 설비 삭제 (Delete) — `critical-workflows.spec.ts`
- [ ] 상태 변경 (가동/정지)
- [x] 설비 상세 모달 — `operator-daily.spec.ts`

---

## 7. 작업지시 (`/production/orders`)

### 표시 항목
- [x] 작업지시 목록 테이블 — `production.spec.ts`
- [x] WO ID, Lot No, 제품, 수량, 상태 — `production.spec.ts`
- [ ] 시작일/종료일

### 기능
- [x] 작업지시 생성 — `critical-workflows.spec.ts`, `planner-daily.spec.ts`
- [x] 상태 변경 (WAITING -> IN_PROGRESS -> DONE) — `operator-daily.spec.ts`
- [ ] 작업지시 수정/삭제
- [ ] 날짜 필터
- [x] 상태 필터 (탭) — `planner-daily.spec.ts`

---

## 8. 생산실적 (`/production/results`)

### 표시 항목
- [x] 실적 목록 테이블 — `production.spec.ts`
- [x] 통계 카드 (총 실적) — `planner-daily.spec.ts`, `manager-overview.spec.ts`
- [ ] 양품/불량 수량 상세

### 기능
- [x] 실적 조회 — `planner-daily.spec.ts`
- [ ] 기간별 필터
- [ ] 설비별 필터
- [ ] CSV 내보내기

---

## 9. 스케줄러 (`/scheduler`, `/scheduler/execute`, `/scheduler/settings`)

### 9-1. 스케줄 현황 (`/scheduler`)
- [x] 날짜 선택기 + "오늘" 버튼 — `scheduler.spec.ts`
- [x] 요약 카드 3개 (설비, 작업지시, 진행중) — `scheduler.spec.ts`
- [x] 간트 차트 또는 빈 상태 — `scheduler.spec.ts`, `role-scheduler.spec.ts`
- [x] 설비별 레인 표시 — `role-scheduler.spec.ts`

### 9-2. 스케줄 실행 (`/scheduler/execute`)
- [x] 워크플로우 상태 배지 (대기/실행중/검토중/승인중/완료) — `scheduler.spec.ts`
- [x] 상태 카드 3개 (가용 설비, 대기 작업지시, 결과) — `scheduler.spec.ts`
- [x] 솔버 선택 드롭다운 (5개 옵션) — `scheduler.spec.ts`, `planner-daily.spec.ts`
- [x] 계획 기간/시간 제한/진행중 포함 설정 — `scheduler.spec.ts`
- [x] 스케줄 실행 버튼 — `scheduler.spec.ts`, `role-scheduler.spec.ts`
- [x] 결과 통계 (Makespan, 가동률, 작업수, 실행시간) — `scheduler.spec.ts`
- [x] 승인/취소/다시실행 버튼 — `scheduler.spec.ts`
- [x] 가용 설비/대기 작업지시 테이블 — `scheduler.spec.ts`
- [x] JSON 모달 뷰어 — `scheduler.spec.ts`

### 9-3. 솔버 설정 (`/scheduler/settings`)
- [x] 설정 페이지 로드 — `scheduler.spec.ts`, `role-scheduler.spec.ts`
- [x] 솔버 옵션 표시 — `role-scheduler.spec.ts`

---

## 10. 품질관리 대시보드 (`/quality`)

### 표시 항목
- [x] 품질 KPI 카드들 (총 검사건수, 합격률) — `quality-engineer.spec.ts`
- [x] 검사 현황 요약 — `quality-engineer.spec.ts`
- [x] NCR 현황 요약 — `manager-overview.spec.ts`
- [ ] SPC 요약

### 기능
- [x] 날짜 필터 변경 — `quality-engineer.spec.ts`

---

## 11. 검사계획 (`/quality/inspection-plans`)

### 표시 항목
- [x] 검사계획 목록 — `quality-engineer.spec.ts`
- [x] 제품, 특성, 규격(USL/LSL), 검사 타입 — `quality-engineer.spec.ts`

### 기능
- [x] 검사계획 추가 (모달 폼 확인) — `quality-engineer.spec.ts`
- [ ] 검사계획 수정/삭제
- [ ] 제품별 필터

---

## 12. 측정결과 (`/quality/inspection-results`)

### 표시 항목
- [x] 측정결과 목록 — `quality-engineer.spec.ts`
- [x] 계획, 측정값, 적합여부 — `quality-engineer.spec.ts`
- [ ] Lot No, Serial No 상세

### 기능
- [x] 측정결과 입력 (수동) — `quality-engineer.spec.ts`
- [x] 측정결과 조회 — `quality-engineer.spec.ts`
- [ ] 적합/부적합 필터
- [x] 기간별 필터 — `quality-engineer.spec.ts`

---

## 13. SPC 차트 (`/quality/spc`)

### 표시 항목
- [x] SPC 페이지 접근 확인 — `manager-overview.spec.ts`
- [ ] X-bar R 차트
- [ ] 관리한계선 (UCL, CL, LCL)
- [ ] Cp/Cpk 값
- [ ] 이탈 포인트 표시

### 기능
- [ ] 특성 선택
- [ ] 기간 선택
- [ ] Western Electric Rules 위반 표시
- [ ] 관리한계 재계산

---

## 14. NCR 관리 (`/quality/ncr`)

### 표시 항목
- [x] NCR 목록 — `quality-engineer.spec.ts`
- [x] NCR 번호, 결함 유형, 상태 — `quality-engineer.spec.ts`
- [ ] 처리 방법 (REWORK, SCRAP 등)

### 기능
- [x] NCR 생성 — `critical-workflows.spec.ts`, `quality-engineer.spec.ts`
- [x] NCR 상태 변경 (OPEN -> IN_PROGRESS -> CLOSED) — `critical-workflows.spec.ts`
- [ ] 처리 방법 지정
- [ ] 근본원인/시정조치 입력
- [ ] 상태별 필터

---

## 15. 분석리포트 대시보드 (`/analytics`)

### 표시 항목
- [x] 생산 KPI 카드 (전체 OEE, 가용성, 성능효율, 품질지수) — `critical-workflows.spec.ts`, `planner-daily.spec.ts`
- [x] 트렌드 차트 (Recharts) — `critical-workflows.spec.ts`
- [ ] 설비 가동률 요약

### 기능
- [ ] 기간 선택
- [ ] KPI 새로고침

### Backend API 상태
- [x] `GET /api/v1/analytics/kpi/summary` — 구현 완료
- [x] `GET /api/v1/analytics/production/trends` — 구현 완료
- [x] `GET /api/v1/analytics/resources` — 구현 완료

---

## 16. 설비 가동률 (`/analytics/equipment`)

### 표시 항목
- [x] 설비별 가동률 차트 — `critical-workflows.spec.ts`, `planner-daily.spec.ts`
- [x] 평균 가동률 통계 — `planner-daily.spec.ts`
- [ ] OEE (가동률, 성능, 품질) 개별 표시
- [ ] 시간별/일별 트렌드

### 기능
- [x] 설비 선택 드롭다운 — `planner-daily.spec.ts`
- [ ] 기간 선택
- [ ] 상세 분석

### Backend API 상태
- [x] `GET /api/v1/analytics/equipment/utilization` — 구현 완료
- [x] `GET /api/v1/analytics/equipment/efficiency` — 구현 완료

---

## 17. Lot 추적 (`/analytics/lot-trace`)

### 표시 항목
- [x] Lot 추적 테이블 — `critical-workflows.spec.ts`, `quality-engineer.spec.ts`
- [ ] Lot 이력 타임라인
- [ ] 공정별 진행 상황
- [ ] 관련 설비, 작업자 정보

### 기능
- [x] Lot 목록 조회 — `quality-engineer.spec.ts`
- [x] Lot 상세 보기 버튼 — `quality-engineer.spec.ts`
- [ ] Lot No 검색
- [ ] 전체 이력 조회
- [ ] 품질 데이터 연결

### Backend API 상태
- [x] `GET /api/v1/analytics/lot-trace` — 구현 완료
- [x] `GET /api/v1/analytics/lot-trace/{lot_no}` — 구현 완료
- [x] `GET /api/v1/analytics/lot-trace/{lot_no}/history` — 구현 완료

---

## 18. AI 어시스턴트 (`/chat`)

### 표시 항목
- [x] 채팅 인터페이스 접근 확인 — `manager-overview.spec.ts`
- [ ] 메시지 히스토리

### 기능
- [ ] 자연어 질문 입력 — *NL-Router 서비스 필요*
- [ ] AI 응답 표시
- [ ] 생산 관련 질의 처리

---

## 공통 기능

### 인증
- [x] 로그인 (`/login`) — `auth.spec.ts`
- [x] 로그아웃 — `auth.spec.ts`
- [ ] 토큰 만료 시 자동 로그아웃
- [ ] 권한별 접근 제어

### UI/UX
- [ ] 반응형 레이아웃
- [x] 로딩 상태 표시 — 모든 페이지에서 검증
- [x] 에러 메시지 표시 — `critical-workflows.spec.ts`
- [ ] 토스트 알림
- [x] 사이드바 네비게이션 — `dashboard.spec.ts`

### 데이터
- [ ] 페이지네이션
- [ ] 정렬 기능
- [ ] 필터 기능
- [ ] 새로고침

### 에러 처리
- [x] 존재하지 않는 페이지 -> 404 또는 리다이렉트 — `critical-workflows.spec.ts`
- [x] 빈 페이지가 아닌지 확인 (body text length > 10) — `critical-workflows.spec.ts`

---

## 테스트 우선순위

### P0 (필수) - E2E 커버리지: 100%
1. [x] 로그인/로그아웃
2. [x] 작업지시 CRUD
3. [x] 생산실적 조회
4. [x] 품질 검사 결과 입력

### P1 (중요) - E2E 커버리지: ~75%
5. [x] 스케줄러 연동 (UI 확인, 실행은 skip)
6. [x] SPC 차트 표시 (페이지 접근 확인)
7. [x] NCR 생성/처리
8. [x] 설비 관리

### P2 (일반) - E2E 커버리지: ~70%
9. [x] 마스터 데이터 관리 (CRUD)
10. [x] Analytics 대시보드 (KPI, 차트)
11. [x] AI 채팅 (접근 확인)
12. [x] Lot 추적 (목록/상세)

---

## E2E 테스트 파일 구조

```
e2e/
  fixtures/auth.ts          # 인증 fixture (auto-login)
  utils/api-helper.ts       # API 유틸리티 (데이터 검증용)
  auth.spec.ts              # 인증 테스트
  dashboard.spec.ts         # 대시보드 테스트
  production.spec.ts        # 생산 관련 테스트
  analytics.spec.ts         # 분석 테스트
  master.spec.ts            # 마스터 데이터 테스트
  quality.spec.ts           # 품질 관리 테스트
  scenarios/
    critical-workflows.spec.ts   # 핵심 워크플로우 (CRUD, 상태전이, 에러처리)
    operator-daily.spec.ts       # CNC 작업자 일일 업무 시나리오
    planner-daily.spec.ts        # 생산계획 담당자 시나리오
    quality-engineer.spec.ts     # 품질관리 담당자 시나리오
    manager-overview.spec.ts     # 관리자/팀장 모니터링 시나리오
  validation/
    ai-validation.spec.ts        # AI 기능 검증 (NL-Router 필요, skip)
    cross-screen-validation.spec.ts  # 크로스 화면 데이터 검증
    scheduler-validation.spec.ts     # 스케줄러 검증 (서비스 필요, skip)
    work-order-validation.spec.ts    # 작업지시 데이터 검증
```

## Skip된 테스트 (4건)

| 테스트 | 이유 | 해결 방법 |
|---|---|---|
| AI validation tests (2건) | NL-Router 서비스 미실행 | NL-Router 서비스 시작 후 실행 |
| Scheduler validation (1건) | 스케줄러 서비스 미실행 | 스케줄러 서비스 시작 후 실행 |
| Cross-screen NL validation (1건) | NL-Router 서비스 미실행 | NL-Router 서비스 시작 후 실행 |

---

*마지막 업데이트: 2026-02-18*
