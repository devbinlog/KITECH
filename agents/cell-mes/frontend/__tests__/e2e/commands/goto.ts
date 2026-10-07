import type { BrowserCommand } from 'vitest/node'

/**
 * App page management.
 * Instead of navigating the Vitest iframe (which breaks the orchestrator),
 * we open a SEPARATE browser tab for the app and interact through it.
 */

// Store the app page reference across commands
let appPage: any = null

async function getOrCreateAppPage(ctx: any): Promise<any> {
  if (appPage && !appPage.isClosed()) {
    return appPage
  }
  // Create a new page (tab) in the same browser context
  appPage = await ctx.context.newPage()
  return appPage
}

/**
 * Navigate to a URL in a separate browser tab (not the Vitest iframe).
 */
export const goto: BrowserCommand<[string]> = async (ctx, url: string) => {
  const page = await getOrCreateAppPage(ctx)
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30_000 })
  // Brief settle time for client-side rendering
  await page.waitForTimeout(1000)
}

/**
 * Get the current URL of the app page.
 */
export const currentUrl: BrowserCommand<[]> = async (ctx) => {
  const page = await getOrCreateAppPage(ctx)
  return page.url()
}

/**
 * Fill a form field by role and name pattern.
 */
export const fillByRole: BrowserCommand<[string, string, string]> = async (
  ctx,
  role: string,
  namePattern: string,
  value: string,
) => {
  const page = await getOrCreateAppPage(ctx)
  const locator = page.getByRole(role as any, { name: new RegExp(namePattern, 'i') })
  await locator.fill(value)
}

/**
 * Fill a form field by label text.
 */
export const fillByLabel: BrowserCommand<[string, string]> = async (
  ctx,
  labelPattern: string,
  value: string,
) => {
  const page = await getOrCreateAppPage(ctx)
  const locator = page.getByLabel(new RegExp(labelPattern, 'i'))
  await locator.fill(value)
}

/**
 * Click an element by role and name pattern.
 */
export const clickByRole: BrowserCommand<[string, string]> = async (
  ctx,
  role: string,
  namePattern: string,
) => {
  const page = await getOrCreateAppPage(ctx)
  const locator = page.getByRole(role as any, { name: new RegExp(namePattern, 'i') })
  await locator.click()
}

/**
 * Check if an element with given role and name is visible.
 */
export const isVisibleByRole: BrowserCommand<[string, string]> = async (
  ctx,
  role: string,
  namePattern: string,
) => {
  const page = await getOrCreateAppPage(ctx)
  const locator = page.getByRole(role as any, { name: new RegExp(namePattern, 'i') })
  try {
    await locator.waitFor({ state: 'visible', timeout: 5_000 })
    return true
  } catch {
    return false
  }
}

/**
 * Wait for the app page URL to match a pattern.
 */
export const waitForUrl: BrowserCommand<[string, number]> = async (
  ctx,
  urlSubstring: string,
  timeout: number = 10_000,
) => {
  const page = await getOrCreateAppPage(ctx)
  const deadline = Date.now() + timeout
  while (Date.now() < deadline) {
    const url = page.url()
    if (new RegExp(urlSubstring).test(url)) {
      return url
    }
    await new Promise((r) => setTimeout(r, 250))
  }
  return page.url()
}

/**
 * Check if text matching a pattern is visible.
 */
export const isVisibleByText: BrowserCommand<[string, number]> = async (
  ctx,
  textPattern: string,
  timeout: number = 5_000,
) => {
  const page = await getOrCreateAppPage(ctx)
  try {
    const locator = page.getByText(new RegExp(textPattern, 'i'))
    await locator.first().waitFor({ state: 'visible', timeout })
    return true
  } catch {
    return false
  }
}

/**
 * Click an element by text content.
 */
export const clickByText: BrowserCommand<[string]> = async (
  ctx,
  textPattern: string,
) => {
  const page = await getOrCreateAppPage(ctx)
  const locator = page.getByText(new RegExp(textPattern, 'i'))
  await locator.first().click()
}

/**
 * Wait for a specified duration.
 */
export const waitForTimeout: BrowserCommand<[number]> = async (
  _ctx,
  ms: number,
) => {
  await new Promise((r) => setTimeout(r, ms))
}

