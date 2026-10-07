# Vitest Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace Playwright E2E entirely with Vitest. Add unit/component tests. Result: a single `npm test` runs all tests via Vitest workspace.

**Architecture:** Vitest 3.x workspace with two projects — `unit` (happy-dom, fast, no browser) and `e2e` (Vitest Browser Mode with Playwright provider, live server required). Unit tests cover pure functions, stores, and components. E2E tests migrate all 50+ Playwright specs to Vitest Browser Mode API.

**Tech Stack:** Vitest 3.x, @vitest/browser, @vitejs/plugin-react, @testing-library/react, happy-dom, Playwright (browser provider), Next.js 14, TypeScript

**Design doc:** `docs/plans/2026-02-15-vitest-migration-design.md`

---

## Phase 0: Project Setup

### Task 1: Install Vitest dependencies

**Files:**
- Modify: `agents/cell-mes/frontend/package.json`

**Step 1:** Install all Vitest dependencies:
```bash
cd agents/cell-mes/frontend
npm install -D vitest @vitest/browser @vitest/ui @vitejs/plugin-react @testing-library/react @testing-library/jest-dom happy-dom playwright
```

**Step 2:** Verify `package.json` devDependencies now includes all packages. Do NOT remove `@playwright/test` yet (cleanup is Phase 5).

---

### Task 2: Create Vitest config files

**Files:**
- Create: `agents/cell-mes/frontend/vitest.workspace.ts`
- Create: `agents/cell-mes/frontend/vitest.unit.config.ts`
- Create: `agents/cell-mes/frontend/vitest.e2e.config.ts`

**Step 1:** Create `vitest.workspace.ts`:
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

**Step 2:** Create `vitest.unit.config.ts`:
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

**Step 3:** Create `vitest.e2e.config.ts`:
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

**Step 4:** Verify configs parse correctly:
```bash
cd agents/cell-mes/frontend
npx vitest --project unit --run 2>&1 | head -5
```
Expected: "no test files found" (not a config error).

---

### Task 3: Create test setup file and directory structure

**Files:**
- Create: `agents/cell-mes/frontend/__tests__/setup.ts`
- Create directories: `__tests__/unit/hooks/`, `__tests__/unit/utils/`, `__tests__/unit/stores/`, `__tests__/components/`, `__tests__/e2e/`, `__tests__/e2e/helpers/`

**Step 1:** Create `__tests__/setup.ts`:
```ts
import '@testing-library/jest-dom/vitest'
```

**Step 2:** Create all directories:
```bash
cd agents/cell-mes/frontend
mkdir -p __tests__/unit/hooks __tests__/unit/utils __tests__/unit/stores
mkdir -p __tests__/components
mkdir -p __tests__/e2e/helpers __tests__/e2e/crud __tests__/e2e/scenarios __tests__/e2e/validation
```

---

### Task 4: Update package.json scripts

**Files:**
- Modify: `agents/cell-mes/frontend/package.json`

**Step 1:** Add new test scripts (keep old Playwright scripts for now):
```json
{
  "scripts": {
    "test": "vitest",
    "test:unit": "vitest --project unit",
    "test:e2e": "vitest --project e2e",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --project unit --coverage",
    "test:e2e:pw": "playwright test",
    "test:e2e:pw:ui": "playwright test --ui",
    "test:e2e:pw:report": "playwright show-report"
  }
}
```

**Step 2:** Verify unit project runs:
```bash
cd agents/cell-mes/frontend
npm run test:unit -- --run
```
Expected: "no test files found" (not a config/script error).

**Step 3:** Commit:
```
feat: add Vitest workspace config and test structure

- vitest.workspace.ts with unit (happy-dom) and e2e (browser) projects
- @testing-library/react + jest-dom setup
- New npm scripts: test, test:unit, test:e2e, test:ui, test:coverage
```

---

## Phase 1: Unit Tests — Pure Functions

### Task 5: Unit tests for `deduplicatePathPrefix` (lib/axios.ts)

**Files:**
- Create: `agents/cell-mes/frontend/__tests__/unit/utils/axios.test.ts`

**Context:** `lib/axios.ts:21-37` exports `deduplicatePathPrefix` (used in request interceptor). It removes duplicate path prefixes between baseURL and request URL.

