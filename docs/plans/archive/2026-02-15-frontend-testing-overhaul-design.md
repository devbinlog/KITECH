# Frontend Testing Overhaul Design

## Problem Statement

The manufacturing MES system has 52 Playwright E2E test files (26,000+ lines, 300+ tests) that **all pass** yet users continue reporting bugs across every category: data display errors, state sync issues, CRUD failures, UI breakage, and more.

### Root Cause Analysis

The test suite was designed to **never fail** rather than to catch bugs:

| Anti-Pattern | Count | Impact |
|---|---|---|
| `.catch(() => false)` swallowing errors | 639 | Broken UI elements silently ignored |
| `expect(... \|\| true).toBeTruthy()` | 60 | Tautological assertions, always pass |
| `console.log()` instead of `expect()` | 1,930 | Observations without verification |
| `waitForTimeout` hard-coded delays | 303 | Timing-dependent, flaky or wasteful |
| `if (!response.ok()) return` (silent skip) | 241 | API failures produce green tests |
| All tests run as `admin` | 52 files | No role/permission testing |

**Consequence:** Tests verify "something visible exists" instead of "the correct thing happened."

## Design

### Phase 1: Bug Safari (Immediate)

**Goal:** Find and fix real user-facing bugs by operating the app like a factory worker.

**Method:** Use Playwright browser (MCP) to manually test ALL 23 pages across 8 menu sections:

#### 1. Login (`/login`)
- Authentication flow, error messages, redirect after login

#### 2. Dashboard (`/dashboard`)
- KPI cards (NaN/null handling), production charts, equipment status grid, real-time updates

#### 3. Master Data / 기준정보 (5 pages)
- **Processes** (`/master/processes`) - CRUD, validation, table display
- **Products** (`/master/products`) - CRUD, product code uniqueness
- **Routings** (`/master/routings`) - Process sequence editing, drag-and-drop
- **Scenarios** (`/master/scenarios`) - Scenario creation, parameter editing
- **Equipments** (`/master/equipments`) - 4 internal tabs: List, Status, History, Maintenance

#### 4. Production / 생산관리 (4 pages)
- **Work Orders** (`/production/orders`) - Full lifecycle: Create -> Start -> Record -> Complete -> Cancel
- **Results** (`/production/results`) - Production result recording, yield_rate display
- **Downtime** (`/production/downtime`) - 2 tabs: Records, Analysis charts
- **Alarms** (`/production/alarms`) - 2 tabs: Active alarms, Alarm history

#### 5. Scheduler / 스케줄러 (3 pages)
- **Status** (`/scheduler/status`) - Current schedule display, Gantt chart
- **Execute** (`/scheduler/execute`) - Solver selection, parameter input, execution
- **Settings** (`/scheduler/settings`) - Solver configuration, constraint settings

#### 6. Quality / 품질관리 (5 pages)
- **Dashboard** (`/quality/dashboard`) - Quality KPIs, defect rate trends
- **Inspection Plans** (`/quality/inspection-plans`) - Plan CRUD, criteria editing
- **Inspection Results** (`/quality/inspection-results`) - Result recording, pass/fail
- **SPC** (`/quality/spc`) - Control charts, Cp/Cpk calculations
- **NCR** (`/quality/ncr`) - Non-conformance creation, status tracking

#### 7. Analytics / 분석리포트 (3 pages)
- **Dashboard** (`/analytics/dashboard`) - Production trends, comparison charts
- **Equipment** (`/analytics/equipment`) - Utilization rates, OEE
- **LOT Trace** (`/analytics/lot-trace`) - Traceability timeline, lot search

#### 8. AI Assistant / AI 어시스턴트 (1 page)
- **Chat** (`/ai/chat`) - NL query input, response rendering, conversation history

**Per-screen checklist:**
- Visual: Layout integrity, no NaN/null/undefined displayed
- Data: Displayed values match API responses
- Interaction: Buttons, forms, modals work correctly
- Error: Invalid inputs show appropriate messages
- State: Screen updates correctly after mutations

**Bug fix process:**
1. Capture screenshot of bug
2. Write failing E2E test first (TDD)
3. Fix the code
4. Verify test passes
5. Commit

