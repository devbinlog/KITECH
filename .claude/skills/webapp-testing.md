---
name: webapp-testing
description: Toolkit for interacting with and testing local web applications using Playwright. Supports verifying frontend functionality, debugging UI behavior, capturing browser screenshots, and viewing browser logs.
---

# Web Application Testing

Playwright 기반 웹 애플리케이션 E2E 테스트 가이드.
Python(`sync_playwright`) 또는 TypeScript(`@playwright/test`) 모두 지원.

## Decision Tree: Choosing Your Approach

```
User task -> Is it static HTML?
    +- Yes -> Read HTML file directly to identify selectors
    |         +- Success -> Write Playwright script using selectors
    |         +- Fails/Incomplete -> Treat as dynamic (below)
    |
    +- No (dynamic webapp) -> Is the server already running?
        +- No -> Start server first, then write Playwright script
        |
        +- Yes -> Reconnaissance-then-action:
            1. Navigate and wait for page to load
            2. Take screenshot or inspect DOM
            3. Identify selectors from rendered state
            4. Execute actions with discovered selectors
```

## TypeScript Playwright (Recommended for Next.js / React)

### Test Structure

```typescript
import { test, expect } from '@playwright/test';
// or from custom fixture:
// import { test, expect } from './fixtures/auth';

test.describe('Feature Name', () => {
  test('specific behavior', async ({ page }) => {
    await page.goto('/path');
    await expect(page.locator('h1:has-text("Title")')).toBeVisible({ timeout: 15000 });
    await page.locator('button:has-text("Action")').click();
    await expect(page.locator('.success')).toBeVisible();
  });
});
```

### Auth Fixture Pattern

로그인이 필요한 앱은 커스텀 fixture로 인증을 자동화한다:

```typescript
// e2e/fixtures/auth.ts
import { test as base, expect } from '@playwright/test';

export const test = base.extend({
  page: async ({ page }, use) => {
    await page.goto('/login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await expect(page.locator('h1:has-text("Dashboard")')).toBeVisible({ timeout: 15000 });
    await use(page);
  },
});

export { expect };
```

## Python Playwright (Quick Scripts)

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('http://localhost:3000')
    page.wait_for_load_state('networkidle')
    page.screenshot(path='/tmp/inspect.png', full_page=True)
    page.click('button:has-text("Submit")')
    assert page.locator('.success-message').is_visible()
    browser.close()
```

---

## Lessons Learned: Common Failure Patterns & Fixes

### 1. Modal Overlay Intercepting Clicks

**Problem**: 모달(`.fixed.inset-0`)의 반투명 배경이 뒤쪽 요소 클릭을 차단한다.
`button:has-text("Action")` 클릭 시 timeout 에러 발생.

**Error**:
```
locator.click: Timeout 30000ms exceeded.
<form class="p-4 space-y-4">...</form> from
<div class="fixed inset-0 bg-black/50...">...</div>
subtree intercepts pointer events
```

**Fix**: 모달 내 버튼은 `button[type="submit"]`으로 정확히 타겟. 모달이 닫히지 않으면 fallback으로 취소:

```typescript
// 모달 내 생성/저장 버튼 클릭
await modal.locator('button[type="submit"]').click({ timeout: 5000 });

// 모달 닫힘 대기 (성공 시 자동 닫힘, API 실패 시 수동 닫기)
const modalClosed = await modal
  .waitFor({ state: 'hidden', timeout: 5000 })
  .then(() => true)
  .catch(() => false);

if (!modalClosed) {
  const cancelBtn = modal.locator('button:has-text("Cancel")');
  if (await cancelBtn.isVisible({ timeout: 1000 }).catch(() => false)) {
    await cancelBtn.click();
  }
  await modal.waitFor({ state: 'hidden', timeout: 5000 }).catch(() => {});
}
```

**Key Rule**: 모달이 열린 상태에서 모달 외부 요소 클릭하면 반드시 실패한다. 모달을 먼저 닫아야 한다.

### 2. Async Loading State Handling

**Problem**: API 응답이 느리거나 실패하면 "로딩 중..." 상태가 영원히 유지된다.
`expect(page.locator('text=KPI Value')).toBeVisible()` → timeout.

**Fix**: 데이터 로딩 OR 로딩 상태 중 하나가 보이면 통과하는 유연한 assertion:

```typescript
// 방법 1: 실제 데이터 OR 로딩 상태 허용
const hasData = await page.locator('text=Target KPI')
  .first().isVisible({ timeout: 10000 }).catch(() => false);