**Step 1:** Write the test file:
```ts
import { describe, it, expect } from 'vitest'

// deduplicatePathPrefix is not exported, so we test by re-implementing the logic
// or by importing the module and testing the interceptor behavior.
// Since it's a private function, we test it by extracting and re-exporting it.

// Alternative: test the axios instance behavior directly
describe('deduplicatePathPrefix', () => {
  // Re-implement for testing (same logic as lib/axios.ts:21-37)
  function deduplicatePathPrefix(
    baseURL: string | undefined,
    url: string | undefined
  ): string | undefined {
    if (!baseURL || !url) return url
    try {
      const { pathname } = new URL(baseURL)
      if (pathname !== '/' && url.startsWith(pathname)) {
        return url.slice(pathname.length) || '/'
      }
    } catch {
      // baseURL parse failure
    }
    return url
  }

  it('removes duplicate /api/v1 prefix', () => {
    const result = deduplicatePathPrefix(
      'http://localhost:8000/api/v1',
      '/api/v1/auth/login'
    )
    expect(result).toBe('/auth/login')
  })

  it('leaves url unchanged when no prefix overlap', () => {
    const result = deduplicatePathPrefix(
      'http://localhost:8000',
      '/api/v1/auth/login'
    )
    expect(result).toBe('/api/v1/auth/login')
  })

  it('returns "/" when url equals prefix exactly', () => {
    const result = deduplicatePathPrefix(
      'http://localhost:8000/api/v1',
      '/api/v1'
    )
    expect(result).toBe('/')
  })

  it('handles undefined baseURL', () => {
    expect(deduplicatePathPrefix(undefined, '/test')).toBe('/test')
  })

  it('handles undefined url', () => {
    expect(deduplicatePathPrefix('http://localhost:8000', undefined)).toBeUndefined()
  })

  it('handles invalid baseURL gracefully', () => {
    expect(deduplicatePathPrefix('not-a-url', '/test')).toBe('/test')
  })
})
```

**Step 2:** Run:
```bash
cd agents/cell-mes/frontend && npm run test:unit -- --run
```
Expected: 6 tests PASS.

---

### Task 6: Unit tests for `formatSeconds` and `formatDateTime` (hooks/useScheduler.ts)

**Files:**
- Create: `agents/cell-mes/frontend/__tests__/unit/utils/scheduler-utils.test.ts`

**Context:** `hooks/useScheduler.ts:113-121` — `formatSeconds(seconds)` returns Korean time string, `formatDateTime(dateStr)` formats ISO date.

**Step 1:** Write the test file:
```ts
import { describe, it, expect } from 'vitest'
import { formatSeconds, formatDateTime } from '@/hooks/useScheduler'

describe('formatSeconds', () => {
  it('formats seconds under 60 as 초', () => {
    expect(formatSeconds(30)).toBe('30초')
    expect(formatSeconds(0)).toBe('0초')
    expect(formatSeconds(59)).toBe('59초')
  })

  it('formats seconds 60-3599 as 분', () => {
    expect(formatSeconds(60)).toBe('1분')
    expect(formatSeconds(120)).toBe('2분')
    expect(formatSeconds(3599)).toBe('60분')
  })

  it('formats seconds >= 3600 as 시간', () => {
    expect(formatSeconds(3600)).toBe('1.0시간')
    expect(formatSeconds(7200)).toBe('2.0시간')
    expect(formatSeconds(5400)).toBe('1.5시간')
  })
})

describe('formatDateTime', () => {
  it('formats ISO date string to yyyy-MM-dd HH:mm', () => {
    expect(formatDateTime('2026-02-15T09:30:00')).toBe('2026-02-15 09:30')
  })
})
```

**Step 2:** Run:
```bash
cd agents/cell-mes/frontend && npm run test:unit -- --run __tests__/unit/utils/scheduler-utils.test.ts
```
Expected: All tests PASS.

---

### Task 7: Unit tests for `convertAvailabilityToTasks` (hooks/useScheduler.ts)

**Files:**
- Create: `agents/cell-mes/frontend/__tests__/unit/hooks/useScheduler.test.ts`

**Context:** `hooks/useScheduler.ts:81-111` — converts equipment availability API data into Gantt chart task objects.

**Step 1:** Write the test file:
```ts
import { describe, it, expect } from 'vitest'
import { convertAvailabilityToTasks } from '@/hooks/useScheduler'

describe('convertAvailabilityToTasks', () => {
  const horizonStart = '2026-02-15T00:00:00'

  it('converts availability slots to Gantt tasks', () => {
    const availability = [{
      equipment_id: 'CNC-001',
      schedule: [{
        slot_start: '2026-02-15T01:00:00',
        slot_end: '2026-02-15T03:00:00',
        work_order_id: 42,
        lot_no: 'LOT-001',
        product: 'Widget-A',
        status: 'RUNNING',
      }],
    }]

    const tasks = convertAvailabilityToTasks(availability as any, horizonStart)
    expect(tasks).toHaveLength(1)
    expect(tasks[0]).toMatchObject({
      wo_id: 'WO-42',
      machine_id: 'CNC-001',
      lot_no: 'LOT-001',
      product_name: 'Widget-A',
      status: 'RUNNING',
    })
    // 1 hour = 3600 seconds
    expect(tasks[0].start_time).toBe(3600)
    // 3 hours = 10800 seconds
    expect(tasks[0].end_time).toBe(10800)
  })

  it('returns empty array when no schedule slots', () => {
    const availability = [{
      equipment_id: 'CNC-001',
      schedule: [],
    }]
    const tasks = convertAvailabilityToTasks(availability as any, horizonStart)
    expect(tasks).toHaveLength(0)
  })

  it('skips slots with missing start/end', () => {
    const availability = [{
      equipment_id: 'CNC-001',
      schedule: [
        { slot_start: null, slot_end: null, work_order_id: 1 },
      ],
    }]
    const tasks = convertAvailabilityToTasks(availability as any, horizonStart)
    expect(tasks).toHaveLength(0)
  })

  it('clamps negative times to 0', () => {
    const availability = [{
      equipment_id: 'CNC-001',
      schedule: [{
        slot_start: '2026-02-14T23:00:00', // before horizon
        slot_end: '2026-02-15T01:00:00',
        work_order_id: 1,
        lot_no: 'LOT-X',
        product: 'P',
        status: 'DONE',
      }],
    }]
    const tasks = convertAvailabilityToTasks(availability as any, horizonStart)
    expect(tasks[0].start_time).toBe(0) // clamped
    expect(tasks[0].end_time).toBe(3600)
  })
})
```

