# Workflow-Level Bug Fixes Design

**Date**: 2026-02-17
**Status**: Approved
**Strategy**: Frontend-only fixes, no backend changes

---

## Context

After fixing 5 API contract mismatches (Fix 1-5), a workflow-level scan of all 10 service files and 23 page components revealed 6 categories of cross-cutting bugs that affect real user workflows.

---

## W1: Stale Data After Cross-Page Mutations (CRITICAL)

**Problem**: Mutations on one page don't invalidate related queries on other pages.

### Instances

| Mutation | File:Line | Missing Invalidation |
|----------|-----------|---------------------|
| Scheduler approve | `scheduler/execute/page.tsx:256` | `["dashboard-orders-stats"]`, `["dashboard-orders-display"]` |
| Downtime end | `downtime/page.tsx:83` | `["equipments"]` (equipment status may change) |
| Order status change | `orders/page.tsx:176` | `["results-for-progress"]`, `["dashboard-orders-stats"]` |

### Fix

Add broader invalidation calls in each mutation's `onSuccess`:

**scheduler/execute/page.tsx** (approve mutation):
```typescript
onSuccess: (data) => {
  // ... existing code ...
  queryClient.invalidateQueries({ queryKey: ["dashboard-orders-stats"] });
  queryClient.invalidateQueries({ queryKey: ["dashboard-orders-display"] });
}
```

**downtime/page.tsx** (end mutation):
```typescript
onSuccess: () => {
  queryClient.invalidateQueries({ queryKey: ["downtime"] });
  queryClient.invalidateQueries({ queryKey: ["equipments"] });
}
```

**orders/page.tsx** (status mutation):
```typescript
onSuccess: () => {
  queryClient.invalidateQueries({ queryKey: ["orders"] });
  queryClient.invalidateQueries({ queryKey: ["results-for-progress"] });
  queryClient.invalidateQueries({ queryKey: ["dashboard-orders-stats"] });
}
```

---

## W2: Progress Bar Over-Fetching (MAJOR)

**Problem**: `orders/page.tsx:115-119` fetches `limit: 1000` results on `POLLING.NORMAL` interval for progress bar computation.

### Fix

Reduce polling frequency and add staleTime:

```typescript
const { data: allResultsData } = useQuery({
  queryKey: ["results-for-progress"],
  queryFn: () => productionService.getResults({ limit: 1000 }),
  refetchInterval: POLLING.SLOW,
  staleTime: 30_000,
});
```

---

## W3: Quality Dashboard Empty Charts (MAJOR)

**Problem**: `quality.ts:219-221` hardcodes `trend_data: []`, `defect_by_type: []`, `top_issues: []`. Charts always show "not enough data".

### Fix

Supplement `getQualityDashboard()` with parallel API calls to existing endpoints:

```typescript
async getQualityDashboard(date_from?: string, date_to?: string) {
  let days = 7;
  if (date_from && date_to) {
    const diffMs = new Date(date_to).getTime() - new Date(date_from).getTime();
    days = Math.max(1, Math.min(90, Math.ceil(diffMs / (1000 * 60 * 60 * 24))));
  }

  const [summaryRes, resultsRes, ncrsRes] = await Promise.all([
    api.get("/api/v1/quality/dashboard/summary", { params: { days } }),
    api.get("/api/v1/quality/inspection-results", {
      params: { date_from, date_to, limit: 500 }
    }),
    api.get("/api/v1/quality/ncr", {
      params: { date_from, date_to, limit: 200 }
    }),
  ]);

  const data = summaryRes.data;
  const results = Array.isArray(resultsRes.data) ? resultsRes.data : resultsRes.data?.items || [];
  const ncrs = Array.isArray(ncrsRes.data) ? ncrsRes.data : ncrsRes.data?.items || [];

  // Compute trend_data: group results by date, calculate pass/fail rate
  const byDate: Record<string, { ok: number; total: number }> = {};
  for (const r of results) {
    const date = (r.inspection_date || r.created_at || "").split("T")[0];
    if (!date) continue;
    if (!byDate[date]) byDate[date] = { ok: 0, total: 0 };
    byDate[date].total++;
    if (r.judgment === "OK") byDate[date].ok++;
  }
  const trend_data = Object.entries(byDate)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, { ok, total }]) => ({
      date,
      pass_rate: total > 0 ? (ok / total) * 100 : 0,
      fail_rate: total > 0 ? ((total - ok) / total) * 100 : 0,
    }));

  // Compute defect_by_type from NCRs
  const defectCounts: Record<string, number> = {};
  for (const ncr of ncrs) {
    const type = ncr.defect_type || "OTHER";
    defectCounts[type] = (defectCounts[type] || 0) + 1;
  }
  const defect_by_type = Object.entries(defectCounts).map(([defect_type, count]) => ({
    defect_type,
    count,
  }));

  // Top issues: group NCRs by product
  // (NCRs may not have product_name directly, use work_order link if available)
  const productCounts: Record<string, number> = {};
  for (const ncr of ncrs) {
    const name = ncr.product_name || ncr.defect_description?.slice(0, 20) || "Unknown";
    productCounts[name] = (productCounts[name] || 0) + 1;
  }
  const top_issues = Object.entries(productCounts)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5)
    .map(([product_name, defect_count]) => ({ product_name, defect_count }));

  return {
    total_inspections: data.total_inspections || 0,
    pass_rate: data.quality_rate_percent || 0,
    fail_rate: 100 - (data.quality_rate_percent || 100),
    rework_rate: 0,
    open_ncrs: data.open_ncrs || 0,
    trend_data,
    defect_by_type,
    top_issues,
  };
}
```