const hasLoading = await page.locator('text=Loading')
  .first().isVisible().catch(() => false);
expect(hasData || hasLoading).toBeTruthy();

// 방법 2: .or() 체이닝 (여러 가능한 상태)
await expect(
  page.locator('table')
    .or(page.locator('text=No data'))
    .or(page.locator('text=Loading'))
).toBeVisible({ timeout: 10000 });
```

**Important**: `.or()` 사용 시 여러 요소가 매칭되면 strict mode 에러 발생. `.first()` 붙여야 한다.

**Best Practice**: 백엔드 API가 확실히 동작하면 데이터를 직접 검증하는 것이 좋다. 로딩 상태 허용은 외부 서비스 의존적인 경우에만 사용.

### 3. Browser Dialog (confirm/alert) Handling

**Problem**: `window.confirm()` 다이얼로그가 뜨면 Playwright가 자동으로 dismiss하여 삭제 등이 취소된다.

**Fix**: 클릭 **전에** dialog 핸들러를 등록한다:

```typescript
// 반드시 클릭 전에 등록!
page.once('dialog', dialog => dialog.accept());

// 그 다음 삭제 버튼 클릭
await page.locator('button:has-text("Delete")').click();
await page.waitForTimeout(2000);
```

**Key Rule**: `page.once('dialog', ...)` 는 반드시 dialog를 트리거하는 클릭 **전에** 등록해야 한다.

### 4. CRUD Test Pattern (Create -> Verify -> Cleanup)

**Problem**: 테스트 데이터가 쌓이면 다음 테스트 실행에 영향을 준다.

**Fix**: 생성한 데이터는 반드시 삭제하는 패턴:

```typescript
test('Product CRUD: Create -> Verify -> Delete', async ({ page }) => {
  await page.goto('/master/products');

  // 1. Create
  const timestamp = Date.now();
  const uniqueCode = `TEST-${timestamp}`;  // 유니크한 식별자
  await page.locator('button:has-text("Add")').click();
  const modal = page.locator('.fixed.inset-0').first();
  await modal.locator('input').first().fill(uniqueCode);
  await modal.locator('button:has-text("Save")').click();
  await page.waitForTimeout(2000);

  // 2. Verify
  await expect(page.locator(`text=${uniqueCode}`)).toBeVisible({ timeout: 10000 });

  // 3. Delete (with dialog handler)
  page.once('dialog', dialog => dialog.accept());
  const row = page.locator(`tr:has-text("${uniqueCode}")`);
  await row.locator('button').last().click();
  await page.waitForTimeout(2000);

  // 4. Verify deletion
  await expect(page.locator(`text=${uniqueCode}`)).not.toBeVisible({ timeout: 10000 });
});
```

### 5. Select/Dropdown Handling

**Problem**: `<select>` 의 첫 번째 option은 보통 placeholder("선택하세요"). `selectOption({index: 0})`하면 빈 값이 된다.

**Fix**:

```typescript
const productSelect = modal.locator('select').first();
const options = await productSelect.locator('option').all();
if (options.length > 1) {
  await productSelect.selectOption({ index: 1 }); // 0은 placeholder
}
```

### 6. Form Field Discovery Pattern

모달 내 폼 필드를 타입별로 찾는 패턴:

```typescript
const modal = page.locator('.fixed.inset-0').first();

// 텍스트 입력
const textInputs = modal.locator('input[type="text"]');
await textInputs.first().fill('value');

// 숫자 입력
const numberInputs = modal.locator('input[type="number"]');
await numberInputs.first().fill('100');

// 날짜 입력
const dateInput = modal.locator('input[type="datetime-local"], input[type="date"]');
if (await dateInput.isVisible({ timeout: 1000 }).catch(() => false)) {
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  await dateInput.fill(tomorrow.toISOString().slice(0, 16));
}

// Select 드롭다운
const selects = modal.locator('select');
const selectCount = await selects.count();
for (let i = 0; i < selectCount; i++) {
  const opts = await selects.nth(i).locator('option').all();
  if (opts.length > 1) {
    await selects.nth(i).selectOption({ index: 1 });
  }
}