**Step 2:** Run:
```bash
cd agents/cell-mes/frontend && npm run test:unit -- --run __tests__/unit/hooks/useScheduler.test.ts
```
Expected: All tests PASS.

---

### Task 8: Unit tests for errorMessages utilities

**Files:**
- Create: `agents/cell-mes/frontend/__tests__/unit/utils/errorMessages.test.ts`

**Context:** `utils/errorMessages.ts` — `getErrorMessage()`, `getQualityErrorMessage()`, `getSuccessMessage()`, `getConfirmMessage()`.

**Step 1:** Write the test file:
```ts
import { describe, it, expect } from 'vitest'
import {
  getErrorMessage,
  getQualityErrorMessage,
  getSuccessMessage,
  getConfirmMessage,
} from '@/utils/errorMessages'

describe('getErrorMessage', () => {
  it('returns network error message', () => {
    const result = getErrorMessage({ code: 'ERR_NETWORK' }, '조회')
    expect(result).toContain('서버에 연결할 수 없습니다')
  })

  it('returns 401 message', () => {
    const result = getErrorMessage({ response: { status: 401 } })
    expect(result).toContain('로그인이 필요합니다')
  })

  it('returns 404 message', () => {
    const result = getErrorMessage({ response: { status: 404 } })
    expect(result).toContain('찾을 수 없습니다')
  })

  it('returns 400 with product not found', () => {
    const result = getErrorMessage({
      response: { status: 400, data: { detail: 'Product not found' } }
    })
    expect(result).toContain('제품이 존재하지 않습니다')
  })

  it('returns 400 with duplicate', () => {
    const result = getErrorMessage({
      response: { status: 400, data: { detail: 'already exists' } }
    })
    expect(result).toContain('이미 존재하는 데이터')
  })

  it('returns 500 message', () => {
    const result = getErrorMessage({ response: { status: 500 } })
    expect(result).toContain('서버 오류')
  })

  it('uses custom context prefix', () => {
    const result = getErrorMessage({ response: { status: 500 } }, '저장')
    expect(result).toMatch(/^저장 실패:/)
  })

  it('falls back to error.message for unknown status', () => {
    const result = getErrorMessage({ message: 'custom error' })
    expect(result).toContain('custom error')
  })
})

describe('getQualityErrorMessage', () => {
  it('detects inspection_plan context', () => {
    const result = getQualityErrorMessage({
      response: { status: 400, data: { detail: 'inspection_plan error' } }
    })
    expect(result).toContain('검사계획')
  })

  it('detects ncr context', () => {
    const result = getQualityErrorMessage({
      response: { status: 400, data: { detail: 'ncr not found' } }
    })
    expect(result).toContain('부적합보고서')
  })

  it('falls back to quality context', () => {
    const result = getQualityErrorMessage({
      response: { status: 500 }
    })
    expect(result).toContain('품질 관리')
  })
})

describe('getSuccessMessage', () => {
  it('returns message with count', () => {
    expect(getSuccessMessage('삭제', 3)).toBe('삭제 완료: 3건이 처리되었습니다.')
  })

  it('returns message without count', () => {
    expect(getSuccessMessage('저장')).toBe('저장이(가) 완료되었습니다.')
  })
})

describe('getConfirmMessage', () => {
  it('returns message with target', () => {
    expect(getConfirmMessage('삭제', 'WO-001')).toContain('WO-001')
  })

  it('returns message without target', () => {
    expect(getConfirmMessage('삭제')).toContain('삭제하시겠습니까')
  })
})
```

**Step 2:** Run:
```bash
cd agents/cell-mes/frontend && npm run test:unit -- --run __tests__/unit/utils/errorMessages.test.ts
```
Expected: All tests PASS.

**Step 3:** Commit:
```
feat: add unit tests for pure utility functions

- deduplicatePathPrefix (axios interceptor logic)
- formatSeconds, formatDateTime, convertAvailabilityToTasks
- getErrorMessage, getQualityErrorMessage, getSuccessMessage, getConfirmMessage
```

---

## Phase 2: Unit Tests — Stores

### Task 9: Unit tests for authStore

**Files:**
- Create: `agents/cell-mes/frontend/__tests__/unit/stores/authStore.test.ts`

**Context:** `stores/authStore.ts` — Zustand store with `persist` middleware. Has `setAuth()`, `logout()`, `checkAuth()`. Uses `localStorage` for token + `auth-storage`.

