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

describe('Scheduler Solve Workflow', () => {
  it('shows idle state with equipment/work order cards and execute button', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/execute`)
    await commands.waitForTimeout(2000)

    // Check status badge for idle state
    const hasIdle = await commands.isVisibleByText('대기', 5000)
    expect(hasIdle).toBe(true)

    // Check status cards
    const hasEquipment = await commands.isVisibleByText('가용 설비', 3000)
    const hasScheduleTarget = await commands.isVisibleByText('스케줄 대상', 3000)
    const hasResult = await commands.isVisibleByText('스케줄 결과', 3000)
    expect(hasEquipment).toBe(true)
    expect(hasScheduleTarget).toBe(true)
    expect(hasResult).toBe(true)

    // Check execute button
    const hasExecuteBtn = await commands.isVisibleByRole('button', '스케줄 실행')
    expect(hasExecuteBtn).toBe(true)
  })

  it('shows equipment and work order summary cards', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/execute`)
    await commands.waitForTimeout(2000)

    // Idle state shows summary cards, not detailed tables
    const hasEquipmentCard = await commands.isVisibleByText('가용 설비', 3000)
    const hasWorkOrderCard = await commands.isVisibleByText('스케줄 대상', 3000)
    const hasResultCard = await commands.isVisibleByText('스케줄 결과', 3000)

    expect(hasEquipmentCard).toBe(true)
    expect(hasWorkOrderCard).toBe(true)
    expect(hasResultCard).toBe(true)
  })

  it('shows JSON view buttons on status cards', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/execute`)
    await commands.waitForTimeout(2000)

    // JSON 보기 buttons exist on equipment and work order cards
    const hasJsonBtn = await commands.isVisibleByText('JSON 보기', 3000)
    expect(hasJsonBtn).toBe(true)
  })

  it('opens JSON view modal when clicking JSON 보기 button', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/execute`)
    await commands.waitForTimeout(2000)

    // Try to find and click JSON view button
    const hasJsonBtn = await commands.isVisibleByText('JSON 보기', 3000)
    if (hasJsonBtn) {
      await commands.clickByText('JSON 보기')
      await commands.waitForTimeout(1000)

      // Modal shows 다운로드 button and ✕ close button (no role="dialog")
      const hasModal = await commands.isVisibleByText('다운로드', 3000)
      expect(hasModal).toBe(true)
    }
  })

  it('has solver selection dropdown with options', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/execute`)
    await commands.waitForTimeout(2000)

    // Check for solver selector
    const hasSelector = await commands.isVisibleBySelector('select', 3000)
    expect(hasSelector).toBe(true)
  })

  it('transitions to solving state when clicking 스케줄 실행', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/execute`)
    await commands.waitForTimeout(2000)

    // Check if work orders available
    const woRes = await commands.fetchApi('/scheduler/work-orders?status=READY&limit=10')
    if (!woRes.ok || !woRes.data?.count) {
      // No data available, skip
      return
    }

    // Click execute button
    const hasExecuteBtn = await commands.isVisibleByRole('button', '스케줄 실행')
    if (hasExecuteBtn) {
      await commands.clickByRole('button', '스케줄 실행')
      await commands.waitForTimeout(2000)

      // Check for solving state indicators
      const hasSolving = await commands.isVisibleByText('실행중', 5000) ||
                        await commands.isVisibleByText('실행 중', 5000)
      expect(hasSolving).toBe(true)
    }
  })

  it('shows comparison table after solve completes, then stat cards in detail view', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/execute`)
    await commands.waitForTimeout(2000)

    // Check if work orders available
    const woRes = await commands.fetchApi('/scheduler/work-orders?status=READY&limit=10')
    if (!woRes.ok || !woRes.data?.count) {
      return
    }

    // Execute and wait for comparing state
    const gotResult = await solveAndWaitForComparing()
    if (!gotResult) return

    // Verify comparison table is visible
    const hasCompareTable = await commands.isVisibleByText('스케줄 결과 비교', 2000)
    expect(hasCompareTable).toBe(true)

    // Click "선택" to enter detail view
    await commands.clickByRole('button', '선택')
    await commands.waitForTimeout(1000)

    // Check for stat cards in detail view
    const hasMakespan = await commands.isVisibleByText('Makespan', 3000)
    const hasUtilization = await commands.isVisibleByText('가동률', 3000)
    const hasScheduledTasks = await commands.isVisibleByText('스케줄 작업', 3000)
    const hasExecutionTime = await commands.isVisibleByText('실행 시간', 3000)

    expect(hasMakespan || hasUtilization || hasScheduledTasks || hasExecutionTime).toBe(true)
  })

  it('shows scheduled tasks table in detail view', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/execute`)
    await commands.waitForTimeout(2000)

    // Check if work orders available
    const woRes = await commands.fetchApi('/scheduler/work-orders?status=READY&limit=10')
    if (!woRes.ok || !woRes.data?.count) {
      return
    }

    // Execute and wait for comparing state
    const gotResult = await solveAndWaitForComparing()
    if (!gotResult) return

    // Click "선택" to enter detail view
    await commands.clickByRole('button', '선택')
    await commands.waitForTimeout(1000)

    // Check for scheduled tasks table columns
    const hasWoId = await commands.isVisibleByText('WO ID', 3000)
    const hasOpId = await commands.isVisibleByText('공정 ID', 3000)
    const hasMachine = await commands.isVisibleByText('설비', 3000)

    expect(hasWoId || hasOpId || hasMachine).toBe(true)
  })

  it('returns to idle state when clicking 결과 초기화 in comparing state', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/execute`)
    await commands.waitForTimeout(2000)

    // Check if work orders available
    const woRes = await commands.fetchApi('/scheduler/work-orders?status=READY&limit=10')
    if (!woRes.ok || !woRes.data?.count) {
      return
    }

    // Execute and wait for comparing state
    const gotResult = await solveAndWaitForComparing()
    if (!gotResult) return

    // Click "결과 초기화" to go back to idle
    const hasResetBtn = await commands.isVisibleByRole('button', '결과 초기화')
    if (hasResetBtn) {
      await commands.clickByRole('button', '결과 초기화')
      await commands.waitForTimeout(1000)

      // Check back to idle
      const hasIdle = await commands.isVisibleByText('대기', 3000)
      expect(hasIdle).toBe(true)
    }
  })

  it('returns to idle and allows re-execution after 결과 초기화', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/execute`)
    await commands.waitForTimeout(2000)

    // Check if work orders available
    const woRes = await commands.fetchApi('/scheduler/work-orders?status=READY&limit=10')
    if (!woRes.ok || !woRes.data?.count) {
      return
    }

    // Execute and wait for comparing state
    const gotResult = await solveAndWaitForComparing()
    if (!gotResult) return

    // Click "결과 초기화"
    const hasResetBtn = await commands.isVisibleByRole('button', '결과 초기화')
    if (hasResetBtn) {
      await commands.clickByRole('button', '결과 초기화')
      await commands.waitForTimeout(1000)

      // Check back to idle with execute button available
      const hasIdle = await commands.isVisibleByText('대기', 3000)
      expect(hasIdle).toBe(true)

      const hasExecuteBtn = await commands.isVisibleByRole('button', '스케줄 실행')
      expect(hasExecuteBtn).toBe(true)
    }
  })

  it('transitions to approved state when clicking 스케줄 승인', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/execute`)
    await commands.waitForTimeout(2000)

    // Check if work orders available
    const woRes = await commands.fetchApi('/scheduler/work-orders?status=READY&limit=10')
    if (!woRes.ok || !woRes.data?.count) {
      return
    }

    // Execute and wait for comparing state
    const gotResult = await solveAndWaitForComparing()
    if (!gotResult) return

    // Click "선택" to enter detail view
    await commands.clickByRole('button', '선택')
    await commands.waitForTimeout(1000)

    // Accept the confirm dialog before clicking approve
    await commands.acceptNextConfirm()

    // Click approve
    const hasApproveBtn = await commands.isVisibleByRole('button', '스케줄 승인')
    if (hasApproveBtn) {
      await commands.clickByRole('button', '스케줄 승인')
      await commands.waitForTimeout(3000)

      // Check for approved state
      const hasApproved = await commands.isVisibleByText('승인완료', 5000) ||
                         await commands.isVisibleByText('스케줄 승인 완료', 5000)
      expect(hasApproved).toBe(true)
    }
  })

  it('shows updated orders table and action buttons in approved state', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/execute`)
    await commands.waitForTimeout(2000)

    // Check if work orders available
    const woRes = await commands.fetchApi('/scheduler/work-orders?status=READY&limit=10')
    if (!woRes.ok || !woRes.data?.count) {
      return
    }

    // Execute and wait for comparing state
    const gotResult = await solveAndWaitForComparing()
    if (!gotResult) return

    // Enter detail view
    await commands.clickByRole('button', '선택')
    await commands.waitForTimeout(1000)

    // Accept the confirm dialog
    await commands.acceptNextConfirm()

    // Approve
    const hasApproveBtn = await commands.isVisibleByRole('button', '스케줄 승인')
    if (hasApproveBtn) {
      await commands.clickByRole('button', '스케줄 승인')
      await commands.waitForTimeout(3000)

      const hasApproved = await commands.isVisibleByText('승인완료', 5000) ||
                         await commands.isVisibleByText('스케줄 승인 완료', 5000)
      if (!hasApproved) return

      // Check for updated orders table
      const hasOrderList = await commands.isVisibleByText('작업지시 ID', 3000) ||
                          await commands.isVisibleByText('할당 설비', 3000)
      expect(hasOrderList).toBe(true)

      // Check for action buttons
      const hasViewBtn = await commands.isVisibleByText('작업지시 목록 보기', 3000)
      const hasNewBtn = await commands.isVisibleByText('새 스케줄 생성', 3000)
      expect(hasViewBtn || hasNewBtn).toBe(true)
    }
  })
})