// Textarea
const textareas = modal.locator('textarea');
if (await textareas.first().isVisible({ timeout: 2000 }).catch(() => false)) {
  await textareas.first().fill('Description text');
}
```

### 7. Frontend-Backend API Path Mismatch & baseURL 중복

**Problem 1**: 프론트엔드 서비스가 호출하는 API 경로와 백엔드 라우터 경로가 불일치하면 영원히 로딩 상태.

**Problem 2 (baseURL 경로 중복)**: `.env`의 `NEXT_PUBLIC_API_URL`에 path prefix(`/api/v1`)가 포함되어 있고, 서비스 코드에서도 `/api/v1/...`로 호출하면 실제 요청 URL이 `http://host/api/v1/api/v1/...`로 중복되어 404 발생. **로그인부터 모든 API가 실패**하므로 프론트엔드 전체가 동작하지 않는다.

**Prevention**: axios interceptor에서 baseURL path와 요청 경로의 중복 prefix를 자동 감지/제거:

```typescript
// lib/axios.ts
function deduplicatePathPrefix(baseURL: string | undefined, url: string | undefined) {
  if (!baseURL || !url) return url;
  try {
    const { pathname } = new URL(baseURL);
    if (pathname !== "/" && url.startsWith(pathname)) {
      return url.slice(pathname.length) || "/";
    }
  } catch {}
  return url;
}

api.interceptors.request.use((config) => {
  config.url = deduplicatePathPrefix(config.baseURL, config.url);
  return config;
});
```

**Convention**: `NEXT_PUBLIC_API_URL`에는 origin만 (`http://localhost:8000`), 서비스 코드에서 `/api/v1/...` full path 사용.

**Debugging**:
1. 프론트엔드 서비스 파일에서 API 호출 경로 확인
2. 백엔드 라우터에서 실제 등록된 경로 확인
3. `curl`로 직접 API 호출하여 404/200 확인:
   ```bash
   curl -s http://localhost:8000/api/v1/analytics/kpi/summary \
     -H "Authorization: Bearer $TOKEN" | head -c 200
   ```
4. 경로가 다르면 백엔드에 프론트엔드가 기대하는 경로의 엔드포인트를 추가

### 8. Conditional Feature Testing

외부 서비스(스케줄러, AI 등)에 의존하는 기능은 `test.skip`으로 조건부 실행:

```typescript
test('Scheduler execution', async ({ page }) => {
  await page.goto('/scheduler/execute');

  // 외부 서비스 연결 여부 확인
  const isConnected = await page.locator('text=Connected')
    .isVisible({ timeout: 5000 }).catch(() => false);

  test.skip(!isConnected, 'Scheduler service not available');

  // 실제 테스트 로직
  await page.locator('button:has-text("스케줄 실행")').click();
});
```

### 9. Hierarchical Menu Testing

계층 메뉴(Sidebar)에서 하위 항목 접근 테스트:

```typescript
test('사이드바 그룹 메뉴 접근', async ({ page }) => {
  await page.goto('/');

  // 그룹 클릭 시 하위 메뉴 펼침
  const group = page.locator('button:has-text("스케줄러")');
  await group.click();

  // 하위 메뉴 표시 확인
  await expect(page.locator('a:has-text("스케줄 현황")')).toBeVisible();
  await expect(page.locator('a:has-text("스케줄 실행")')).toBeVisible();

  // 하위 메뉴 클릭으로 페이지 이동
  await page.locator('a:has-text("스케줄 실행")').click();
  await expect(page).toHaveURL('/scheduler/execute');
});
```

**Route Map (메뉴 개편 후):**
- `/scheduler` — 스케줄 현황 (간트 차트)
- `/scheduler/execute` — 스케줄 실행/승인 워크플로우
- `/scheduler/settings` — 솔버 설정

---

## Selector Best Practices

```typescript
// By text (가장 간단하지만 언어 의존적)
page.locator('text=Submit')
page.locator('button:has-text("Submit")')

// By heading (h1-h6 필터링)
page.locator('h1:has-text("Dashboard")')
page.locator('h1, h2').filter({ hasText: /Pattern|Regex/ }).first()

// By role
page.locator('[role="dialog"]')

// By CSS class
page.locator('.fixed.inset-0')  // 모달 오버레이
page.locator('[class*="cursor-pointer"]')  // 부분 매칭

// By type attribute
page.locator('button[type="submit"]')
page.locator('input[type="number"]')

// By test ID (recommended for new projects)
page.locator('[data-testid="submit-btn"]')

// Row 기반 탐색
page.locator(`tr:has-text("${uniqueId}")`).locator('button').last()
```

## Assertions