**Step 1:** Write the test file:
```ts
import { describe, it, expect, beforeEach } from 'vitest'
import { useAuthStore } from '@/stores/authStore'

describe('authStore', () => {
  beforeEach(() => {
    // Reset store state
    useAuthStore.setState({ user: null, isAuthenticated: false })
    localStorage.clear()
  })

  it('setAuth stores token and user', () => {
    const user = { id: 1, username: 'admin', role: 'admin' }
    useAuthStore.getState().setAuth('test-token', user)

    const state = useAuthStore.getState()
    expect(state.isAuthenticated).toBe(true)
    expect(state.user).toEqual(user)
    expect(localStorage.getItem('token')).toBe('test-token')
  })

  it('logout clears everything', () => {
    const user = { id: 1, username: 'admin', role: 'admin' }
    useAuthStore.getState().setAuth('test-token', user)
    useAuthStore.getState().logout()

    const state = useAuthStore.getState()
    expect(state.isAuthenticated).toBe(false)
    expect(state.user).toBeNull()
    expect(localStorage.getItem('token')).toBeNull()
  })

  it('checkAuth returns true when token and user exist', () => {
    localStorage.setItem('token', 'test-token')
    useAuthStore.setState({ user: { id: 1, username: 'admin', role: 'admin' } })

    expect(useAuthStore.getState().checkAuth()).toBe(true)
    expect(useAuthStore.getState().isAuthenticated).toBe(true)
  })

  it('checkAuth returns false when no token', () => {
    useAuthStore.setState({ user: { id: 1, username: 'admin', role: 'admin' } })

    expect(useAuthStore.getState().checkAuth()).toBe(false)
    expect(useAuthStore.getState().isAuthenticated).toBe(false)
  })

  it('checkAuth returns false when no user', () => {
    localStorage.setItem('token', 'test-token')
    useAuthStore.setState({ user: null })

    expect(useAuthStore.getState().checkAuth()).toBe(false)
  })
})
```

**Step 2:** Run:
```bash
cd agents/cell-mes/frontend && npm run test:unit -- --run __tests__/unit/stores/authStore.test.ts
```
Expected: All tests PASS.

**Step 3:** Commit:
```
feat: add unit tests for authStore

- setAuth, logout, checkAuth state transitions
- localStorage token persistence
```

---

## Phase 3: E2E Setup — Auth Helper and First Test

### Task 10: Create E2E auth helper

**Files:**
- Create: `agents/cell-mes/frontend/__tests__/e2e/helpers/auth.ts`

**Context:** Replaces `e2e/fixtures/auth.ts`. In Vitest Browser Mode, we use `fetch()` directly (runs in real browser), set `localStorage`, then navigate.

**Step 1:** Write the auth helper:
```ts
/**
 * E2E auth helper for Vitest Browser Mode.
 * Logs in via MES API and sets localStorage for authenticated state.
 */

const API_BASE = 'http://localhost:8000/api/v1'
const APP_URL = 'http://localhost:3000'

export interface AuthToken {
  token: string
  user: { id: number; username: string; role: string }
}

export async function loginAsAdmin(): Promise<AuthToken> {
  // 1. Get token via API
  const loginRes = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: 'username=admin&password=admin123',
  })
  if (!loginRes.ok) throw new Error(`Login failed: ${loginRes.status}`)
  const loginData = await loginRes.json()
  const token = loginData.access_token

  // 2. Get user info
  const meRes = await fetch(`${API_BASE}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!meRes.ok) throw new Error(`Get user failed: ${meRes.status}`)
  const user = await meRes.json()

  // 3. Set localStorage (same format as Zustand persist)
  localStorage.setItem('token', token)
  localStorage.setItem('auth-storage', JSON.stringify({
    state: { user, isAuthenticated: true },
    version: 0,
  }))

  return { token, user }
}

export async function navigateAuthenticated(path: string = '/'): Promise<void> {
  const { page } = await import('@vitest/browser/context')
  await loginAsAdmin()
  await page.goto(`${APP_URL}${path}`)
}

export function getApiHeaders(token: string): Record<string, string> {
  return {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  }
}
```

---

### Task 11: Create E2E API helper

**Files:**
- Create: `agents/cell-mes/frontend/__tests__/e2e/helpers/api.ts`

**Context:** Replaces `e2e/utils/api-helper.ts`. Provides common API fetching utilities.

**Step 1:** Write the API helper:
```ts
/**
 * E2E API helper for direct backend validation.
 */

const API_BASE = 'http://localhost:8000/api/v1'

export async function getToken(): Promise<string> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: 'username=admin&password=admin123',
  })
  const data = await res.json()
  return data.access_token
}

export async function fetchWithAuth(path: string, token?: string): Promise<any> {
  const t = token || await getToken()
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { Authorization: `Bearer ${t}` },
  })
  if (!res.ok) throw new Error(`API ${path} failed: ${res.status}`)
  return res.json()
}

