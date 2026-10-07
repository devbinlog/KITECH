# Phase 1: Bug Safari Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Find and fix every user-facing bug across all 23 pages of the Cell-MES frontend by operating the app like a factory worker, using Playwright MCP browser for live testing.

**Architecture:** Systematically visit every page, run a 5-point checklist (Visual, Data, Interaction, Error, State), capture bugs with screenshots, write failing E2E tests first (TDD), fix the code, verify. Each task covers one logical page group. Tests use proper assertions (no anti-patterns).

**Tech Stack:** Next.js 14 (localhost:3000), FastAPI backend (localhost:8000), Playwright MCP browser, TypeScript, TailwindCSS, Recharts, React Query, Zustand

---

## Prerequisites

**Before starting any task:**

1. Start all backend services:
```bash
powershell ./start-mes.ps1
```

2. Start the frontend dev server:
```bash
cd agents/cell-mes/frontend && npm run dev
```

3. Verify services are running:
- Backend API: `http://localhost:8000/docs`
- Frontend: `http://localhost:3000`
- NL Router: `http://localhost:8001/docs`
- Scheduler: `http://localhost:8002/docs`

4. Seed test data if needed:
```bash
cd agents/cell-mes && uv run python -m src.seed_data
```

## Per-Page Bug Checklist (apply to EVERY page)

| Check | What to look for | How to verify |
|-------|-------------------|---------------|
| **Visual** | Layout broken, text overflow, NaN/null/undefined displayed, missing icons, wrong colors | Take screenshot, inspect visible text |
| **Data** | Displayed values don't match API, wrong counts, stale data, empty when should have data | Compare browser content with API response via network tab |
| **Interaction** | Buttons don't work, forms don't submit, modals don't open/close, dropdowns empty | Click every button, fill every form, open every modal |
| **Error** | No error message on invalid input, cryptic errors, unhandled exceptions | Submit empty forms, enter invalid data, check console |
| **State** | Page doesn't update after create/edit/delete, stale cache, navigation loses state | Perform CRUD, verify list updates without manual refresh |

## Bug Fix Process (for every bug found)

1. **Screenshot** the bug using `browser_take_screenshot`
2. **Identify** the root cause file (page component, shared component, service, or API)
3. **Write failing test** in `agents/cell-mes/frontend/e2e/bug-fixes/` (new directory)
4. **Fix the code** in the source file
5. **Verify** the fix via browser + test passes
6. **Commit** with message: `fix(module): description of bug fix`

## New Test Rules (MANDATORY)

```typescript
// NEVER use these patterns in new tests:
// .catch(() => false)
// expect(... || true).toBeTruthy()
// console.log() without expect()
// page.waitForTimeout()
// if (!response.ok()) return

// ALWAYS use:
await expect(page.locator('...')).toBeVisible({ timeout: 10000 });
await page.waitForResponse(resp => resp.url().includes('/api/v1/...'));
await expect(page.locator('...')).toHaveText('expected value');
```

---

## Task 1: Login & Authentication Flow

**Pages:** `/login`

**Files to potentially fix:**
- `agents/cell-mes/frontend/app/login/page.tsx`
- `agents/cell-mes/frontend/stores/authStore.ts`
- `agents/cell-mes/frontend/services/auth.ts`
- `agents/cell-mes/frontend/lib/axios.ts`

**Step 1: Navigate to login page**
- Open `http://localhost:3000/login` using `browser_navigate`
- Take snapshot with `browser_snapshot`

**Step 2: Run checklist**
- Visual: Login form layout, logo, input fields visible
- Interaction: Type invalid credentials -> expect error message displayed
- Interaction: Type valid credentials (admin/admin123) -> expect redirect to dashboard
- Error: Empty username/password -> expect validation message
- Error: Wrong password -> expect "인증 실패" or similar error
- State: After login, localStorage should have `token` and `auth-storage`

**Step 3: Test auth redirect**
- Navigate to `http://localhost:3000/` without token -> expect redirect to `/login`
- After login, navigate to protected page -> expect page loads normally

**Step 4: Write tests for any bugs found**

Test file: `agents/cell-mes/frontend/e2e/bug-fixes/login.spec.ts`
```typescript
import { test, expect } from '@playwright/test';

test.describe('Login Page', () => {
  test('shows error on invalid credentials', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[type="text"], input[name="username"]', 'wronguser');
    await page.fill('input[type="password"]', 'wrongpass');
    await page.click('button[type="submit"]');
    await expect(page.locator('.bg-red-100, [class*="error"], [role="alert"]')).toBeVisible({ timeout: 5000 });
  });

  test('redirects to dashboard on valid login', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[type="text"], input[name="username"]', 'admin');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/');
    await expect(page).toHaveURL(/\//);
  });

  test('redirects unauthenticated users to login', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveURL(/\/login/);
  });
});
```