---

## W4: Connection Status Over-Fetching (MINOR)

**Problem**: `quality/page.tsx:108-111` fetches `limit: 1000` for plans and results every `POLLING.SLOW` just for a connection count.

### Fix

Reduce limits to 200 (sufficient for connection status counting):

```typescript
const [plans, results] = await Promise.all([
  qualityService.getInspectionPlans({ limit: 200 }),
  qualityService.getInspectionResults({ limit: 200 })
]);
```

---

## W5: Completed Downtime Tab Stale (MINOR)

**Problem**: `downtime/page.tsx:48-52` — completed tab query has no `refetchInterval`. After ending a downtime, switching to completed tab shows stale data.

### Fix

Invalidate completed query when ending a downtime:

```typescript
// In endMutation onSuccess:
onSuccess: () => {
  queryClient.invalidateQueries({ queryKey: ["downtime"] }); // covers both active + completed
  queryClient.invalidateQueries({ queryKey: ["equipments"] });
}
```

The existing `queryClient.invalidateQueries({ queryKey: ["downtime"] })` should already cover `["downtime", "completed"]` since React Query invalidates by prefix. Verify this works — if not, add explicit `["downtime", "completed"]`.

---

## W6: Missing Error Boundaries (MINOR)

**Problem**: Only quality dashboard has `ErrorBoundary`. Other critical pages crash entirely on render errors.

### Fix

Wrap these pages in existing `ErrorBoundary` component:

- `production/orders/page.tsx`
- `downtime/page.tsx`
- `alarms/page.tsx`

Pattern:
```tsx
import ErrorBoundary from "@/components/ErrorBoundary";

export default function Page() {
  return (
    <ErrorBoundary>
      {/* existing content */}
    </ErrorBoundary>
  );
}
```

---

## Files to Modify

| File | Fixes | Changes |
|------|-------|---------|
| `frontend/services/quality.ts` | W3 | Supplement dashboard with trend/defect data |
| `frontend/app/(main)/production/orders/page.tsx` | W1, W2, W6 | Broader invalidation, reduce polling, add ErrorBoundary |
| `frontend/app/(main)/downtime/page.tsx` | W1, W5, W6 | Broader invalidation, add ErrorBoundary |
| `frontend/app/(main)/scheduler/execute/page.tsx` | W1 | Broader invalidation after approve |
| `frontend/app/(main)/quality/page.tsx` | W4 | Reduce connection status fetch limits |
| `frontend/app/(main)/alarms/page.tsx` | W6 | Add ErrorBoundary |

---

## Verification

1. **W1**: Approve schedule → navigate to dashboard → verify orders reflect new schedule
2. **W2**: Open orders page → verify network tab shows slower polling for results
3. **W3**: Quality dashboard → verify trend chart and defect pie chart show data (when inspection results exist)
4. **W4**: Quality dashboard → verify smaller payloads in network tab
5. **W5**: End a downtime → switch to completed tab → verify it appears immediately
6. **W6**: Verify pages render error fallback instead of white screen on error

### TypeScript verification
```bash
cd agents/cell-mes/frontend && npx tsc --noEmit
```