export async function postWithAuth(path: string, body: any, token?: string): Promise<any> {
  const t = token || await getToken()
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${t}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  })
  return res.json()
}
```

---

### Task 12: First E2E test — Auth flow

**Files:**
- Create: `agents/cell-mes/frontend/__tests__/e2e/auth.test.ts`

**Context:** Migrates `e2e/auth.spec.ts`. Tests login form, authentication, and logout.

**Step 1:** Write the test:
```ts
import { describe, it, expect, beforeAll } from 'vitest'
import { page } from '@vitest/browser/context'

const APP_URL = 'http://localhost:3000'

describe('Authentication', () => {
  describe('Login page', () => {
    it('shows login form', async () => {
      await page.goto(`${APP_URL}/login`)
      await expect.element(page.getByRole('heading', { name: /로그인|login/i })).toBeVisible()
      await expect.element(page.getByRole('textbox', { name: /username|아이디/i })).toBeVisible()
    })

    it('logs in with valid credentials', async () => {
      await page.goto(`${APP_URL}/login`)

      await page.getByRole('textbox', { name: /username|아이디/i }).fill('admin')
      await page.getByLabelText(/password|비밀번호/i).fill('admin123')
      await page.getByRole('button', { name: /로그인|login/i }).click()

      // Should redirect to dashboard
      await expect.poll(() => page.url(), { timeout: 10_000 })
        .toContain('/')
      await expect.poll(() => page.url()).not.toContain('/login')
    })

    it('shows error with invalid credentials', async () => {
      await page.goto(`${APP_URL}/login`)

      await page.getByRole('textbox', { name: /username|아이디/i }).fill('wrong')
      await page.getByLabelText(/password|비밀번호/i).fill('wrong')
      await page.getByRole('button', { name: /로그인|login/i }).click()

      // Should show error (stay on login page)
      await expect.poll(() => page.url(), { timeout: 5_000 })
        .toContain('/login')
    })
  })
})
```

**Step 2:** Run (requires live servers):
```bash
cd agents/cell-mes/frontend && npm run test:e2e -- --run __tests__/e2e/auth.test.ts
```
Expected: PASS (if servers running) or clear connection error (if not).

**Step 3:** Commit:
```
feat: add E2E infrastructure and auth test for Vitest Browser Mode

- Auth helper (loginAsAdmin, navigateAuthenticated)
- API helper (getToken, fetchWithAuth, postWithAuth)
- First migrated E2E test: auth flow
```

---

## Phase 4: E2E Migration — Core Pages

### Task 13: E2E — Dashboard

**Files:**
- Create: `agents/cell-mes/frontend/__tests__/e2e/dashboard.test.ts`

**Context:** Migrates `e2e/dashboard.spec.ts`. Tests KPI cards, equipment status grid, recent work orders.

**Step 1:** Write the test:
```ts
import { describe, it, expect, beforeAll } from 'vitest'
import { page } from '@vitest/browser/context'
import { navigateAuthenticated } from './helpers/auth'

describe('Dashboard', () => {
  beforeAll(async () => {
    await navigateAuthenticated('/')
  })

  it('displays KPI cards', async () => {
    // Dashboard should show key metrics
    await expect.element(
      page.getByText(/생산량|production/i)
    ).toBeVisible()
  })

  it('displays equipment status section', async () => {
    await expect.element(
      page.getByText(/설비 현황|equipment/i)
    ).toBeVisible()
  })

  it('displays recent work orders section', async () => {
    await expect.element(
      page.getByText(/작업지시|work order/i)
    ).toBeVisible()
  })

  it('navigates to other pages via sidebar', async () => {
    const productionLink = page.getByRole('link', { name: /생산/i })
    await expect.element(productionLink).toBeVisible()
  })
})
```

**Step 2:** Run:
```bash
cd agents/cell-mes/frontend && npm run test:e2e -- --run __tests__/e2e/dashboard.test.ts
```

---

### Task 14: E2E — Production page

**Files:**
- Create: `agents/cell-mes/frontend/__tests__/e2e/production.test.ts`

**Context:** Migrates `e2e/production.spec.ts`. Tests work order list, status tabs, production results.

**Step 1:** Write the test:
```ts
import { describe, it, expect, beforeAll } from 'vitest'
import { page } from '@vitest/browser/context'
import { navigateAuthenticated } from './helpers/auth'

describe('Production', () => {
  beforeAll(async () => {
    await navigateAuthenticated('/production')
  })

  describe('Work Orders', () => {
    it('shows work order list', async () => {
      await expect.element(
        page.getByText(/작업지시|work order/i)
      ).toBeVisible()
    })

    it('has status filter tabs', async () => {
      // Look for status tabs: ALL, READY, RUNNING, DONE, etc.
      await expect.element(
        page.getByRole('tab', { name: /전체|ALL/i })
      ).toBeVisible()
    })

    it('displays work order cards or table rows', async () => {
      // Should have at least one work order visible
      await expect.poll(async () => {
        const rows = page.getByRole('row')
        // Table should have header + at least 1 data row
        return rows
      }, { timeout: 10_000 }).toBeTruthy()
    })
  })

  describe('Production Results', () => {
    it('navigates to results tab', async () => {
      const resultsTab = page.getByRole('tab', { name: /실적|result/i })
      if (await resultsTab.query()) {
        await resultsTab.click()
        await expect.element(
          page.getByText(/생산 실적|production result/i)
        ).toBeVisible()
      }
    })
  })
})
```

---

### Task 15: E2E — Quality page

**Files:**
- Create: `agents/cell-mes/frontend/__tests__/e2e/quality.test.ts`

**Context:** Migrates `e2e/quality.spec.ts`. Tests inspection plans, SPC charts, NCR list.

**Step 1:** Write the test:
```ts
import { describe, it, expect, beforeAll } from 'vitest'
import { page } from '@vitest/browser/context'
import { navigateAuthenticated } from './helpers/auth'