**Step 5: Fix any bugs found, commit**

---

## Task 2: Dashboard

**Pages:** `/` (main dashboard)

**Files to potentially fix:**
- `agents/cell-mes/frontend/app/(main)/page.tsx`
- `agents/cell-mes/frontend/components/analytics/KPICard.tsx`
- `agents/cell-mes/frontend/components/dashboard/AISummaryWidget.tsx`
- `agents/cell-mes/frontend/components/equipment/EquipmentCard.tsx`

**Step 1: Login and navigate to dashboard**
- Use auth fixture or manual login
- Take snapshot of full dashboard

**Step 2: Run checklist**
- Visual: KPI cards show numbers (not NaN, null, undefined, "-" when data exists)
- Visual: Charts render correctly (not empty, no error boundary shown)
- Visual: Equipment status grid shows correct status colors (green=RUN, gray=STOP, red=ERROR)
- Data: KPI values match `/api/v1/analytics/daily-status` response
- Data: Equipment statuses match `/api/v1/masters/equipments` response
- Interaction: Click equipment card -> navigates to equipment detail or shows modal
- Interaction: AI Summary widget loads (or shows graceful error if NL Router down)
- State: Dashboard auto-refreshes (polling every 5s per config)
- Error: Check browser console for JavaScript errors

**Step 3: Specific KPICard checks**
- Verify `value.toLocaleString()` doesn't crash on null/undefined values
- Verify trend arrow direction matches data (up = positive trend)
- Verify progress bar width calculation when target = 0
- Verify color mapping works for all 7 colors

**Step 4: Write tests, fix bugs, commit**

Test file: `agents/cell-mes/frontend/e2e/bug-fixes/dashboard.spec.ts`

---

## Task 3: Master Data - Processes & Products

**Pages:** `/master/processes`, `/master/products`

**Files to potentially fix:**
- `agents/cell-mes/frontend/app/(main)/master/processes/page.tsx`
- `agents/cell-mes/frontend/app/(main)/master/products/page.tsx`
- `agents/cell-mes/frontend/services/master.ts`
- `agents/cell-mes/frontend/components/dynamic/DynamicDataTable.tsx`

**Step 1: Navigate to Processes page**
- Take snapshot
- Verify table loads with data from `/api/v1/masters/std-processes`

**Step 2: Run checklist - Processes**
- Visual: Table headers correct, data rows populated, no empty table when data exists
- Data: Row count matches API response total
- Interaction: Sort by clicking column headers -> verify sort works
- Interaction: Search/filter -> verify filtering works
- Interaction: Pagination -> verify page navigation
- Interaction: Create new process -> fill form -> submit -> verify added to list
- Interaction: Edit existing process -> modify -> save -> verify updated
- Interaction: Delete process -> confirm -> verify removed from list
- Error: Submit form with empty required fields -> expect validation error
- State: After CRUD, table refreshes without manual reload

**Step 3: Navigate to Products page, repeat checklist**
- Same CRUD flow for products
- Verify product code uniqueness validation
- Verify product-process associations display correctly

**Step 4: DynamicDataTable component checks**
- `formatCellValue(null)` returns '-' (not "null" string)
- `formatCellValue(undefined)` returns '-'
- Sort with Korean text uses `localeCompare` correctly
- CSV export includes UTF-8 BOM and correct data
- Pagination resets to page 1 after filter change
- Empty search shows all rows

**Step 5: Write tests, fix bugs, commit**

---

## Task 4: Master Data - Routings & Scenarios

**Pages:** `/master/routings`, `/master/scenarios`

**Files to potentially fix:**
- `agents/cell-mes/frontend/app/(main)/master/routings/page.tsx`
- `agents/cell-mes/frontend/app/(main)/master/scenarios/page.tsx`
- `agents/cell-mes/frontend/services/master.ts`

**Step 1: Navigate to Routings page**
- Take snapshot
- Verify routing list loads

