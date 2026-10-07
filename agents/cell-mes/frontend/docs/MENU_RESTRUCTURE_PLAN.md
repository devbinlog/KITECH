# Cell-MES 메뉴 구조 개편 계획

**작성일:** 2026-02-07
**작성자:** Claude (AI Assistant)
**상태:** ✅ 구현 완료 (2026-02-08)

> **구현 결과 요약:**
> - Phase 1 (Sidebar 계층 구조): ✅ 완료 — `components/ui/Sidebar.tsx` 전면 재작성 (271줄)
> - Phase 2 (스케줄러 분리): ✅ 완료 — 3개 페이지 + 공유 훅 + JsonModal
> - Phase 3 (테스트 및 검증): ✅ 완료 — 백엔드 1,013 passed / E2E 567 passed
> - 리다이렉트 설정: ✅ `/production/scheduler` → `/scheduler` (next.config.js)
> - E2E 테스트 7개 파일 경로 업데이트 완료
> - `SidebarMenu.tsx` 별도 분리 대신 `Sidebar.tsx` 내부에 통합 구현

---

## 1. 현황 분석

### 1.1 현재 메뉴 구조 (평면)

```
대시보드
표준공정
제품관리
라우팅설계
물류시나리오
설비관리
작업지시
생산실적
스케줄러연동
품질관리
분석리포트
AI 어시스턴트
```

**문제점:**
- 11개 메뉴가 동일 레벨에 나열 → 사용자 탐색 어려움
- 논리적 그룹핑 없음
- 하위 페이지 접근성 낮음 (URL 직접 입력 필요)

### 1.2 숨겨진 하위 페이지

| 상위 메뉴 | 하위 페이지 | 현재 접근 방법 |
|-----------|-------------|----------------|
| 품질관리 | 검사계획 (`/quality/inspection-plans`) | URL 직접 입력 |
| 품질관리 | 측정결과 (`/quality/inspection-results`) | URL 직접 입력 |
| 품질관리 | SPC 차트 (`/quality/spc`) | URL 직접 입력 |
| 품질관리 | NCR 관리 (`/quality/ncr`) | URL 직접 입력 |
| 분석리포트 | 설비 가동률 (`/analytics/equipment`) | URL 직접 입력 |
| 분석리포트 | Lot 추적 (`/analytics/lot-trace`) | URL 직접 입력 |

### 1.3 스케줄러 기능 과밀

현재 `/production/scheduler` 단일 페이지에 포함된 기능:
- 현재 스케줄 간트차트 조회
- 스케줄 실행 (5개 솔버: OR-Tools, GA, SA, TABU, ALNS)
- 승인 워크플로우
- 설정 (horizon, 시간 제한 등)

**권장:** 기능별 페이지 분리

---

## 2. 개편 목표

1. **2단계 계층 구조** 도입으로 논리적 그룹핑
2. **숨겨진 하위 페이지** 메뉴에 노출
3. **스케줄러 기능 분리**로 복잡도 감소
4. **확장 가능한 구조**로 향후 메뉴 추가 용이

---

## 3. 신규 메뉴 구조

```
📊 대시보드                    /

📁 기준정보 ▾
   ├─ 표준공정                 /master/processes
   ├─ 제품관리                 /master/products
   ├─ 라우팅설계               /master/routings
   ├─ 물류시나리오             /master/scenarios
   └─ 설비관리                 /master/equipments

📁 생산관리 ▾
   ├─ 작업지시                 /production/orders
   └─ 생산실적                 /production/results

📁 스케줄러 ▾
   ├─ 스케줄 현황              /scheduler (NEW)
   ├─ 스케줄 실행              /scheduler/execute (NEW)
   └─ 솔버 설정                /scheduler/settings (NEW, optional)

📁 품질관리 ▾
   ├─ 품질 대시보드            /quality
   ├─ 검사계획                 /quality/inspection-plans
   ├─ 측정결과                 /quality/inspection-results
   ├─ SPC 차트                 /quality/spc
   └─ NCR 관리                 /quality/ncr

📁 분석리포트 ▾
   ├─ 분석 대시보드            /analytics
   ├─ 설비 가동률              /analytics/equipment
   └─ Lot 추적                 /analytics/lot-trace

🤖 AI 어시스턴트              /chat
```

---

## 4. 구현 계획

### 4.1 Phase 1: Sidebar 컴포넌트 개편 (1일)

**파일:** `components/ui/Sidebar.tsx`