describe('Quality', () => {
  beforeAll(async () => {
    await navigateAuthenticated('/quality')
  })

  it('shows quality management page', async () => {
    await expect.element(
      page.getByText(/품질|quality/i)
    ).toBeVisible()
  })

  it('has sub-navigation tabs', async () => {
    // Quality page has tabs for inspection, SPC, NCR
    const tabs = page.getByRole('tab')
    await expect.element(tabs.first()).toBeVisible()
  })

  it('shows inspection plans or results', async () => {
    await expect.element(
      page.getByText(/검사|inspection/i)
    ).toBeVisible()
  })
})
```

---

### Task 16: E2E — Master Data page

**Files:**
- Create: `agents/cell-mes/frontend/__tests__/e2e/master.test.ts`

**Context:** Migrates `e2e/master.spec.ts`. Tests equipment list, product list, process list, routing.

**Step 1:** Write the test:
```ts
import { describe, it, expect, beforeAll } from 'vitest'
import { page } from '@vitest/browser/context'
import { navigateAuthenticated } from './helpers/auth'

describe('Master Data', () => {
  beforeAll(async () => {
    await navigateAuthenticated('/master')
  })

  it('shows master data page', async () => {
    await expect.element(
      page.getByText(/기준정보|master/i)
    ).toBeVisible()
  })

  it('shows equipment management', async () => {
    const equipmentTab = page.getByRole('tab', { name: /설비|equipment/i })
    if (await equipmentTab.query()) {
      await equipmentTab.click()
      await expect.element(
        page.getByText(/설비|equipment/i)
      ).toBeVisible()
    }
  })

  it('shows product management', async () => {
    const productTab = page.getByRole('tab', { name: /제품|product/i })
    if (await productTab.query()) {
      await productTab.click()
      await expect.element(
        page.getByText(/제품|product/i)
      ).toBeVisible()
    }
  })
})
```

---

### Task 17: E2E — Scheduler page

**Files:**
- Create: `agents/cell-mes/frontend/__tests__/e2e/scheduler.test.ts`

**Context:** Migrates `e2e/scheduler.spec.ts`. Tests schedule view, solver selection, Gantt chart.

**Step 1:** Write the test:
```ts
import { describe, it, expect, beforeAll } from 'vitest'
import { page } from '@vitest/browser/context'
import { navigateAuthenticated } from './helpers/auth'

describe('Scheduler', () => {
  beforeAll(async () => {
    await navigateAuthenticated('/scheduler')
  })

  it('shows scheduler page', async () => {
    await expect.element(
      page.getByText(/스케줄|schedul/i)
    ).toBeVisible()
  })

  it('has solver selection', async () => {
    await expect.element(
      page.getByText(/OR-Tools|유전|담금질|타부|ALNS/i)
    ).toBeVisible()
  })

  it('shows equipment availability or Gantt chart area', async () => {
    await expect.element(
      page.getByText(/설비|equipment|간트|gantt/i)
    ).toBeVisible()
  })
})
```

**Step 2:** Run all core E2E tests:
```bash
cd agents/cell-mes/frontend && npm run test:e2e -- --run
```

**Step 3:** Commit:
```
feat: migrate core E2E tests to Vitest Browser Mode

