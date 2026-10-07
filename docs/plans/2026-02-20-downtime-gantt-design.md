# Downtime Gantt Visualization Design

**Date**: 2026-02-20
**Status**: Completed

## Goal

1. 스케줄 현황 페이지(`/scheduler`) 간트 차트에 다운타임 블록을 함께 표시
2. 다운타임 관리 페이지(`/downtime`)에 간트 차트 추가 (다운타임만)

## User Decisions

- **다운타임 시각적 스타일**: 빗금 패턴 블록 (hatched diagonal stripes)
- **다운타임 페이지 간트 범위**: 오늘 하루 + 날짜 선택
- **다운타임 페이지 간트 내용**: 다운타임만 표시 (작업 없음)

## Approach: Extend Existing `SchedulerGanttChart`

기존 `SchedulerGanttChart` 컴포넌트를 확장하여 `"DOWNTIME"` 상태 타입을 추가. 새 컴포넌트 생성 대신 기존 것을 재사용하여 코드 중복 방지.

## Changes

### 1. `SchedulerGanttChart.tsx` — Downtime Rendering

- SVG `<defs>` 추가: 45도 대각선 빗금 패턴 (red stripes on light-red bg)
- `getTaskColor()` — `DOWNTIME` case 추가 (빗금 + red border)
- 다운타임 블록은 클릭 불가 (작업지시 네비게이션 없음)
- 다운타임 전용 툴팁: 설비명, 사유, 시작/종료, 소요시간 (수량/Lot 없음)
- Footer 범례에 "다운타임" 추가 (빗금 스와치)

### 2. `useScheduler.ts` — New Hook

```ts
export function useDowntimeForGantt(date: string) → ScheduledTaskForGantt[]
```

- `downtimeService.getAll({ date_from, date_to, status: "all" })` 호출
- 각 다운타임을 `ScheduledTaskForGantt`로 변환:
  - `wo_id`: `"DT-{id}"`
  - `status`: `"DOWNTIME"`
  - `start_time`/`end_time`: 날짜 기준 초(seconds) 변환
  - `product_name`: reason name (툴팁/블록 텍스트용)
  - `machine_id`: `"EQ-{equipment_id}"` 형태
  - `quantity`: 0

### 3. `/scheduler/page.tsx` — Merge Downtime

- `useDowntimeForGantt(selectedDate)` 호출
- 다운타임 tasks를 기존 schedule tasks와 합쳐서 `SchedulerGanttChart`에 전달
- UI 레이아웃 변경 없음

### 4. `/downtime/page.tsx` — Add Gantt Section

- 날짜 선택기 (기본값: 오늘)
- 설비 필터 (선택)
- `useDowntimeForGantt(date)` + 설비 목록 → Gantt 렌더링
- 기존 카드 목록/테이블 위에 배치
- `SchedulerGanttChart` 사용 (title="다운타임 타임라인")

## Visual Spec

| Property | Value |
|----------|-------|
| Pattern | 45° diagonal stripes, 4px spacing |
| Stripe color | `#EF4444` at 30% opacity |
| Background | `#FEE2E2` |
| Border | `border-red-400` (solid) |
| Text | `text-red-800` |
| Legend | Hatched square + "다운타임" |

## Files to Modify

| File | Change |
|------|--------|
| `components/scheduler/SchedulerGanttChart.tsx` | SVG pattern, DOWNTIME status, tooltip, legend |
| `hooks/useScheduler.ts` | `useDowntimeForGantt()` hook |
| `app/(main)/scheduler/page.tsx` | Merge downtime into Gantt tasks |
| `app/(main)/downtime/page.tsx` | Add Gantt section with date picker |

## Implementation Notes (2026-02-20)

### 구현 완료 사항
- SVG 대신 CSS `repeating-linear-gradient` 사용 (더 간단하고 DOM 오버헤드 없음)
- 다운타임 페이지 간트는 전체 설비 표시 (다운타임 있는 설비만이 아닌)
- `isDowntimeTask()` 헬퍼: `status === 'DOWNTIME' || wo_id.startsWith('DT-')`로 이중 체크
- 다운타임 블록 `end_time` 클램프: `Math.min(endSec, 86400)` (24h 범위 내)
- 진행중 다운타임(`end_time=null`)은 `dateTo` (23:59:59)까지 표시

### 함께 수정된 버그 (같은 세션)
1. **설비 상태 매핑** — `RUN`/`STOP` → `RUNNING`/`AVAILABLE` 매핑 추가
2. **스케줄러 다운타임 반영** — `_get_occupied_slots()`에 Downtime 테이블 조회 추가
3. **진척도 초과** — `progressMap` 합산 → `Math.max` 변경 (225/150 → 142/150)