**작업 내용:**
1. 메뉴 데이터 구조 변경 (평면 → 계층)
2. 접기/펼치기 UI 추가
3. 현재 경로 기반 상위 메뉴 자동 펼침
4. 아이콘 그룹별 통일

**예시 코드:**
```typescript
interface MenuItem {
  href?: string;
  label: string;
  icon: LucideIcon;
  children?: MenuItem[];
}

const menuItems: MenuItem[] = [
  { href: "/", label: "대시보드", icon: LayoutDashboard },
  {
    label: "기준정보",
    icon: Database,
    children: [
      { href: "/master/processes", label: "표준공정", icon: Settings },
      { href: "/master/products", label: "제품관리", icon: Package },
      { href: "/master/routings", label: "라우팅설계", icon: Workflow },
      { href: "/master/scenarios", label: "물류시나리오", icon: Truck },
      { href: "/master/equipments", label: "설비관리", icon: Cpu },
    ],
  },
  // ...
];
```

### 4.2 Phase 2: 스케줄러 페이지 분리 (2-3일)

**현재:** `/production/scheduler` (단일 페이지, 800+ lines)

**분리 계획:**

| 신규 경로 | 기능 | 우선순위 |
|-----------|------|----------|
| `/scheduler` | 스케줄 현황 (간트차트, 설비 가용성) | P1 |
| `/scheduler/execute` | 스케줄 실행 및 승인 워크플로우 | P1 |
| `/scheduler/settings` | 솔버 설정, 파라미터 관리 | P2 (optional) |

**작업 내용:**
1. `app/(main)/scheduler/` 폴더 생성
2. 기존 코드에서 컴포넌트 분리
3. 공통 상태/서비스 추출
4. 라우팅 업데이트

### 4.3 Phase 3: 테스트 및 검증 (1일)

1. E2E 테스트 업데이트 (경로 변경 반영)
2. 기존 북마크/링크 리다이렉트 처리
3. 사용자 시나리오 테스트

---

## 5. 파일 변경 목록

### 수정 필요
| 파일 | 변경 내용 |
|------|-----------|
| `components/ui/Sidebar.tsx` | 계층 구조 메뉴 지원 |
| `app/(main)/production/scheduler/page.tsx` | 기능 분리 후 삭제 또는 리다이렉트 |

### 신규 생성
| 파일 | 설명 |
|------|------|
| `app/(main)/scheduler/page.tsx` | 스케줄 현황 |
| `app/(main)/scheduler/execute/page.tsx` | 스케줄 실행 |
| `app/(main)/scheduler/settings/page.tsx` | 솔버 설정 (optional) |
| `components/ui/SidebarMenu.tsx` | 접기/펼치기 메뉴 컴포넌트 |

### E2E 테스트 업데이트
| 파일 | 변경 내용 |
|------|-----------|
| `e2e/scenarios/*.spec.ts` | 경로 업데이트 |
| `e2e/crud/*.spec.ts` | 경로 업데이트 |

---

## 6. 일정

| Phase | 작업 | 예상 소요 | 담당 |
|-------|------|-----------|------|
| 1 | Sidebar 계층 구조 | 1일 | - |
| 2 | 스케줄러 페이지 분리 | 2-3일 | - |
| 3 | 테스트 및 검증 | 1일 | - |
| **합계** | | **4-5일** | |

---

## 7. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|-----------|
| 기존 URL 북마크 깨짐 | 중 | 리다이렉트 설정 (`next.config.js`) |
| 스케줄러 상태 공유 이슈 | 중 | Zustand store 또는 URL 파라미터 활용 |
| E2E 테스트 대량 실패 | 저 | 경로 변수화로 일괄 수정 용이 |

---

## 8. 승인

- [x] 메뉴 구조 확정 (2026-02-07)
- [x] 스케줄러 분리 범위 확정 (2026-02-07)
- [x] 일정 확정 (2026-02-07)
- [x] 개발 착수 및 완료 (2026-02-08)

---

## 부록: 아이콘 매핑

| 메뉴 | 아이콘 | Lucide 컴포넌트 |
|------|--------|-----------------|
| 대시보드 | 📊 | `LayoutDashboard` |
| 기준정보 | 📁 | `Database` |
| 생산관리 | 📁 | `Factory` |
| 스케줄러 | 📁 | `Calendar` |
| 품질관리 | 📁 | `Shield` |
| 분석리포트 | 📁 | `TrendingUp` |
| AI 어시스턴트 | 🤖 | `Bot` |