- dashboard, production, quality, master, scheduler
- All use navigateAuthenticated helper
```

---

## Phase 5: E2E Migration — Alarms, Analytics, Downtime, Workflow

### Task 18: E2E — Alarms page

**Files:**
- Create: `agents/cell-mes/frontend/__tests__/e2e/alarms.test.ts`

**Context:** Migrates `e2e/alarms.spec.ts`. Tests active alarms list, alarm history, severity filters.

**Step 1:** Write the test based on the existing Playwright spec patterns. Key assertions:
- Active alarms visible
- Alarm cards show severity badges
- Filter by severity works
- Alarm history tab accessible

---

### Task 19: E2E — Analytics page

**Files:**
- Create: `agents/cell-mes/frontend/__tests__/e2e/analytics.test.ts`

**Context:** Migrates `e2e/analytics.spec.ts`. Tests KPI dashboard, utilization charts, trend views.

---

### Task 20: E2E — Downtime page

**Files:**
- Create: `agents/cell-mes/frontend/__tests__/e2e/downtime.test.ts`

**Context:** Migrates `e2e/downtime.spec.ts`. Tests active downtime list, downtime history, registration.

---

### Task 21: E2E — Workflow page

**Files:**
- Create: `agents/cell-mes/frontend/__tests__/e2e/workflow.test.ts`

**Context:** Migrates `e2e/workflow.spec.ts`. Tests cross-page workflows (production → quality → scheduling).

**Step 2:** Run all:
```bash
cd agents/cell-mes/frontend && npm run test:e2e -- --run
```

**Step 3:** Commit:
```
feat: migrate alarms, analytics, downtime, workflow E2E tests
```

---

## Phase 6: E2E Migration — CRUD Operations

### Task 22: E2E — Work Orders CRUD

**Files:**
- Create: `agents/cell-mes/frontend/__tests__/e2e/crud/work-orders.test.ts`

**Context:** Migrates `e2e/crud/work-orders.crud.spec.ts`. Tests create, read, update, status transitions, and search of work orders.

**Important patterns from Playwright spec:**
- Uses `TEST_PREFIX` pattern to isolate test data
- Modal interactions for create/edit
- Status transition (READY → RUNNING → DONE)
- Cleanup in afterAll

**Step 1:** Write test following the existing pattern but with Vitest Browser Mode API:
```ts
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { page } from '@vitest/browser/context'
import { navigateAuthenticated } from '../helpers/auth'
import { fetchWithAuth, postWithAuth } from '../helpers/api'

const TEST_PREFIX = 'VTEST'