**Step 2: Run checklist - Routings**
- Visual: Process sequence displayed correctly (ordered steps)
- Data: Routing steps match API data (correct operation order)
- Interaction: Create routing -> add process steps -> save
- Interaction: Edit routing -> reorder steps -> save -> verify new order persisted
- Interaction: Delete routing -> confirm -> verify removed
- Error: Create routing without product association -> expect error
- Error: Duplicate routing for same product -> expect error or warning
- State: After editing routing steps, page shows updated sequence

**Step 3: Navigate to Scenarios page, repeat checklist**
- Verify scenario parameter editing (numeric fields, dropdowns)
- Verify scenario list pagination
- Verify scenario-equipment association

**Step 4: Write tests, fix bugs, commit**

---

## Task 5: Master Data - Equipments (4 tabs)

**Pages:** `/master/equipments` (List, Status, History, Maintenance tabs)

**Files to potentially fix:**
- `agents/cell-mes/frontend/app/(main)/master/equipments/page.tsx`
- `agents/cell-mes/frontend/components/equipment/EquipmentCard.tsx`
- `agents/cell-mes/frontend/services/equipment.ts`
- `agents/cell-mes/frontend/hooks/useConnectionStatus.ts`

**Step 1: Navigate to Equipment List tab**
- Take snapshot
- Verify equipment cards or table loads

**Step 2: Run checklist per tab**

**List Tab:**
- Visual: Equipment cards show correct icons (CNC=Cpu, ROBOT=Bot, AMR=Truck, PLC=CircuitBoard)
- Visual: Status border colors correct (green/gray/red)
- Data: Equipment count matches API response
- Interaction: Click equipment -> navigates to detail view
- Interaction: Create new equipment -> fill form -> save
- Error: Create equipment with duplicate ID -> expect error

**Status Tab:**
- Visual: Real-time status indicators updating
- Data: Status matches `/api/v1/masters/equipments/{id}/status`
- CNC-specific: RPM and Load % display correctly (not NaN)
- ROBOT-specific: Battery level and movement status display
- State: Status updates via WebSocket or polling

**History Tab:**
- Visual: History timeline or table displays events
- Data: Events ordered by timestamp (newest first)
- Interaction: Filter by date range -> verify filtered results

**Maintenance Tab:**
- Visual: Maintenance schedule or records display
- Interaction: Log maintenance activity -> verify saved

**Step 3: Write tests, fix bugs, commit**

---

## Task 6: Production - Work Orders

**Pages:** `/production/orders`

**Files to potentially fix:**
- `agents/cell-mes/frontend/app/(main)/production/orders/page.tsx`
- `agents/cell-mes/frontend/services/production.ts`
- `agents/cell-mes/frontend/types/index.ts`

**Step 1: Navigate to Work Orders page**
- Take snapshot
- Verify work order table loads

**Step 2: Run checklist - Full lifecycle**
- Visual: Status badges show correct colors per status (READY, RUNNING, PAUSE, DONE, ERROR, CANCEL)
- Visual: Table columns display all expected fields (WO ID, product, qty, dates, status)
- Data: Work order count and values match `/api/v1/production/orders`
- Interaction: **Create** work order -> fill product, qty, dates -> submit -> verify in list
- Interaction: **Start** work order (READY -> RUNNING) -> verify status changes
- Interaction: **Pause** work order (RUNNING -> PAUSE) -> verify
- Interaction: **Resume** work order (PAUSE -> RUNNING) -> verify
- Interaction: **Complete** work order (RUNNING -> DONE) -> verify
- Interaction: **Cancel** work order (READY -> CANCEL) -> verify (Task 1 fix from Round 3)
- Error: Create order without product -> expect validation error
- Error: Create order with negative qty -> expect validation error
- Error: Start order that's already RUNNING -> expect error or button disabled
- State: Status transition updates list immediately

**Step 3: Filter and sort**
- Filter by status -> verify only matching orders shown
- Sort by date -> verify chronological order
- Pagination -> verify navigation between pages

**Step 4: Write tests, fix bugs, commit**

---

## Task 7: Production - Results

**Pages:** `/production/results`

**Files to potentially fix:**
- `agents/cell-mes/frontend/app/(main)/production/results/page.tsx`
- `agents/cell-mes/frontend/services/production.ts`

**Step 1: Navigate to Production Results page**
- Take snapshot
- Verify results table loads

