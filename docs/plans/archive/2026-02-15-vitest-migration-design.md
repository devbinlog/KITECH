# Vitest Migration Design

**Date:** 2026-02-15
**Target:** `agents/cell-mes/frontend/` (Next.js 14 + TypeScript)
**Scope:** Replace Playwright E2E entirely with Vitest. Add unit/component tests.

## Decision Summary

| Decision | Choice |
|----------|--------|
| Test runner | Vitest 3.x (replaces Playwright) |
| Approach | Workspace mode: unit (happy-dom) + e2e (browser) |
| Browser provider | Playwright via `@vitest/browser` |
| API mocking | None - live server required |
| Component testing | @testing-library/react in happy-dom |

## Dependencies

### Add
```
devDependencies:
  vitest: ^3.x
  @vitest/browser: ^3.x
  @vitest/ui: ^3.x
  @vitejs/plugin-react: ^4.x
  @testing-library/react: ^16.x
  @testing-library/jest-dom: ^6.x
  happy-dom: ^16.x
  playwright: (peer dep for @vitest/browser)
```

### Remove
```
@playwright/test
```

## Config Files

### vitest.workspace.ts
```ts
export default [
  {
    extends: './vitest.unit.config.ts',
    test: { name: 'unit' }
  },
  {
    extends: './vitest.e2e.config.ts',
    test: { name: 'e2e' }
  }
]
```

### vitest.unit.config.ts
```ts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'happy-dom',
    include: [
      '__tests__/unit/**/*.test.{ts,tsx}',
      '__tests__/components/**/*.test.{ts,tsx}',
    ],
    setupFiles: ['__tests__/setup.ts'],
    alias: {
      '@/': path.resolve(__dirname, './'),
      '@/generated/': path.resolve(__dirname, './src/generated/'),
    },
  },
})
```

### vitest.e2e.config.ts
```ts
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    include: ['__tests__/e2e/**/*.test.ts'],
    browser: {
      enabled: true,
      provider: 'playwright',
      instances: [{ browser: 'chromium' }],
    },
    testTimeout: 60_000,
    hookTimeout: 30_000,
  },
})
```

## Package Scripts

```json
{
  "test": "vitest",
  "test:unit": "vitest --project unit",
  "test:e2e": "vitest --project e2e",
  "test:ui": "vitest --ui",
  "test:coverage": "vitest --project unit --coverage"
}
```

## Directory Structure

```
frontend/
  vitest.workspace.ts
  vitest.unit.config.ts
  vitest.e2e.config.ts
  __tests__/
    setup.ts                    # @testing-library/jest-dom matchers
    unit/
      hooks/                    # useAuth, useEquipment, etc.
      stores/                   # Zustand stores
      utils/                    # formatters, validators
    components/
      chat/                     # ChatInput, ChatMessage, etc.
      dynamic/                  # DynamicRenderer, KPICard, etc.
      quality/                  # SPCChart, NCRForm, etc.
      scheduler/                # SchedulerGanttChart, etc.
      analytics/                # KPICard, UtilizationChart
    e2e/
      auth.test.ts
      dashboard.test.ts
      production.test.ts
      quality.test.ts
      scheduler.test.ts
      master.test.ts
      analytics.test.ts
      alarms.test.ts
      downtime.test.ts
      workflow.test.ts
      scenarios/
        operator-daily.test.ts
        planner-daily.test.ts
        manager-overview.test.ts
        ...
      crud/
        work-orders.test.ts
        equipments.test.ts
        products.test.ts
        ...
      validation/
        data-integrity.test.ts
        business-rules.test.ts
        calculations.test.ts
        ...
```

## E2E Migration: API Translation

| Playwright | Vitest Browser Mode |
|------------|-------------------|
| `import { test, expect } from '@playwright/test'` | `import { test, expect } from 'vitest'` + `import { page } from '@vitest/browser/context'` |
| `page.goto('/')` | `page.goto('http://localhost:3000/')` |
| `page.locator('.cls')` | `page.getByRole()` / `page.getByTestId()` |
| `expect(locator).toHaveText('X')` | `expect.element(locator).toHaveTextContent('X')` |
| `page.click('text=X')` | `page.getByText('X').click()` |
| `expect(page).toHaveURL(/pat/)` | `expect.poll(() => page.url()).toContain('pat')` |
| `test.use({ storageState })` | `beforeAll` with API login |

## E2E Migration Priority

1. **Phase 1 - Core pages** (5 specs): dashboard, production, quality, master, scheduler
2. **Phase 2 - CRUD operations** (8 specs): work-orders, equipments, products, processes, routings, scenarios, ncr, inspection-plans
3. **Phase 3 - Scenarios** (12 specs): operator-daily, planner-daily, manager-overview, quality-engineer, role-based specs
4. **Phase 4 - Validations** (10 specs): data-integrity, business-rules, calculations, cross-screen, manufacturing-integrity
5. **Phase 5 - Advanced** (remaining): deep-workflow, integration-workflow, AI validation, etc.

## Auth Handling

Current Playwright uses `fixtures/auth.ts` with storage state. Vitest replacement:

```ts
// __tests__/e2e/helpers/auth.ts
export async function loginAsAdmin() {
  const response = await fetch('http://localhost:8000/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: 'username=admin&password=admin123',
  });
  const data = await response.json();
  // Set cookie/token for subsequent requests
  document.cookie = `token=${data.access_token}; path=/`;
  return data.access_token;
}
```

## Requirements for Running Tests

- **Unit tests**: No external dependencies. Run anywhere.
- **E2E tests**: Requires:
  - Frontend dev server on port 3000 (`npm run dev`)
  - MES backend on port 8000
  - NL-Router on port 8001
  - (Optional) Cell-Scheduler on port 8002

## Cleanup After Migration

- Delete `e2e/` directory (old Playwright tests)
- Delete `playwright.config.ts`
- Delete `playwright-report/` and `test-results/`
- Remove `@playwright/test` from devDependencies
- Remove `test:e2e`, `test:e2e:ui`, `test:e2e:report` scripts (replaced by new ones)
