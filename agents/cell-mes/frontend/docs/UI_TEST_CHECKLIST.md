# Cell-MES UI 테스트 체크리스트

## 📊 테스트 현황 요약

| 카테고리 | 파일 수 | 테스트 수 | 상태 |
|----------|---------|-----------|------|
| 역할별 시나리오 | 17 | ~250 | ✅ 완료 |
| 데이터 정합성 | 10 | ~150 | ✅ 완료 |
| 기본 기능 | 18 | ~200 | ✅ 완료 |
| **총계** | **45** | **~600** | ✅ |

---

## 🎭 역할별 테스트

### 1. 생산관리자 (role-production-manager.spec.ts)
- [x] 작업지시 목록 조회/필터/탭 전환
- [x] 작업지시 생성 (폼 검증, 연속 생성)
- [x] 상태 전이 (WAITING → IN_PROGRESS → COMPLETED)
- [x] 수량 변경 후 스케줄러 연동
- [x] 우선순위 및 일정 관리
- [x] 비정상 케이스 (음수, 중복 Lot, 미래날짜)

### 2. 현장작업자 (role-operator.spec.ts)
- [x] 오늘 작업 목록 조회
- [x] 실적 등록 (양품/불량)
- [x] 연속 실적 등록 (5건)
- [x] 설비 상태 확인
- [x] 비정상 케이스 (수량 미입력, 목표 초과)

### 3. 품질관리자 (role-quality-manager.spec.ts)
- [x] 검사계획 생성/관리
- [x] 측정결과 등록 및 자동 판정
- [x] NCR 생성 및 상태 전이
- [x] SPC 차트 조회 (Cp, Cpk)
- [x] 비정상 케이스 (USL < LSL, 규격 이탈)

### 4. 스케줄러 (role-scheduler.spec.ts)
- [x] 간트 차트 조회
- [x] 스케줄 실행 및 결과 확인
- [x] 솔버 선택 (OR-Tools, GA, SA, TABU)
- [x] 설비 배정 및 충돌 검사
- [x] 비정상 케이스 (타임아웃, 중복 실행)

---

## ✅ CRUD 테스트 (crud-deep-validation.spec.ts)

### Create 검증
- [x] 생성 후 목록에 즉시 반영
- [x] ID 자동 생성 확인
- [x] 연관 데이터 자동 생성 (공정 배정)
- [x] 실적 등록 시 진행률 자동 계산

### Read 검증
- [x] 목록/상세 데이터 일치
- [x] 합계 일치 (UI 통계 vs API 합산)
- [x] 상태 필터 후 데이터 정확성
- [x] 날짜 필터 후 범위 확인
- [x] 페이지네이션 중복 없음
- [x] 전체 개수와 페이지별 합계 일치

### Update 검증
- [x] 수량 수정 후 목록 반영
- [x] 수정 시 스케줄러 연동
- [x] 상태 전이 순서 검증 (역방향 방지)
- [x] 상태별 수정 가능 여부

### Delete 검증
- [x] 삭제 후 목록에서 즉시 제거
- [x] 연관 데이터 있으면 삭제 방지
- [x] 삭제된 데이터 참조 시 404 반환

---

## 📊 데이터 정합성 테스트 (data-integrity-deep.spec.ts)

### 시스템간 연계
- [x] 작업지시 ↔ 실적: 진행률 자동 계산
- [x] 작업지시 ↔ 실적: 수량 합계 일치
- [x] 실적 ↔ 품질: 불량 수량 vs NCR 수량
- [x] 품질 → 작업지시: 부적합 시 상태 영향
- [x] 작업지시 ↔ 스케줄러: 수량 동기화
- [x] 스케줄러: 설비-공정 호환성
- [x] 스케줄러: 시간 겹침 없음

### 마스터 데이터
- [x] 제품 → 공정 → 설비 연결
- [x] 삭제된 마스터 참조 검사

### UI ↔ API 일치
- [x] 작업지시 목록
- [x] 대시보드 통계

### 시간/날짜
- [x] 시작 < 종료 논리
- [x] 미래 날짜 데이터 검사

### 수량/숫자
- [x] 음수 검사
- [x] 양품 + 불량 = 총생산량
- [x] 진행률 0-100 범위

---

## 🔄 워크플로우 테스트

### 핵심 워크플로우 (critical-workflows.spec.ts)
- [x] 작업지시 → 실적 → 완료 전체 흐름
- [x] 품질 이슈 발생 → NCR → 해결 흐름
- [x] 스케줄 생성 → 실행 → 결과 확인

### 제조 워크플로우 (manufacturing-workflow.spec.ts)
- [x] 자재 입고 → 작업 → 출하
- [x] 불량 발생 → 재작업/폐기
- [x] 긴급 작업지시 처리

---

## 🧪 테스트 실행 방법

```bash
# 전체 테스트
npm run test:e2e

# 역할별 테스트
npm run test:e2e -- e2e/scenarios/role-production-manager.spec.ts
npm run test:e2e -- e2e/scenarios/role-operator.spec.ts
npm run test:e2e -- e2e/scenarios/role-quality-manager.spec.ts
npm run test:e2e -- e2e/scenarios/role-scheduler.spec.ts

# 정합성 테스트
npm run test:e2e -- e2e/validation/crud-deep-validation.spec.ts
npm run test:e2e -- e2e/validation/data-integrity-deep.spec.ts

# UI 모드 (디버깅)
npm run test:e2e:ui
```

---

## 📁 테스트 파일 구조

```
e2e/
├── fixtures/
│   └── auth.ts              # 인증 fixture
├── scenarios/               # 시나리오 테스트
│   ├── role-production-manager.spec.ts
│   ├── role-operator.spec.ts
│   ├── role-quality-manager.spec.ts
│   ├── role-scheduler.spec.ts
│   ├── critical-workflows.spec.ts
│   ├── deep-workflow.spec.ts
│   ├── manufacturing-workflow.spec.ts
│   └── ...
└── validation/              # 데이터 검증 테스트
    ├── crud-deep-validation.spec.ts
    ├── data-integrity-deep.spec.ts
    ├── data-sync-integrity.spec.ts
    ├── manufacturing-integrity.spec.ts
    └── ...
```

---

## 🎯 테스트 설계 원칙

### 1. 역할 기반 테스트
각 사용자 역할이 수행하는 업무 흐름 중심으로 테스트 구성

### 2. CRUD 깊이 있는 검증
- **Create**: 즉시 반영, ID 생성, 연관 데이터
- **Read**: 목록/상세 일치, 필터/정렬, 페이지네이션
- **Update**: 즉시 반영, 연관 업데이트, 상태 전이
- **Delete**: 목록 제거, 연관 데이터 처리

### 3. 시스템간 정합성
- 작업지시 → 실적 → 품질 → 스케줄러 데이터 흐름
- 수량 합계, 상태 동기화, 자동 계산값 검증

### 4. 엣지 케이스
- 동시 수정
- 삭제된 참조
- 잘못된 상태 전이
- 범위 초과 값

---

*Last Updated: 2026-02-08*