/**
 * Check if an element matching a CSS selector is visible.
 */
export const isVisibleBySelector: BrowserCommand<[string, number]> = async (
  ctx,
  selector: string,
  timeout: number = 5_000,
) => {
  const page = await getOrCreateAppPage(ctx)
  try {
    const locator = page.locator(selector)
    await locator.first().waitFor({ state: 'visible', timeout })
    return true
  } catch {
    return false
  }
}

/**
 * Make an API call from the server side (Node.js context).
 * This bypasses browser sandbox restrictions that prevent fetch() from
 * the Vitest iframe to localhost:8000.
 */
let cachedToken: string | null = null

async function getApiToken(): Promise<string> {
  if (cachedToken) return cachedToken
  const res = await fetch('http://localhost:8000/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: 'username=admin&password=admin123',
  })
  const data = (await res.json()) as any
  cachedToken = data.access_token as string
  return cachedToken
}

export const fetchApi: BrowserCommand<[string, string?, string?]> = async (
  _ctx,
  path: string,
  method: string = 'GET',
  body?: string,
) => {
  const token = await getApiToken()
  const options: RequestInit = {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  }
  if (body) {
    options.body = body
  }
  try {
    const res = await fetch(`http://localhost:8000/api/v1${path}`, options)
    const responseData = await res.json().catch(() => null)
    return { ok: res.ok, status: res.status, data: responseData }
  } catch {
    return { ok: false, status: 0, data: null }
  }
}

/**
 * Make an HTTP request to an arbitrary URL from the server side (Node.js context).
 * Unlike fetchApi which is scoped to localhost:8000/api/v1, this accepts a full URL.
 * No auth token is attached -- callers can include their own headers via the body/method params.
 */
export const fetchExternal: BrowserCommand<[string, string?, string?]> = async (
  _ctx,
  url: string,
  method: string = 'GET',
  body?: string,
) => {
  const options: RequestInit = {
    method,
    headers: { 'Content-Type': 'application/json' },
  }
  if (body) {
    options.body = body
  }
  try {
    const res = await fetch(url, options)
    const responseData = await res.json().catch(() => null)
    return { ok: res.ok, status: res.status, data: responseData }
  } catch {
    return { ok: false, status: 0, data: null }
  }
}

/**
 * Close the app page (cleanup between test files).
 */
export const closeAppPage: BrowserCommand<[]> = async (_ctx) => {
  if (appPage && !appPage.isClosed()) {
    await appPage.close()
    appPage = null
  }
}

/**
 * Accept the next browser confirm/alert dialog.
 * Must be called BEFORE the action that triggers the dialog.
 */
export const acceptNextConfirm: BrowserCommand<[]> = async (ctx) => {
  const page = await getOrCreateAppPage(ctx)
  page.once('dialog', (dialog: any) => dialog.accept())
}

/**
 * Select an option in a <select> element by CSS selector.
 * @param selector - CSS selector for the <select> element
 * @param value - The option value attribute to select
 */
export const selectOption: BrowserCommand<[string, string]> = async (
  ctx,
  selector: string,
  value: string,
) => {
  const page = await getOrCreateAppPage(ctx)
  const locator = page.locator(selector).first()
  await locator.selectOption(value)
}

/**
 * Click an element by CSS selector. Clicks the first match.
 * @param selector - CSS selector for the element
 */
export const clickBySelector: BrowserCommand<[string]> = async (
  ctx,
  selector: string,
) => {
  const page = await getOrCreateAppPage(ctx)
  const locator = page.locator(selector).first()
  await locator.click()
}

/**
 * Fill an input by CSS selector. Works for inputs without proper label association.
 * @param selector - CSS selector for the input element
 * @param value - The value to fill
 */
export const fillBySelector: BrowserCommand<[string, string]> = async (
  ctx,
  selector: string,
  value: string,
) => {
  const page = await getOrCreateAppPage(ctx)
  const locator = page.locator(selector).first()
  await locator.fill(value)
}

/**
 * Evaluate JavaScript in the app page context and return the result.
 * @param expression - JS expression to evaluate (will be wrapped in a function)
 */
export const evaluateInPage: BrowserCommand<[string]> = async (
  ctx,
  expression: string,
) => {
  const page = await getOrCreateAppPage(ctx)
  return await page.evaluate(expression)
}
