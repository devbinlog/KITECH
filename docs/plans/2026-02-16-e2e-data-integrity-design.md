# E2E 데이터 무결성 검증 보강 계획

**작성일**: 2026-02-16
**상태**: 분석/계획 단계
**현재 상태**: 58파일 755테스트 전체 통과

## 1. 현재 커버리지 분석

### 1.1 기존 검증 테스트 현황

| 파일 | 테스트 수 | 커버 영역 |
|------|----------|----------|
| `calculations.test.ts` | 6 | 수율, 진도율, 불량률 범위 검증 |
| `cross-module-workflow.test.ts` | 25 | 설비↔알람↔다운타임↔스케줄러 참조 |
| `data-integrity.test.ts` | ~10 | 생산 데이터 진도 자동계산, 수량 정합 |
| `business-rules.test.ts` | ~8 | 비즈니스 규칙 (상태전이, 필수필드) |
| `production-integrity.test.ts` | ~10 | 생산 데이터 구조 검증 |
| `manufacturing-integrity.test.ts` | ~12 | 제품↔WO 참조, 수량 rollup |
| `work-order-validation.test.ts` | ~8 | WO 상태값, 필드 유효성 |
| `crud-deep-validation.test.ts` | ~10 | CRUD 심층 검증, 고아 데이터 |

### 1.2 이미 커버되는 항목

**계산 정확성:**
- 수율 = ok_qty / (ok_qty + ng_qty) * 100 (±0.1% 허용)
- 진도율 = produced_qty / target_qty * 100 (±5% 허용)
- 불량률 = ng_qty / total * 100
- ok_qty + ng_qty = total_qty 정합

**참조 무결성:**
- 알람의 equipment_id가 설비 마스터에 존재
- 다운타임의 equipment_id가 설비 마스터에 존재
- 스케줄러 장비가 설비 마스터와 일치
- WO의 product가 제품 마스터에 존재

**파이프라인:**
- WO 생성 → 상태전이 (READY→RUNNING→DONE)
- 생산실적 등록 후 수량 반영
- 대시보드 KPI 카드 표시 확인

### 1.3 갭 분석 (현재 API 기준으로 실현 가능한 항목)

## 2. 보강 계획

### 2.1 Tier 1: calculations.test.ts 보강

**현재**: 수율/진도율/불량률 범위 검증만 있음
**보강할 내용**:

#### A. OEE 계산 검증
```
GET /analytics/kpi/summary 응답에서:
- OEE = availability × performance × quality (각 0~1 범위)
- 각 구성요소가 0~100% 범위인지
- OEE가 세 구성요소의 곱과 일치하는지
```

#### B. 다운타임 duration 계산 검증
```
GET /downtime 응답에서:
- 종료된 다운타임: duration_sec = (ended_at - started_at) 초
- 활성 다운타임: duration_sec가 null이거나 계속 증가
- duration이 음수가 아닌지
```

#### C. 설비 가동률 계산 검증
```
GET /analytics/equipment/utilization 응답에서:
- utilization_rate가 0~100% 범위
- 총 시간 = 가동시간 + 비가동시간 + 다운타임 (허용오차 내)
```

#### D. Edge case 계산
```
- total_qty = 0일 때 수율이 NaN/Infinity가 아닌지
- ng_qty만 있고 ok_qty = 0일 때 수율 = 0%
- ok_qty만 있고 ng_qty = 0일 때 수율 = 100%
```

### 2.2 Tier 2: cross-module-workflow.test.ts 보강

**현재**: 설비ID 참조만 체크
**보강할 내용**:

#### A. 생산실적 → 대시보드 KPI 반영 검증
```
1. GET /production/results 에서 최근 실적 합계 계산
2. GET /analytics/kpi/summary 에서 KPI 값 조회
3. 실적 합계와 KPI 값이 일관성 있는지 (같은 기간 기준)
```

#### B. 알람 → 다운타임 연관성 검증
```
1. GET /alarms/active 에서 활성 알람 설비 목록
2. GET /downtime?status=ACTIVE 에서 활성 다운타임 설비 목록
3. CRITICAL/EMERGENCY 알람이 있는 설비에 다운타임도 있는지 (선택적)
```

#### C. 스케줄러 WO → 생산 WO 일치 검증
```
1. GET /scheduler/work-orders 에서 스케줄된 WO 목록
2. GET /production/orders 에서 WO 목록
3. 스케줄된 WO가 실제 생산 WO에 존재하는지
```

### 2.3 Tier 3: business-rules.test.ts 보강

**현재**: 기본 상태전이만 체크
**보강할 내용**:

#### A. WO 상태 머신 무결성
```
- READY인 WO만 RUNNING으로 전이 가능
- RUNNING인 WO만 DONE/PAUSE로 전이 가능
- DONE인 WO는 다른 상태로 전이 불가
- 현재 WO들의 상태가 유효한 값인지 (READY/RUNNING/PAUSE/DONE/ERROR)
```

#### B. NCR 상태 전이 규칙
```
- OPEN → INVESTIGATING → CORRECTIVE_ACTION → CLOSED 순서
- CLOSED된 NCR에 resolution_note가 있는지
- 현재 NCR들의 상태가 유효한 값인지
```

#### C. 알람 심각도 → 대응 수준 매칭
```
- CRITICAL/EMERGENCY 알람이 오래 방치되지 않았는지
- 해결된 알람에 resolved_by가 있는지
```

### 2.4 Tier 4: data-integrity.test.ts 보강

**현재**: 진도율 자동계산, 수량 정합
**보강할 내용**:

#### A. Lot 번호 추적성
```
1. GET /production/orders 에서 lot_no 추출
2. GET /analytics/lot-trace/{lot_no} 로 추적
3. 추적 결과에 해당 WO가 포함되는지
```

#### B. 설비 상태 이력 연속성
```
1. GET /masters/equipments/{id}/status-history
2. 상태 이력이 시간순으로 정렬되어 있는지
3. 같은 상태가 연속으로 중복 기록되지 않았는지
```

#### C. 생산실적 → WO 수량 rollup 정확성
```
1. 특정 WO의 생산실적 합계 (sum of ok_qty)
2. WO의 completed_qty와 비교
3. 차이가 허용오차(±1) 내인지
```

## 3. 실현 가능성 체크 (확인 필요)

아래 API가 실제로 데이터를 반환하는지 서버 실행 후 확인 필요:

| API | 용도 | 확인 상태 |
|-----|------|----------|
| `GET /analytics/kpi/summary` | OEE 계산 검증 | 기존 테스트에서 사용됨 ✓ |
| `GET /analytics/equipment/utilization` | 가동률 검증 | 기존 테스트에서 사용됨 ✓ |
| `GET /downtime` | 다운타임 duration | 기존 테스트에서 사용됨 ✓ |
| `GET /scheduler/work-orders` | 스케줄-WO 매칭 | scheduler-data-integrity에서 사용, 그레이스풀 처리 |
| `GET /analytics/lot-trace/{lot_no}` | Lot 추적성 | analytics.py에 정의됨 ✓ |
| `GET /masters/equipments/{id}/status-history` | 설비 이력 | equipments.py에 정의됨 ✓ |
| `GET /downtime/summary` | 다운타임 요약 | downtime.py에 정의됨 ✓ |

## 4. 보강하지 않는 항목 (이유)

| 항목 | 이유 |
|------|------|
| BOM/자재 소모 | 현재 API에 BOM 엔드포인트 없음 |
| 원가/예산 추적 | 현재 API에 원가 엔드포인트 없음 |
| 구매/공급업체 | 현재 시스템 범위 밖 |
| 유지보수 스케줄 | 별도 유지보수 모듈 없음 |
| FPY (First Pass Yield) | API에서 first_pass 구분 필드 없음 |
| WIP 재공품 추적 | 공정별 입출고 API 없음 |

## 5. 실제 구현 결과

| Tier | 파일 | Before | After | 추가 | 결과 |
|------|------|--------|-------|------|------|
| Tier 1 | calculations.test.ts | 6 | 21 | +15 | ALL PASSED |
| Tier 2 | cross-module-workflow.test.ts | 25 | 35 | +10 | ALL PASSED |
| Tier 3 | business-rules.test.ts | 6 | 16 | +10 | ALL PASSED |
| Tier 4 | data-integrity.test.ts | 10 | 18 | +8 | ALL PASSED |
| **합계** | **4개 기존 파일** | **47** | **90** | **+43** | **ALL PASSED** |

### 추가된 검증 항목 상세

**Tier 1 (calculations.test.ts +15)**:
- OEE 계산: 구성요소 범위, A*P*Q 공식, defect_rate, downtime_hours, trend_data 정렬
- 설비 가동률: rate 범위, 시간합=planned, running/planned≈utilization, 음수 없음
- 다운타임: duration>=0, duration=end-start, 활성 다운타임 end_time 없음, summary 합계
- Edge case: NaN/Infinity 없음, 음수 수량 없음, target_qty=0 진도율

**Tier 2 (cross-module-workflow.test.ts +10)**:
- 생산실적→KPI: total_production 일치, defect_rate 일관성, quality≈100-defect_rate
- 알람-다운타임: resolved_by, acknowledged_at, summary↔list count 일치
- 스케줄러-생산: MES WO 참조, product_id 유효성, results→WO 참조

**Tier 3 (business-rules.test.ts +10)**:
- WO 상태 머신: DONE→완료 증빙, READY 상태 실적거부, 필수 필드
- NCR 상태 전이: 유효 상태값, CLOSED→resolution, 필수 필드
- 알람 심각도: 유효 심각도, resolved→resolved_by, definition 참조
- 검사계획: USL>=Nominal>=LSL

**Tier 4 (data-integrity.test.ts +8)**:
- Lot 추적성: Lot Trace API 조회, lot_no 형식 일관성
- 설비 상태 이력: 시간순 정렬, 유효 상태값, status API 필수 필드
- 생산실적→WO rollup: completed_qty 일치, running WO target 이내
- 마스터 데이터: routing→std-processes 참조, 제품 필수 필드

## 6. TypeScript 정적분석 수정 (부산물)

| 파일 | 수정 내용 |
|------|----------|
| `types/index.ts` | QualityFilters에 work_order_id, inspection_plan_id, status, offset 추가 |
| `downtime/page.tsx` | "COMPLETED" → "completed" (타입 대소문자 불일치) |
| `alarms/page.tsx` | MutationFunction 시그니처 수정 |
| `quality/inspection-results/page.tsx` | result 파라미터 타입 명시 |
| `quality/ncr/page.tsx` | ncr 파라미터 타입 + keyof 캐스팅 |

## 7. 완료 상태

- [x] 서버 실행 상태에서 각 API 응답 구조 확인
- [x] Tier 1 구현 및 검증 (21/21 PASSED)
- [x] Tier 2 구현 및 검증 (35/35 PASSED)
- [x] Tier 3 구현 및 검증 (16/16 PASSED)
- [x] Tier 4 구현 및 검증 (18/18 PASSED)
- [x] TypeScript 정적분석 오류 수정 (app-level 0 errors)