**Step 2: Run checklist**
- Visual: Table shows ok_qty, ng_qty, total_qty, yield_rate columns
- Visual: yield_rate displayed as percentage (e.g., "95.0%", not "0.95" or "NaN%")
- Data: total_qty = ok_qty + ng_qty (verify calculation)
- Data: yield_rate = ok_qty / total_qty * 100 (verify calculation)
- Data: Results match `/api/v1/production/results` API response
- Interaction: Record new result -> select work order -> enter ok/ng qty -> submit
- Interaction: Verify new result appears in table with correct calculated fields
- Error: Enter negative quantities -> expect validation
- Error: Record result for DONE work order -> verify behavior
- State: After recording result, table and related work order status update

**Step 3: Verify Round 3 fix (Task 2)**
- Confirm ProdResultRead includes total_qty and yield_rate in API response
- Confirm frontend displays these computed fields

**Step 4: Write tests, fix bugs, commit**

---

## Task 8: Production - Downtime

**Pages:** `/production/downtime` (2 tabs: Records, Analysis)

**Files to potentially fix:**
- `agents/cell-mes/frontend/app/(main)/downtime/page.tsx`
- `agents/cell-mes/frontend/services/downtime.ts`

**Step 1: Navigate to Downtime page**
- Take snapshot of Records tab

**Step 2: Run checklist - Records tab**
- Visual: Downtime records table or list displays correctly
- Data: Records show equipment, reason, start/end time, duration
- Data: Duration calculation correct (end - start)
- Interaction: Log new downtime -> select equipment, reason, times -> save
- Interaction: Edit existing record -> modify -> save -> verify updated
- Error: End time before start time -> expect validation error
- Error: Missing required fields -> expect validation

**Step 3: Switch to Analysis tab**
- Visual: Charts render (downtime by reason, by equipment, trend over time)
- Data: Chart data matches records
- Interaction: Filter by date range -> charts update
- Visual: No NaN/null in chart labels or tooltips

**Step 4: Write tests, fix bugs, commit**

---

## Task 9: Production - Alarms

**Pages:** `/production/alarms` (2 tabs: Active, History)

**Files to potentially fix:**
- `agents/cell-mes/frontend/app/(main)/alarms/page.tsx`
- `agents/cell-mes/frontend/services/alarm.ts`

**Step 1: Navigate to Alarms page**
- Take snapshot of Active alarms tab

**Step 2: Run checklist - Active tab**
- Visual: Active alarms display with severity indicators (CRITICAL=red, WARNING=yellow, INFO=blue)
- Data: Active alarms match `/api/v1/alarms?active=true` or similar API
- Interaction: Acknowledge alarm -> verify status changes
- State: Real-time alarm updates (WebSocket or polling)

**Step 3: Switch to History tab**
- Visual: Historical alarms display with timestamps
- Data: Ordered by timestamp (newest first)
- Interaction: Filter by severity, equipment, date range
- Interaction: Search alarm by code or description

**Step 4: Write tests, fix bugs, commit**

---

## Task 10: Scheduler - Status (Gantt Chart)

**Pages:** `/scheduler` or `/scheduler/status`

**Files to potentially fix:**
- `agents/cell-mes/frontend/app/(main)/scheduler/page.tsx`
- `agents/cell-mes/frontend/components/scheduler/SchedulerGanttChart.tsx`
- `agents/cell-mes/frontend/components/dynamic/charts/GanttChart.tsx`
- `agents/cell-mes/frontend/hooks/useScheduler.ts`
- `agents/cell-mes/frontend/services/scheduler.ts`

**Step 1: Navigate to Scheduler Status page**
- Take snapshot
- Verify Gantt chart or schedule display renders

**Step 2: Run checklist**
- Visual: Gantt chart renders with equipment rows and time blocks
- Visual: Status colors correct (RUNNING=green, AVAILABLE=gray, MAINTENANCE=blue, OFFLINE=red)
- Visual: Time axis labels readable, not overlapping
- Data: Schedule data matches `/api/v1/scheduler/equipment-availability` or current schedule endpoint
- Data: Equipment utilization percentages display correctly (not NaN)
- Interaction: Hover over task block -> tooltip shows lot_no, product, times
- Interaction: Date selector -> changes displayed schedule date
- Error: No schedule data -> shows meaningful empty state (not crash)
- State: After solving new schedule (Task 11), this page reflects updated results

**Step 3: Check GanttChart component specifics**
- Slot width calculation with different time spans
- Overlapping slots handling
- Empty schedule slots rendering

**Step 4: Write tests, fix bugs, commit**

---

## Task 11: Scheduler - Execute

**Pages:** `/scheduler/execute`