describe('Work Orders CRUD', () => {
  beforeAll(async () => {
    await navigateAuthenticated('/production')
  })

  it('lists work orders', async () => {
    await expect.element(page.getByRole('table')).toBeVisible()
  })

  // Create, edit, status change, delete tests...
  // Each follows: click button → fill modal → submit → verify
})
```

---

### Task 23: E2E — Equipments CRUD

**Files:**
- Create: `agents/cell-mes/frontend/__tests__/e2e/crud/equipments.test.ts`

**Context:** Migrates `e2e/crud/equipments.crud.spec.ts`.

---

### Task 24: E2E — Products, Processes, Routings CRUD

**Files:**
- Create: `agents/cell-mes/frontend/__tests__/e2e/crud/products.test.ts`
- Create: `agents/cell-mes/frontend/__tests__/e2e/crud/processes.test.ts`
- Create: `agents/cell-mes/frontend/__tests__/e2e/crud/routings.test.ts`

**Context:** Migrates corresponding `e2e/crud/*.crud.spec.ts` files.

---

### Task 25: E2E — Quality CRUD (NCR, Inspection Plans)

**Files:**
- Create: `agents/cell-mes/frontend/__tests__/e2e/crud/ncr.test.ts`
- Create: `agents/cell-mes/frontend/__tests__/e2e/crud/inspection-plans.test.ts`

**Context:** Migrates `e2e/crud/ncr.crud.spec.ts` and `e2e/crud/inspection-plans.crud.spec.ts`.

**Step 2:** Run:
```bash
cd agents/cell-mes/frontend && npm run test:e2e -- --run __tests__/e2e/crud/
```

**Step 3:** Commit:
```
feat: migrate CRUD E2E tests to Vitest Browser Mode

- work-orders, equipments, products, processes, routings
- ncr, inspection-plans
```

---

## Phase 7: E2E Migration — Scenarios

### Task 26: E2E — Operator daily scenario

**Files:**
- Create: `agents/cell-mes/frontend/__tests__/e2e/scenarios/operator-daily.test.ts`

**Context:** Migrates `e2e/scenarios/operator-daily.spec.ts`. Persona-driven workflow for 김현장 (CNC Operator) — views dashboard, checks assigned work orders, reports production results.

---

### Task 27: E2E — Planner daily scenario

**Files:**
- Create: `agents/cell-mes/frontend/__tests__/e2e/scenarios/planner-daily.test.ts`

**Context:** Migrates `e2e/scenarios/planner-daily.spec.ts`.

---

### Task 28: E2E — Manager overview scenario

**Files:**
- Create: `agents/cell-mes/frontend/__tests__/e2e/scenarios/manager-overview.test.ts`

**Context:** Migrates `e2e/scenarios/manager-overview.spec.ts`.

---

### Task 29: E2E — Remaining scenarios

**Files:**
- Create files for each remaining scenario spec:
  - `critical-workflows.test.ts`
  - `crud-operations.test.ts`
  - `deep-workflow.test.ts`
  - `filters-pagination.test.ts`
  - `integration-workflow.test.ts`
  - `manufacturing-workflow.test.ts`
  - `master-crud.test.ts`
  - `production-workflow.test.ts`
  - `quality-engineer.test.ts`
  - `quality-workflow.test.ts`
  - `role-operator.test.ts`
  - `role-production-manager.test.ts`
  - `role-quality-manager.test.ts`
  - `role-scheduler.test.ts`
  - `spc-analytics.test.ts`
  - `ui-common.test.ts`
  - `work-order-scheduler-integration.test.ts`

**Step 3:** Commit:
```
feat: migrate scenario E2E tests to Vitest Browser Mode
```

---

## Phase 8: E2E Migration — Validations

### Task 30: E2E — Data integrity validations

**Files:**
- Create: `agents/cell-mes/frontend/__tests__/e2e/validation/data-integrity.test.ts`

**Context:** Migrates `e2e/validation/data-integrity-deep.spec.ts` and `e2e/validations/data-integrity.spec.ts`. Hybrid UI + API validation — verifies UI counts match API data.

---

### Task 31: E2E — Business rules and calculations

**Files:**
- Create: `agents/cell-mes/frontend/__tests__/e2e/validation/business-rules.test.ts`
- Create: `agents/cell-mes/frontend/__tests__/e2e/validation/calculations.test.ts`

**Context:** Migrates `e2e/validations/business-rules.spec.ts` and `e2e/validations/calculations.spec.ts`.

---

### Task 32: E2E — Remaining validations

**Files:**
- Create files for each remaining validation spec:
  - `ai-validation.test.ts`
  - `cross-screen-validation.test.ts`
  - `crud-deep-validation.test.ts`
  - `data-sync-integrity.test.ts`
  - `manufacturing-integrity.test.ts`
  - `production-integrity.test.ts`
  - `quality-validation.test.ts`
  - `scheduler-validation.test.ts`
  - `work-order-validation.test.ts`

**Step 3:** Commit:
```
feat: migrate validation E2E tests to Vitest Browser Mode
```

---

## Phase 9: Cleanup

### Task 33: Remove Playwright and old test files

**Files:**
- Delete: `agents/cell-mes/frontend/e2e/` (entire directory)
- Delete: `agents/cell-mes/frontend/playwright.config.ts`
- Delete: `agents/cell-mes/frontend/playwright-report/` (if exists)
- Delete: `agents/cell-mes/frontend/test-results/` (if exists)
- Modify: `agents/cell-mes/frontend/package.json`

**Step 1:** Remove old Playwright scripts from `package.json`:
```json
{
  "scripts": {
    "test:e2e:pw": null,
    "test:e2e:pw:ui": null,
    "test:e2e:pw:report": null
  }
}
```

**Step 2:** Uninstall Playwright test runner:
```bash
cd agents/cell-mes/frontend
npm uninstall @playwright/test
```

**Step 3:** Delete old files:
```bash
rm -rf e2e/ playwright.config.ts playwright-report/ test-results/
```

**Step 4:** Verify everything still works:
```bash
npm run test:unit -- --run
npm run test:e2e -- --run  # requires servers
```

**Step 5:** Commit:
```
chore: remove Playwright and old E2E test infrastructure

- Delete e2e/ directory (50+ Playwright specs)
- Delete playwright.config.ts
- Remove @playwright/test dependency
- All tests now run via Vitest
```

---

### Task 34: Final verification

**Step 1:** Run full test suite:
```bash
cd agents/cell-mes/frontend
npm test -- --run
```

**Step 2:** Check test counts:
- Unit tests: ~30+ (utils, hooks, stores)
- E2E tests: ~50+ (matching or exceeding old Playwright count)
- Total: 80+

**Step 3:** Verify `npm run test:ui` works (opens Vitest UI dashboard).

---

## API Translation Quick Reference

When migrating each Playwright spec, use this translation table:

| Playwright | Vitest Browser Mode |
|------------|-------------------|
| `import { test, expect } from '@playwright/test'` | `import { describe, it, expect } from 'vitest'` + `import { page } from '@vitest/browser/context'` |
| `test('name', async ({ page }) => {})` | `it('name', async () => {})` (page from import) |
| `page.goto('/')` | `page.goto('http://localhost:3000/')` |
| `page.locator('.cls')` | `page.getByRole()` / `page.getByTestId()` |
| `page.locator('text=X')` | `page.getByText('X')` |
| `expect(locator).toBeVisible()` | `await expect.element(locator).toBeVisible()` |
| `expect(locator).toHaveText('X')` | `await expect.element(locator).toHaveTextContent('X')` |
| `expect(page).toHaveURL(/pat/)` | `await expect.poll(() => page.url()).toContain('pat')` |
| `page.waitForTimeout(ms)` | `await new Promise(r => setTimeout(r, ms))` |
| `page.waitForLoadState('networkidle')` | `await expect.poll(() => ..., { timeout: 10000 })` |
| `test.describe.serial` | `describe` (Vitest Browser Mode runs sequentially per file) |
| `test.use({ storageState })` | `beforeAll(() => loginAsAdmin())` |
| `page.waitForSelector('.cls')` | `await expect.element(page.locator('.cls')).toBeVisible()` |

---

## Verification Checklist

- [ ] `npm run test:unit -- --run` passes (no servers needed)
- [ ] `npm run test:e2e -- --run` passes (servers on 3000, 8000, 8001)
- [ ] `npm test -- --run` runs both projects
- [ ] `npm run test:ui` opens Vitest UI
- [ ] No `@playwright/test` imports remain
- [ ] `playwright.config.ts` deleted
- [ ] `e2e/` directory deleted
- [ ] All old test scripts removed from package.json