```typescript
// Visibility with timeout
await expect(page.locator('h1')).toBeVisible({ timeout: 15000 });

// Text content
await expect(page.locator('h1')).toHaveText('Welcome');

// Not visible (deletion 확인 등)
await expect(page.locator(`text=${deletedItem}`)).not.toBeVisible({ timeout: 10000 });

// Count
await expect(page.locator('li')).toHaveCount(5);
expect(await items.count()).toBeGreaterThanOrEqual(1);

// URL
await expect(page).toHaveURL('/dashboard');

// Body text length (빈 페이지 감지)
const bodyText = await page.locator('body').textContent();
expect(bodyText?.length).toBeGreaterThan(10);
```

## Timeout Guidelines

| Context | Recommended Timeout |
|---|---|
| Page navigation + hydration | 15000ms |
| API-dependent data loading | 10000ms |
| Modal/dialog appearance | 5000ms |
| Button/element visibility | 3000ms |
| Optional element check | 1000-2000ms |

## Common Pitfalls

1. **`.or()` strict mode**: `.or()` 결과가 여러 요소면 에러. `.first()` 필수
2. **`networkidle` 과의존**: SPA에서는 웹소켓/polling으로 인해 networkidle이 안 올 수 있음. `toBeVisible` timeout이 더 안정적
3. **모달 뒤 클릭 시도**: 모달이 열린 상태에서 외부 요소 클릭 -> pointer intercept 에러
4. **Dialog 핸들러 타이밍**: `page.once('dialog', ...)` 는 트리거 클릭 **전에** 등록
5. **Select placeholder**: `selectOption({index: 0})` 은 보통 "선택하세요" placeholder
6. **Timestamp 기반 uniqueness**: CRUD 테스트에서 `Date.now()` 활용하여 테스트간 충돌 방지
7. **API 경로 불일치**: 프론트엔드가 호출하는 경로와 백엔드 라우터 경로가 다르면 영원히 로딩 상태
8. **baseURL + 서비스 경로 중복**: `.env`에 `API_URL=http://host/api/v1`, 서비스에 `/api/v1/...` → 실제 요청 `http://host/api/v1/api/v1/...` (404). interceptor로 중복 자동 제거 필수
9. **undefined 컴포넌트 렌더링**: `const Icon = iconMap[status]` 에서 status가 맵에 없으면 `<Icon/>`이 undefined → React 런타임 에러. fallback 필수: `iconMap[status] || DefaultIcon`
10. **SQLite BIGINT 자동증가 실패**: SQLAlchemy `BigInteger` → SQLite `BIGINT`는 자동증가 안됨. `INSERT` 시 `NOT NULL constraint failed: table.id` 에러 발생. SQLite는 `INTEGER PRIMARY KEY`만 `ROWID` alias로 자동증가 지원. **Fix**: `BigInteger` 대신 `Integer` 사용:
    ```python
    # ❌ SQLite에서 자동증가 안됨
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # ✅ SQLite에서 자동증가 됨
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ```
    **DB 마이그레이션**: 기존 BIGINT 테이블은 재생성 필요 (`CREATE TABLE new ... AS SELECT * FROM old`, `DROP old`, `ALTER TABLE new RENAME TO old`)
11. **스케줄러 점유구간(occupied slots) 미반영**: 기존 생산실적이 점유 중인 시간대를 스케줄러에 전달하지 않으면, 새 스케줄이 기존 작업과 겹친다. Gantt 차트에서 동일 설비에 Work Order가 겹쳐 보이는 버그 발생. **Fix**: MES에서 `ProdResult`의 `start_time`/`end_time`을 조회하여 `occupied_slots`로 변환 후 스케줄러에 전달. 모든 솔버(OR-Tools, GA, SA, Tabu, ALNS)가 점유구간을 회피하도록 구현 필요
12. **Async SQLAlchemy MissingGreenlet (lazy loading)**: `response_model`에 relationship 필드(예: `product: Optional[ProductEmbedded]`)가 있을 때, 쿼리 시 `selectinload()`를 안 쓰면 FastAPI가 응답 직렬화 시 lazy loading을 시도하여 `MissingGreenlet` → 500 에러. 프론트엔드에서는 `ERR_NETWORK`로 보임. **Fix**: `WorkOrderRead`처럼 relationship을 포함하는 response_model을 쓸 때는 반드시 `selectinload()`로 eager load:
    ```python
    # ❌ 500 Internal Server Error (MissingGreenlet)
    await db.refresh(work_order)
    return work_order  # work_order.product 접근 시 lazy load 시도 → 에러

    # ✅ selectinload로 미리 로드
    result = await db.execute(
        select(WorkOrder).where(WorkOrder.id == work_order.id)
        .options(selectinload(WorkOrder.product))
    )
    return result.scalar_one()
    ```