**Files to potentially fix:**
- `agents/cell-mes/frontend/app/(main)/scheduler/execute/page.tsx`
- `agents/cell-mes/frontend/hooks/useScheduler.ts`
- `agents/cell-mes/frontend/services/scheduler.ts`

**Step 1: Navigate to Scheduler Execute page**
- Take snapshot
- Verify solver selection and execution UI loads

**Step 2: Run checklist**
- Visual: Solver selection options displayed (OR-Tools, GA, SA, Tabu, ALNS)
- Visual: Parameter inputs for selected solver visible
- Data: Available equipment and work orders loaded from API
- Interaction: Select solver -> verify parameter fields update
- Interaction: Click "Solve" -> verify loading state shown
- Interaction: Wait for result -> verify result displayed (Gantt or summary)
- Interaction: "Approve" result -> verify schedule saved
- Error: Solve with no work orders -> expect meaningful error message
- Error: Solve with no available equipment -> expect error
- State: After solving, result persists on page until approved/rejected

**Step 3: Test solver execution flow end-to-end**
- Select OR-Tools solver (most reliable)
- Configure parameters (if applicable)
- Execute solve
- Verify response contains schedule data
- Check result display (makespan, cost, assignments)

**Step 4: Write tests, fix bugs, commit**

---

## Task 12: Scheduler - Settings

**Pages:** `/scheduler/settings`

**Files to potentially fix:**
- `agents/cell-mes/frontend/app/(main)/scheduler/settings/page.tsx`

**Step 1: Navigate to Scheduler Settings page**
- Take snapshot
- Verify settings form loads

**Step 2: Run checklist**
- Visual: Solver configuration options displayed
- Visual: Constraint settings visible
- Interaction: Modify solver parameters -> save -> verify persisted
- Interaction: Toggle constraints on/off -> save -> verify
- Error: Invalid parameter values (negative, out of range) -> expect validation
- State: After saving settings, execute page uses new settings

**Step 3: Write tests, fix bugs, commit**

---

## Task 13: Quality - Dashboard

**Pages:** `/quality`

**Files to potentially fix:**
- `agents/cell-mes/frontend/app/(main)/quality/page.tsx`
- `agents/cell-mes/frontend/components/analytics/KPICard.tsx`

**Step 1: Navigate to Quality Dashboard**
- Take snapshot
- Verify KPI cards and charts load

**Step 2: Run checklist**
- Visual: Quality KPIs display (defect rate, inspection pass rate, NCR count)
- Visual: KPI values are percentages where appropriate (not raw decimals)
- Visual: Trend charts render (defect rate over time, by type)
- Data: KPI values match quality API endpoints
- Data: No NaN, null, or undefined in KPI cards
- Interaction: Click on KPI card -> navigates to detail page (if applicable)
- Error: No quality data -> shows meaningful empty state
- State: Dashboard refreshes with new data after inspection results entered

**Step 3: Write tests, fix bugs, commit**

---

## Task 14: Quality - Inspection Plans

**Pages:** `/quality/inspection-plans`

**Files to potentially fix:**
- `agents/cell-mes/frontend/app/(main)/quality/inspection-plans/page.tsx`
- `agents/cell-mes/frontend/components/quality/InspectionPlanForm.tsx`
- `agents/cell-mes/frontend/components/quality/InspectionPlanFormImproved.tsx`
- `agents/cell-mes/frontend/components/quality/InspectionPlanTable.tsx`
- `agents/cell-mes/frontend/services/quality.ts`

**Step 1: Navigate to Inspection Plans page**
- Take snapshot
- Verify plan list loads

**Step 2: Run checklist**
- Visual: Plans table shows product, type, item count, status
- Data: Plan list matches `/api/v1/quality/inspection-plans`
- Interaction: **Create** plan -> select product -> add inspection items (USL, LSL, target, method) -> save
- Interaction: Quick templates add correct default items
- Interaction: Auto-calculation: Target = (USL + LSL) / 2 when both set
- Interaction: Add/remove inspection items dynamically
- Interaction: Edit existing plan -> modify items -> save -> verify
- Interaction: Delete plan -> confirm -> verify removed
- Error: Empty item name -> expect validation
- Error: USL < LSL -> expect validation
- Error: Missing measurement method -> expect validation
- State: After create/edit, table refreshes with new plan

**Step 3: Verify InspectionPlanForm specifics**
- Product dropdown populated from masters API
- Sort order maintained when deleting items
- Form resets properly when closing and reopening

**Step 4: Write tests, fix bugs, commit**

---

## Task 15: Quality - Inspection Results

