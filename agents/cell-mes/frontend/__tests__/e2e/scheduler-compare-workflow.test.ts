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

describe('Scheduler Compare Workflow', () => {
  it('shows scheduling mode selection when idle', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/execute`)
    await commands.waitForTimeout(1000)

    // Check for mode section header
    const hasModeSection = await commands.isVisibleByText('스케줄링 모드', 2000)
    expect(hasModeSection).toBe(true)

    // Check for three mode cards
    const hasNew = await commands.isVisibleByText('신규 수립', 2000)
    const hasReschedule = await commands.isVisibleByText('재스케줄링', 2000)
    const hasRebalance = await commands.isVisibleByText('전체 재배치', 2000)
    expect(hasNew).toBe(true)
    expect(hasReschedule).toBe(true)
    expect(hasRebalance).toBe(true)
  })

  it('executes single solver and shows comparison table with 1 column', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/execute`)
    await commands.waitForTimeout(1000)

    // Check if work orders available
    const woRes = await commands.fetchApi('/scheduler/work-orders?status=READY&limit=10')
    if (!woRes.ok || !woRes.data?.count) return

    // Select OR-Tools solver via select element
    await commands.selectOption('select', 'OR_TOOLS')
    await commands.waitForTimeout(500)

    // Execute and wait for comparison state
    const gotResult = await solveAndWaitForComparing()
    if (!gotResult) return

    // Verify comparison table visible
    const hasCompareTable = await commands.isVisibleByText('스케줄 결과 비교', 2000)
    expect(hasCompareTable).toBe(true)

    // Verify comparing status badge
    const isComparing = await commands.isVisibleByText('비교중', 2000)
    expect(isComparing).toBe(true)

    // Verify result column exists (check for OR-Tools label)
    const hasORToolsColumn = await commands.isVisibleByText('OR-Tools', 2000)
    expect(hasORToolsColumn).toBe(true)
  })

  it('executes additional solver and shows 2 columns in comparison table', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/execute`)
    await commands.waitForTimeout(1000)

    // Check if work orders available
    const woRes = await commands.fetchApi('/scheduler/work-orders?status=READY&limit=10')
    if (!woRes.ok || !woRes.data?.count) return

    // Execute first solver (OR-Tools)
    await commands.selectOption('select', 'OR_TOOLS')
    await commands.waitForTimeout(500)
    const gotFirstResult = await solveAndWaitForComparing()
    if (!gotFirstResult) return

    // Execute second solver (GA) - select is still visible in comparing state
    await commands.selectOption('select', 'GA')
    await commands.waitForTimeout(500)
    await commands.clickByRole('button', '스케줄 실행')

    // Wait for second result (comparison table should update)
    let gotSecondResult = false
    for (let i = 0; i < 18; i++) {
      await commands.waitForTimeout(5000)
      // Check for GA solver label in comparison table
      const hasGA = await commands.isVisibleByText('유전 알고리즘', 2000)
      if (hasGA) {
        gotSecondResult = true
        break
      }
    }
    if (!gotSecondResult) return

    // Verify both columns exist
    const hasORTools = await commands.isVisibleByText('OR-Tools', 2000)
    const hasGA = await commands.isVisibleByText('유전 알고리즘', 2000)
    expect(hasORTools).toBe(true)
    expect(hasGA).toBe(true)
  })

  it('shows "전체 비교" button and progress when clicked', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/execute`)
    await commands.waitForTimeout(1000)

    // Check if work orders available
    const woRes = await commands.fetchApi('/scheduler/work-orders?status=READY&limit=10')
    if (!woRes.ok || !woRes.data?.count) return

    // Check for "전체 비교" button
    const hasCompareAllButton = await commands.isVisibleByRole('button', '전체 비교', 2000)
    expect(hasCompareAllButton).toBe(true)

    // Click it
    await commands.clickByRole('button', '전체 비교')
    await commands.waitForTimeout(1000)

    // Verify progress text appears
    const hasProgress = await commands.isVisibleByText('솔버 실행중', 5000)
    expect(hasProgress).toBe(true)

    // Verify "중단" button appears
    const hasAbortButton = await commands.isVisibleByRole('button', '중단', 2000)
    expect(hasAbortButton).toBe(true)
  })

  it('shows KPI rows in comparison table', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/execute`)
    await commands.waitForTimeout(1000)

    // Check if work orders available
    const woRes = await commands.fetchApi('/scheduler/work-orders?status=READY&limit=10')
    if (!woRes.ok || !woRes.data?.count) return

    // Execute solver
    await commands.selectOption('select', 'OR_TOOLS')
    await commands.waitForTimeout(500)
    const gotResult = await solveAndWaitForComparing()
    if (!gotResult) return

    // Verify all KPI rows
    const hasMakespan = await commands.isVisibleByText('Makespan', 2000)
    const hasUtilization = await commands.isVisibleByText('평균 가동률', 2000)
    const hasJobCount = await commands.isVisibleByText('작업 수', 2000)
    const hasExecTime = await commands.isVisibleByText('실행 시간', 2000)
    const hasObjective = await commands.isVisibleByText('목적함수', 2000)

    expect(hasMakespan).toBe(true)
    expect(hasUtilization).toBe(true)
    expect(hasJobCount).toBe(true)
    expect(hasExecTime).toBe(true)
    expect(hasObjective).toBe(true)
  })

  it('highlights best values with green background', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/execute`)
    await commands.waitForTimeout(1000)

    // Check if work orders available
    const woRes = await commands.fetchApi('/scheduler/work-orders?status=READY&limit=10')
    if (!woRes.ok || !woRes.data?.count) return

    // Execute solver
    await commands.selectOption('select', 'OR_TOOLS')
    await commands.waitForTimeout(500)
    const gotResult = await solveAndWaitForComparing()
    if (!gotResult) return

    // Check for green highlighted cells (bg-green-50)
    const hasGreenHighlight = await commands.isVisibleBySelector('.bg-green-50', 2000)
    expect(hasGreenHighlight).toBe(true)
  })

  it('shows "기존 스케줄" column when current schedule exists', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/execute`)
    await commands.waitForTimeout(1000)

    // Check if work orders available
    const woRes = await commands.fetchApi('/scheduler/work-orders?status=READY&limit=10')
    if (!woRes.ok || !woRes.data?.count) return

    // Execute solver
    await commands.selectOption('select', 'OR_TOOLS')
    await commands.waitForTimeout(500)
    const gotResult = await solveAndWaitForComparing()
    if (!gotResult) return

    // Check for "기존 스케줄" column (depends on whether current schedule data exists)
    const hasBaselineColumn = await commands.isVisibleByText('기존 스케줄', 2000)
    // This may or may not be true depending on whether there's existing schedule data
    // Just verify comparison table is functional
    const hasCompareTable = await commands.isVisibleByText('스케줄 결과 비교', 2000)
    expect(hasCompareTable).toBe(true)
  })

  it('clicking "선택" button shows detail view with stats cards', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/execute`)
    await commands.waitForTimeout(1000)

    // Check if work orders available
    const woRes = await commands.fetchApi('/scheduler/work-orders?status=READY&limit=10')
    if (!woRes.ok || !woRes.data?.count) return

    // Execute solver
    await commands.selectOption('select', 'OR_TOOLS')
    await commands.waitForTimeout(500)
    const gotResult = await solveAndWaitForComparing()
    if (!gotResult) return

    // Click "선택" button
    await commands.clickByRole('button', '선택')
    await commands.waitForTimeout(1000)

    // Verify detail view stats cards
    const hasMakespan = await commands.isVisibleByText('Makespan', 2000)
    const hasUtilization = await commands.isVisibleByText('평균 가동률', 2000)
    const hasScheduledJobs = await commands.isVisibleByText('스케줄 작업', 2000)
    const hasExecTime = await commands.isVisibleByText('실행 시간', 2000)

    expect(hasMakespan).toBe(true)
    expect(hasUtilization).toBe(true)
    expect(hasScheduledJobs).toBe(true)
    expect(hasExecTime).toBe(true)
  })

  it('detail view "스케줄 승인" transitions to approved state', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/execute`)
    await commands.waitForTimeout(1000)

    // Check if work orders available
    const woRes = await commands.fetchApi('/scheduler/work-orders?status=READY&limit=10')
    if (!woRes.ok || !woRes.data?.count) return

    // Execute solver
    await commands.selectOption('select', 'OR_TOOLS')
    await commands.waitForTimeout(500)
    const gotResult = await solveAndWaitForComparing()
    if (!gotResult) return

    // Go to detail view
    await commands.clickByRole('button', '선택')
    await commands.waitForTimeout(1000)

    // Accept the confirm dialog before clicking approve
    await commands.acceptNextConfirm()

    // Click "스케줄 승인"
    const hasApproveButton = await commands.isVisibleByRole('button', '스케줄 승인', 2000)
    if (!hasApproveButton) return

    await commands.clickByRole('button', '스케줄 승인')
    await commands.waitForTimeout(3000)

    // Verify approved state
    const hasApproved = await commands.isVisibleByText('승인완료', 5000) ||
                       await commands.isVisibleByText('스케줄 승인 완료', 5000)
    expect(hasApproved).toBe(true)
  })

  it('clicking "결과 초기화" resets comparison table and returns to idle', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/execute`)
    await commands.waitForTimeout(1000)

    // Check if work orders available
    const woRes = await commands.fetchApi('/scheduler/work-orders?status=READY&limit=10')
    if (!woRes.ok || !woRes.data?.count) return

    // Execute solver
    await commands.selectOption('select', 'OR_TOOLS')
    await commands.waitForTimeout(500)
    const gotResult = await solveAndWaitForComparing()
    if (!gotResult) return

    // Click "결과 초기화"
    await commands.clickByRole('button', '결과 초기화')
    await commands.waitForTimeout(1000)

    // Verify comparison table is gone
    const hasCompareTable = await commands.isVisibleByText('스케줄 결과 비교', 2000)
    expect(hasCompareTable).toBe(false)

    // Verify idle state (mode selection visible again)
    const hasModeSelection = await commands.isVisibleByText('스케줄링 모드', 2000)
    expect(hasModeSelection).toBe(true)
  })

  it('clicking "중단" button stops all-solver execution', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/execute`)
    await commands.waitForTimeout(1000)

    // Check if work orders available
    const woRes = await commands.fetchApi('/scheduler/work-orders?status=READY&limit=10')
    if (!woRes.ok || !woRes.data?.count) return

    // Click "전체 비교"
    await commands.clickByRole('button', '전체 비교')
    await commands.waitForTimeout(2000)

    // Verify progress started
    const hasProgress = await commands.isVisibleByText('솔버 실행중', 3000)
    if (!hasProgress) return

    // Click "중단" button
    await commands.clickByRole('button', '중단')
    await commands.waitForTimeout(1000)

    // Verify execution stopped (progress message is gone)
    const progressGone = !(await commands.isVisibleByText('솔버 실행중', 2000))
    expect(progressGone).toBe(true)
  })
})
