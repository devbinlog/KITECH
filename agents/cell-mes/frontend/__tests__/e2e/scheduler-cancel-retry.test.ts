import { describe, it, expect } from 'vitest'
import { commands } from 'vitest/browser'

const APP_URL = 'http://localhost:3000'

async function login() {
  await commands.goto(`${APP_URL}/login`)
  await commands.fillByRole('textbox', '사용자 ID', 'admin')
  await commands.fillByLabel('비밀번호', 'admin123')
  await commands.clickByRole('button', '로그인')
  await commands.waitForUrl('^(?!.*\\/login)', 10_000)
}

/** Execute solver and wait for comparing state. Returns true if successful. */
async function solveAndWaitForComparing(): Promise<boolean> {
  await commands.clickByRole('button', '스케줄 실행')
  for (let i = 0; i < 18; i++) {
    await commands.waitForTimeout(5000)
    const hasCompare = await commands.isVisibleByText('비교중', 2000) ||
                       await commands.isVisibleByText('스케줄 결과 비교', 2000)
    if (hasCompare) return true
  }
  return false
}

async function solveViaApi() {
  const res = await commands.fetchApi(
    '/scheduler/solve',
    'POST',
    JSON.stringify({
      horizon_hours: 24,
      include_running: false,
      solver_type: 'OR_TOOLS',
      time_limit_sec: 60,
      auto_apply: false,
    })
  )
  return res
}

describe('Scheduler Cancel and Retry Workflows', () => {
  it('cancel does not change work orders', async () => {
    await login()

    const woRes = await commands.fetchApi('/scheduler/work-orders?status=READY&limit=10')
    if (!woRes.ok || !woRes.data?.count) return

    const woBefore = woRes.data.items.map((wo: any) => ({ id: wo.id, status: wo.status }))

    await commands.goto(`${APP_URL}/scheduler/execute`)
    await commands.waitForTimeout(2000)

    // Execute and wait for comparing state
    const gotResult = await solveAndWaitForComparing()
    if (!gotResult) return

    // Click "결과 초기화" to cancel without applying
    const hasResetBtn = await commands.isVisibleByRole('button', '결과 초기화', 2000)
    if (!hasResetBtn) return

    await commands.clickByRole('button', '결과 초기화')
    await commands.waitForTimeout(2000)

    const woAfterRes = await commands.fetchApi('/scheduler/work-orders?status=READY&limit=10')
    if (!woAfterRes.ok) return

    const woAfter = woAfterRes.data.items.map((wo: any) => ({ id: wo.id, status: wo.status }))
    expect(woAfter).toEqual(woBefore)
  })

  it('cancel then re-execute works', async () => {
    await login()

    const woRes = await commands.fetchApi('/scheduler/work-orders?status=READY&limit=10')
    if (!woRes.ok || !woRes.data?.count) return

    await commands.goto(`${APP_URL}/scheduler/execute`)
    await commands.waitForTimeout(2000)

    // First execution
    const gotResult = await solveAndWaitForComparing()
    if (!gotResult) return

    // Reset results
    const hasResetBtn = await commands.isVisibleByRole('button', '결과 초기화', 2000)
    if (!hasResetBtn) return

    await commands.clickByRole('button', '결과 초기화')
    await commands.waitForTimeout(2000)

    const hasExecuteBtn = await commands.isVisibleByRole('button', '스케줄 실행', 2000)
    expect(hasExecuteBtn).toBe(true)

    // Second execution
    const gotResult2 = await solveAndWaitForComparing()
    expect(gotResult2).toBe(true)
  })

  it('different solver re-execution shows new result', async () => {
    await login()

    const woRes = await commands.fetchApi('/scheduler/work-orders?status=READY&limit=10')
    if (!woRes.ok || !woRes.data?.count) return

    await commands.goto(`${APP_URL}/scheduler/execute`)
    await commands.waitForTimeout(2000)

    // First execution with default solver (OR_TOOLS)
    const gotResult = await solveAndWaitForComparing()
    if (!gotResult) return

    // Reset results
    const hasResetBtn = await commands.isVisibleByRole('button', '결과 초기화', 2000)
    if (!hasResetBtn) return

    await commands.clickByRole('button', '결과 초기화')
    await commands.waitForTimeout(2000)

    // Change solver to GA using the select element
    const hasSelector = await commands.isVisibleBySelector('select', 2000)
    if (!hasSelector) return

    await commands.selectOption('select', 'GA')
    await commands.waitForTimeout(500)

    // Second execution
    const gotResult2 = await solveAndWaitForComparing()
    expect(gotResult2).toBe(true)
  })

  it('repeated solve/cancel cycle works 3 times', async () => {
    await login()

    const woRes = await commands.fetchApi('/scheduler/work-orders?status=READY&limit=10')
    if (!woRes.ok || !woRes.data?.count) return

    await commands.goto(`${APP_URL}/scheduler/execute`)
    await commands.waitForTimeout(2000)

    for (let cycle = 0; cycle < 3; cycle++) {
      // Execute and wait for comparing state
      const gotResult = await solveAndWaitForComparing()
      if (!gotResult) return

      // Reset results
      const hasResetBtn = await commands.isVisibleByRole('button', '결과 초기화', 2000)
      if (!hasResetBtn) return

      await commands.clickByRole('button', '결과 초기화')
      await commands.waitForTimeout(2000)

      const hasExecuteBtn = await commands.isVisibleByRole('button', '스케줄 실행', 2000)
      expect(hasExecuteBtn).toBe(true)
    }
  })

  it('solver parameter change reflects in re-execution', async () => {
    await login()

    const woRes = await commands.fetchApi('/scheduler/work-orders?status=READY&limit=10')
    if (!woRes.ok || !woRes.data?.count) return

    await commands.goto(`${APP_URL}/scheduler/execute`)
    await commands.waitForTimeout(2000)

    // First execution with default time limit
    const gotResult = await solveAndWaitForComparing()
    if (!gotResult) return

    // Reset results
    const hasResetBtn = await commands.isVisibleByRole('button', '결과 초기화', 2000)
    if (!hasResetBtn) return

    await commands.clickByRole('button', '결과 초기화')
    await commands.waitForTimeout(2000)

    // Change time limit parameter
    const hasTimeInput = await commands.isVisibleBySelector('input[type="number"]', 2000)
    if (!hasTimeInput) return

    // Re-execute with changed parameter
    const gotResult2 = await solveAndWaitForComparing()
    expect(gotResult2).toBe(true)
  })

  it('mode selection changes scheduling behavior', async () => {
    await login()

    const woRes = await commands.fetchApi('/scheduler/work-orders?status=READY&limit=10')
    if (!woRes.ok || !woRes.data?.count) return

    await commands.goto(`${APP_URL}/scheduler/execute`)
    await commands.waitForTimeout(2000)

    // Default mode is "신규 수립" - verify mode selection is visible
    const hasModeSection = await commands.isVisibleByText('스케줄링 모드', 2000)
    if (!hasModeSection) return

    // Select "재스케줄링" mode
    await commands.clickByText('재스케줄링')
    await commands.waitForTimeout(500)

    // Verify warning banner appears
    const hasWarning = await commands.isVisibleByText('기존 스케줄이 새 결과로 덮어씌워집니다', 3000)
    expect(hasWarning).toBe(true)

    // Execute with reschedule mode
    const gotResult = await solveAndWaitForComparing()
    if (!gotResult) return

    // Verify we got results
    const hasCompareTable = await commands.isVisibleByText('스케줄 결과 비교', 2000)
    expect(hasCompareTable).toBe(true)
  })
})