**Pages:** `/quality/inspection-results`

**Files to potentially fix:**
- `agents/cell-mes/frontend/app/(main)/quality/inspection-results/page.tsx`
- `agents/cell-mes/frontend/services/quality.ts`

**Step 1: Navigate to Inspection Results page**
- Take snapshot

**Step 2: Run checklist**
- Visual: Results table with pass/fail indicators, measured values
- Visual: Pass = green, Fail = red visual distinction
- Data: Results match `/api/v1/quality/inspection-results`
- Interaction: Record new result -> select plan -> enter measurements -> submit
- Interaction: Measured value vs spec limits comparison shown
- Interaction: Out-of-spec values highlighted in red
- Error: Non-numeric measurement values -> expect validation
- Error: Missing required measurements -> expect validation
- State: After recording, result appears in table with correct pass/fail

**Step 3: Write tests, fix bugs, commit**

---

## Task 16: Quality - SPC Charts

**Pages:** `/quality/spc`

**Files to potentially fix:**
- `agents/cell-mes/frontend/app/(main)/quality/spc/page.tsx`
- `agents/cell-mes/frontend/components/quality/SPCChart.tsx`

**Step 1: Navigate to SPC page**
- Take snapshot
- Verify SPC charts render

**Step 2: Run checklist**
- Visual: X-bar chart renders with control lines (UCL, CL, LCL)
- Visual: R chart renders with control lines
- Visual: Out-of-control points highlighted in red
- Visual: In-control points in blue
- Data: UCL/LCL values match API response
- Data: Cp/Cpk values displayed correctly (not NaN)
- Interaction: Select different inspection plan -> charts update
- Interaction: Hover data point -> tooltip shows sample #, value, limits
- Error: No SPC data for selected plan -> meaningful empty state
- Error: All values same (R=0) -> charts handle gracefully (no division by zero)

**Step 3: SPCChart component specifics**
- Custom dot coloring logic works (red vs blue threshold)
- Reference lines (UCL, CL, LCL) render at correct Y positions
- Legend shows both states
- Chart responsive to container resize

**Step 4: Write tests, fix bugs, commit**

---

## Task 17: Quality - NCR (Non-Conformance Records)

**Pages:** `/quality/ncr`

**Files to potentially fix:**
- `agents/cell-mes/frontend/app/(main)/quality/ncr/page.tsx`
- `agents/cell-mes/frontend/components/quality/NCRForm.tsx`
- `agents/cell-mes/frontend/services/quality.ts`

**Step 1: Navigate to NCR page**
- Take snapshot
- Verify NCR list loads

**Step 2: Run checklist**
- Visual: NCR table shows ncr_no, defect_type, severity, status
- Visual: Severity badges: CRITICAL=red, MAJOR=amber, MINOR=yellow
- Data: NCR list matches `/api/v1/quality/ncr`
- Interaction: **Create** NCR -> fill all fields (auto-generated ncr_no) -> save
- Interaction: NCR No format: `NCR-YYYYMMDD-XXX` auto-generated correctly
- Interaction: Select work order -> links to inspection result
- Interaction: Defect type dropdown: DIMENSION, SURFACE, MATERIAL, PROCESS, OTHER
- Interaction: Severity dropdown: CRITICAL, MAJOR, MINOR
- Interaction: Root cause, corrective/preventive action textareas
- Interaction: Edit NCR -> update status -> save
- Interaction: Delete NCR -> confirm -> verify removed
- Error: Empty defect description -> expect validation
- Error: Missing severity -> expect validation
- State: After create, NCR appears in list with correct data

**Step 3: Write tests, fix bugs, commit**

---

## Task 18: Analytics - Dashboard

**Pages:** `/analytics`

**Files to potentially fix:**
- `agents/cell-mes/frontend/app/(main)/analytics/page.tsx`
- `agents/cell-mes/frontend/components/dynamic/charts/DynamicLineChart.tsx`
- `agents/cell-mes/frontend/components/dynamic/charts/DynamicBarChart.tsx`
- `agents/cell-mes/frontend/services/analytics.ts`

**Step 1: Navigate to Analytics Dashboard**
- Take snapshot
- Verify charts and KPIs load

**Step 2: Run checklist**
- Visual: Production trend line chart renders with correct axes
- Visual: Bar charts show values with correct colors (threshold-based)
- Visual: KPI summary cards show meaningful numbers
- Data: Trend data matches `/api/v1/analytics/trends`
- Data: KPI data matches `/api/v1/analytics/kpis`
- Interaction: Change date range -> charts update
- Interaction: Toggle between daily/weekly/monthly views (if available)
- Error: No data for selected period -> meaningful empty state (not chart crash)
- Error: Check chart tooltip values don't show NaN or undefined

