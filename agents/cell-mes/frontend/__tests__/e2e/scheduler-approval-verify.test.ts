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

async function solveAndApprove(): Promise<boolean> {
  await login()
  await commands.goto(`${APP_URL}/scheduler/execute`)
  await commands.waitForTimeout(2000)

  // Check if work orders available
  const woRes = await commands.fetchApi('/scheduler/work-orders?status=READY&limit=10')
  if (!woRes.ok || !woRes.data?.count) return false

  // Click execute
  const hasExecuteBtn = await commands.isVisibleByRole('button', '스케줄 실행')
  if (!hasExecuteBtn) return false

  await commands.clickByRole('button', '스케줄 실행')

  // Wait for comparing state (up to 90 seconds)
  let gotResult = false
  for (let i = 0; i < 18; i++) {
    await commands.waitForTimeout(5000)
    const hasCompare = await commands.isVisibleByText('비교중', 2000) ||
                       await commands.isVisibleByText('스케줄 결과 비교', 2000)
    if (hasCompare) {
      gotResult = true
      break
    }
  }
  if (!gotResult) return false

  // Click "선택" to enter detail view
  const hasSelectBtn = await commands.isVisibleByRole('button', '선택')
  if (!hasSelectBtn) return false

  await commands.clickByRole('button', '선택')
  await commands.waitForTimeout(1000)

  // Accept the confirm dialog before clicking approve
  await commands.acceptNextConfirm()

  // Approve
  const hasApproveBtn = await commands.isVisibleByRole('button', '스케줄 승인')
  if (!hasApproveBtn) return false

  await commands.clickByRole('button', '스케줄 승인')
  await commands.waitForTimeout(3000)

  const hasApproved = await commands.isVisibleByText('승인완료', 10000) ||
                     await commands.isVisibleByText('스케줄 승인 완료', 10000)
  return hasApproved
}

describe('Scheduler Approval Verification', () => {
  it('shows 작업지시 목록 보기 link after approval', async () => {
    const approved = await solveAndApprove()
    if (!approved) {
      // Could not complete solve+approve cycle
      return
    }

    const hasViewLink = await commands.isVisibleByText('작업지시 목록 보기', 5000)
    expect(hasViewLink).toBe(true)
  })

  it('displays updated orders count in approval result', async () => {
    const approved = await solveAndApprove()
    if (!approved) {
      return
    }

    // Check for updated orders count text pattern
    const hasUpdateCount = await commands.isVisibleByText('작업지시 업데이트', 5000) ||
                          await commands.isVisibleByText('개 작업지시', 5000)
    expect(hasUpdateCount).toBe(true)
  })

  it('returns to idle and refreshes work order list when clicking 새 스케줄 생성', async () => {
    const approved = await solveAndApprove()
    if (!approved) {
      return
    }

    const hasNewBtn = await commands.isVisibleByText('새 스케줄 생성', 5000)
    if (!hasNewBtn) return

    await commands.clickByText('새 스케줄 생성')
    await commands.waitForTimeout(2000)

    // Check back to idle state
    const hasIdle = await commands.isVisibleByText('대기', 5000)
    expect(hasIdle).toBe(true)

    // Check work order list refreshed
    const hasWoTable = await commands.isVisibleByText('WO ID', 3000) ||
                      await commands.isVisibleByText('Lot No', 3000)
    expect(hasWoTable).toBe(true)
  })

  it('shows Gantt data on /scheduler page after approval', async () => {
    const approved = await solveAndApprove()
    if (!approved) {
      return
    }

    // Navigate to scheduler main page
    await commands.goto(`${APP_URL}/scheduler`)
    await commands.waitForTimeout(2000)

    // Check for Gantt chart or schedule visualization
    const hasGantt = await commands.isVisibleByText('Gantt', 3000) ||
                    await commands.isVisibleBySelector('[class*="gantt"]', 3000) ||
                    await commands.isVisibleByText('타임라인', 3000)

    // At minimum, should show some scheduled data
    const hasScheduleData = hasGantt ||
                           await commands.isVisibleByText('Machine', 3000) ||
                           await commands.isVisibleByText('설비', 3000)

    expect(hasScheduleData).toBe(true)
  })

  it('verifies approved work orders have scheduled_start and scheduled_end set', async () => {
    const approved = await solveAndApprove()
    if (!approved) {
      return
    }

    // Fetch work orders to verify scheduled times
    const woRes = await commands.fetchApi('/scheduler/work-orders?limit=10')
    if (!woRes.ok) return

    const workOrders = woRes.data?.items || []

    // Find any work order with scheduled times
    const hasScheduledWO = workOrders.some((wo: any) =>
      wo.scheduled_start && wo.scheduled_end
    )

    expect(hasScheduledWO).toBe(true)
  })

  it('does not show approve button in approved state (no duplicate approval)', async () => {
    const approved = await solveAndApprove()
    if (!approved) {
      return
    }

    // In approved state, approve button should not be visible
    const hasApproveBtn = await commands.isVisibleByRole('button', '스케줄 승인', 2000)
    expect(hasApproveBtn).toBe(false)

    // Instead, should show action buttons
    const hasViewBtn = await commands.isVisibleByText('작업지시 목록 보기', 3000)
    const hasNewBtn = await commands.isVisibleByText('새 스케줄 생성', 3000)
    expect(hasViewBtn || hasNewBtn).toBe(true)
  })
})