**New test principles (mandatory for all new tests):**
- No `.catch(() => false)` - let assertions fail
- No `expect(... || true)` - tests must be falsifiable
- No `waitForTimeout` - use `waitForSelector` / `waitForResponse`
- Every mutation must be followed by result verification
- Use API fixtures for test data setup, not conditional skips

### Phase 2: Anti-Pattern Removal (After Bug Safari)

**Goal:** Transform existing E2E tests from "always pass" to "catch real bugs."

**Priority order:**
1. **High:** `production.spec.ts`, `dashboard.spec.ts`, `work-orders.crud.spec.ts` (core features)
2. **Medium:** `quality.spec.ts`, `scheduler.spec.ts`, `master.spec.ts`
3. **Low:** `validation/` folder (API tests - consider migrating to backend pytest)

**Transformation patterns:**

```typescript
// BEFORE: Always passes
const hasCards = await page.locator('...').isVisible().catch(() => false);
expect(hasCards || true).toBeTruthy();

// AFTER: Fails when broken
await expect(page.locator('...')).toBeVisible({ timeout: 10000 });
```

```typescript
// BEFORE: Skips silently when data missing
if (hasReadyOrder) {
  // ... test logic
}
expect(true).toBeTruthy();

// AFTER: Ensures data exists via fixture
test.beforeEach(async ({ request }) => {
  await request.post('/api/v1/production/orders', { data: testOrder });
});
await expect(page.locator('tr:has-text("READY")')).toBeVisible();
```

```typescript
// BEFORE: Hard-coded delay
await page.waitForTimeout(2000);

// AFTER: Wait for actual condition
await page.waitForResponse(resp => resp.url().includes('/api/v1/production/orders'));
```

**Decision for each failing test after anti-pattern removal:**
- Real bug found -> Fix code, keep test
- Test environment issue -> Add proper fixture/setup
- Duplicate of another test -> Delete
- Testing wrong thing -> Rewrite or move to unit test

### Phase 3: New Test Framework (Progressive)

**Goal:** Build a proper test pyramid with fast component tests and focused E2E tests.

**Component Tests (Vitest + React Testing Library):**

Setup:
- Add `vitest` + `@testing-library/react` + `@testing-library/jest-dom`
- Configure in `vitest.config.ts` alongside existing Next.js config

Priority components to test:
- `KPICard` - Number formatting, null/undefined handling, color logic
- `DynamicDataTable` - Sort, filter, pagination, empty state
- `StatusBadge` - Status-to-color mapping for all states
- `WorkOrderForm` / `NCRForm` - Validation rules, required fields
- `DynamicLineChart` / `DynamicBarChart` - Data transformation, empty data
- `ErrorBoundary` - Error display, recovery
- `LoadingState` - Loading indicator behavior

**Target test pyramid:**
- Component unit tests: ~100 (fast feedback, < 30 seconds)
- E2E workflow tests: ~30 (real user scenarios, < 10 minutes)
- Existing 52 E2E files -> Consolidate to ~20 (remove duplicates, dead tests)

**Test data strategy:**
- API fixture helpers for creating/cleaning test data
- Seed script for known baseline state
- Each test responsible for its own data (setup + teardown)

## Success Criteria

1. **Phase 1:** All 23 pages can be operated without encountering bugs
2. **Phase 2:** E2E tests actually fail when bugs are introduced (mutation testing)
3. **Phase 3:** Component tests catch data formatting/null bugs before E2E
4. **Overall:** User bug reports decrease by 80%+ within one iteration cycle

## Files Modified

### Phase 1 (Bug fixes)
- `agents/cell-mes/frontend/app/` - Page components with bugs
- `agents/cell-mes/frontend/components/` - Shared components with bugs
- `agents/cell-mes/frontend/e2e/` - New proper E2E tests

### Phase 2 (Anti-pattern removal)
- `agents/cell-mes/frontend/e2e/*.spec.ts` - All 52 existing test files
- `agents/cell-mes/frontend/e2e/fixtures/` - New test data fixtures

### Phase 3 (New framework)
- `agents/cell-mes/frontend/vitest.config.ts` - New
- `agents/cell-mes/frontend/__tests__/` - New component test directory
- `agents/cell-mes/frontend/package.json` - Add vitest dependencies