**Step 3: Chart component specifics**
- DynamicLineChart: Multiple series auto-detection works
- DynamicLineChart: Target reference line renders at correct position
- DynamicBarChart: Color threshold logic (green >= 80%, amber >= 60%, red < 60%)
- All charts: Responsive container fills parent correctly
- All charts: Empty data array -> no crash

**Step 4: Write tests, fix bugs, commit**

---

## Task 19: Analytics - Equipment Utilization

**Pages:** `/analytics/equipment`

**Files to potentially fix:**
- `agents/cell-mes/frontend/app/(main)/analytics/equipment/page.tsx`
- `agents/cell-mes/frontend/components/analytics/UtilizationChart.tsx`

**Step 1: Navigate to Equipment Analytics page**
- Take snapshot

**Step 2: Run checklist**
- Visual: Utilization chart renders (bar, pie, or detailed view)
- Visual: Utilization percentages display correctly (0-100%, not > 100%)
- Visual: Color coding: green >= 85%, amber >= 70%, red < 70%
- Data: Utilization values match `/api/v1/analytics/equipment-utilization`
- Data: OEE calculation correct if displayed
- Interaction: Switch between chart types (bar/pie/detailed)
- Interaction: Filter by equipment type
- Interaction: Date range selector works
- Error: Equipment with no data -> shows 0% (not NaN)
- Error: Rotated X-axis labels don't overlap

**Step 3: UtilizationChart component checks**
- Bar mode: Individual bars per equipment
- Pie mode: Donut chart with legend
- Detailed (ComposedChart): Stacked bars + line overlay
- Labels < 5% hidden in pie chart (not overlapping)
- Custom tooltip shows breakdown values

**Step 4: Write tests, fix bugs, commit**

---

## Task 20: Analytics - LOT Traceability

**Pages:** `/analytics/lot-trace`

**Files to potentially fix:**
- `agents/cell-mes/frontend/app/(main)/analytics/lot-trace/page.tsx`
- `agents/cell-mes/frontend/components/dynamic/TraceabilityTimeline.tsx`
- `agents/cell-mes/frontend/services/analytics.ts`

**Step 1: Navigate to LOT Trace page**
- Take snapshot

**Step 2: Run checklist**
- Visual: Search input for LOT number visible
- Visual: Timeline renders after LOT search
- Data: Traceability data matches `/api/v1/analytics/traceability/{lot_no}`
- Interaction: Enter valid LOT number -> search -> timeline appears
- Interaction: Enter invalid LOT -> meaningful "not found" message
- Interaction: Click timeline node -> shows detail popup
- Error: Empty search -> validation message
- Error: Malformed LOT number -> graceful handling
- State: Search results persist after interaction with timeline

**Step 3: TraceabilityTimeline component checks**
- Timeline nodes ordered chronologically
- Each node shows operation, equipment, timestamps, status
- Visual connections between timeline steps
- Responsive layout for many steps

**Step 4: Write tests, fix bugs, commit**

---

## Task 21: AI Assistant - Chat

**Pages:** `/chat` or `/ai/chat`

**Files to potentially fix:**
- `agents/cell-mes/frontend/app/(main)/chat/page.tsx`
- `agents/cell-mes/frontend/components/chat/ChatInterface.tsx`
- `agents/cell-mes/frontend/components/chat/ChatInput.tsx`
- `agents/cell-mes/frontend/components/chat/ChatMessage.tsx`
- `agents/cell-mes/frontend/components/chat/QuickActions.tsx`
- `agents/cell-mes/frontend/components/dynamic/DynamicRenderer.tsx`
- `agents/cell-mes/frontend/services/nlm.ts`
- `agents/cell-mes/frontend/stores/chatStore.ts`

**Step 1: Navigate to Chat page**
- Take snapshot
- Verify chat interface loads with empty state

**Step 2: Run checklist**
- Visual: Empty state shows greeting message with Sparkles icon
- Visual: Quick actions grid displayed below greeting
- Visual: Input field at bottom with send button
- Interaction: Type "오늘 생산 현황" -> send -> loading animation -> response
- Interaction: Response shows text bubble + UI schema rendering (if applicable)
- Interaction: Quick action button click -> sends predefined query
- Interaction: Multiple messages -> conversation history scrolls
- Data: Metadata shows intent + confidence + processing time
- Error: NL Router down -> graceful error message (not crash)
- Error: Empty message send -> should be prevented
- Error: Very long message -> handled gracefully (max 500 chars per API)
- State: Chat history persists in Zustand store during session
- State: Clearing chat -> resets to empty state

**Step 3: Test NL Router integration (if service running)**
- "도움말" -> should return help response (Round 3 Task 10 fix)
- "CNC-001 상태" -> should return equipment status
- "이번주 실적" -> should return production data (Round 3 Task 12 fix)
- "ROBOT-001 상태" -> should work (Round 3 Task 8 fix)

**Step 4: DynamicRenderer checks**
- Unknown component type -> red alert box (not crash)
- Dashboard layout -> 4-column grid on desktop
- Empty components array -> no crash

**Step 5: Write tests, fix bugs, commit**

---

## Task 22: Cross-Page Navigation & State

**Purpose:** Test navigation between all pages, sidebar behavior, and shared state consistency.

**Step 1: Sidebar navigation**
- Click every menu item in order -> verify correct page loads
- Verify active item highlighting matches current route
- Verify group auto-expand when child route active
- Verify collapsed sidebar remembers state

**Step 2: Cross-page data consistency**
- Create work order on Orders page -> navigate to Dashboard -> verify KPI updated
- Record production result -> navigate to Analytics -> verify reflected
- Create inspection plan -> navigate to Inspection Results -> verify plan available
- Record NCR -> navigate to Quality Dashboard -> verify count updated

**Step 3: Browser back/forward**
- Navigate Dashboard -> Orders -> Results -> press Back -> verify Orders shown
- Press Forward -> verify Results shown
- No stale data on navigation

**Step 4: URL direct access**
- Enter `/production/orders` directly in URL -> verify loads (with auth)
- Enter `/quality/spc` directly -> verify loads
- Enter non-existent route -> verify 404 or redirect

**Step 5: Write tests, fix bugs, commit**

---

## Task 23: Error States & Edge Cases

**Purpose:** Test error handling across the entire application.

**Step 1: API down scenarios**
- Stop backend -> navigate to dashboard -> verify error state (not white screen)
- Error boundary should catch and show "오류가 발생했습니다"
- "다시 시도" button should attempt reload

**Step 2: Empty data states**
- Pages with no data should show meaningful empty states
- Not "undefined" or empty table with no message
- Each page: Dashboard, Orders, Results, Inspection Plans, NCR, etc.

**Step 3: Network error handling**
- Slow API response -> loading state shown (not hung UI)
- 401 Unauthorized -> redirect to login
- 403 Forbidden -> appropriate error message
- 500 Server Error -> error displayed (not raw JSON)

**Step 4: Console error sweep**
- Navigate through all pages, check browser console for:
  - React hydration errors
  - Unhandled promise rejections
  - TypeError / ReferenceError
  - React key warnings
  - Missing prop warnings

**Step 5: Write tests, fix bugs, commit**

---

## Task 24: Final Verification & Test Suite

**Step 1: Run all new bug-fix E2E tests**
```bash
cd agents/cell-mes/frontend
npx playwright test e2e/bug-fixes/ --reporter=list
```
Expected: All tests pass

**Step 2: Run backend tests**
```bash
uv run pytest tests/ -v --tb=short
```
Expected: All 149+ tests pass

**Step 3: Create bug inventory document**
Create `docs/phase1-bug-inventory.md` listing:
- Every bug found (page, description, severity)
- Fix applied (file, change)
- Test written (test file, test name)
- Screenshot reference

**Step 4: Commit all changes**
```bash
git add agents/cell-mes/frontend/ tests/ docs/
git commit -m "fix(frontend): Phase 1 Bug Safari - fix N bugs across 23 pages

- [List of bugs fixed]
- Added E2E regression tests for each fix
- No anti-patterns in new tests

Tests: N new E2E tests, all passing

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Verification Checklist

Before marking Phase 1 complete:

- [ ] Every page (23 total) visited and tested
- [ ] Every bug found has a screenshot
- [ ] Every bug has a failing E2E test written BEFORE the fix
- [ ] Every fix verified via browser AND test
- [ ] No new tests use anti-patterns (.catch, || true, console.log, waitForTimeout)
- [ ] All new tests pass
- [ ] All existing backend tests still pass
- [ ] Bug inventory document created
- [ ] All changes committed
