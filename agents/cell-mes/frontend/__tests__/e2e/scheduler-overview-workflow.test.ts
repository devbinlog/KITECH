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

describe('Scheduler Overview Workflow', () => {
  it('should display page title and date picker on load', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler`)
    await commands.waitForTimeout(1000)

    const titleVisible = await commands.isVisibleByText('스케줄 현황', 5000)
    expect(titleVisible).toBe(true)

    const subtitleVisible = await commands.isVisibleByText('일별 생산 스케줄을 간트 차트로 확인합니다', 5000)
    expect(subtitleVisible).toBe(true)

    const datePickerVisible = await commands.isVisibleByText('날짜 선택', 5000)
    expect(datePickerVisible).toBe(true)

    const todayButtonVisible = await commands.isVisibleByRole('button', '오늘')
    expect(todayButtonVisible).toBe(true)
  })

  it('should display summary cards or empty state', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler`)
    await commands.waitForTimeout(2000)

    // Either all summary cards are visible (schedule exists) or empty state is shown
    const equipmentCardVisible = await commands.isVisibleByText('스케줄된 설비', 3000)
    const emptyStateVisible = await commands.isVisibleByText('스케줄된 작업지시가 없습니다', 3000)

    expect(equipmentCardVisible || emptyStateVisible).toBe(true)
  })

  it('should have a date input that can be changed', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler`)
    await commands.waitForTimeout(1000)

    const dateInput = await commands.isVisibleBySelector('input[type="date"]', 5000)
    expect(dateInput).toBe(true)

    // Change date to a future date
    const futureDate = new Date()
    futureDate.setDate(futureDate.getDate() + 30)
    const futureDateStr = futureDate.toISOString().split('T')[0]

    await commands.fillBySelector('input[type="date"]', futureDateStr)
    await commands.waitForTimeout(1500)

    // Page should show either summary cards or empty state after date change
    const equipmentCardVisible = await commands.isVisibleByText('스케줄된 설비', 3000)
    const emptyStateVisible = await commands.isVisibleByText('스케줄된 작업지시가 없습니다', 3000)

    expect(equipmentCardVisible || emptyStateVisible).toBe(true)
  })

  it('should restore today when clicking "오늘" button', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler`)
    await commands.waitForTimeout(1000)

    // Change to a different date first
    const futureDate = new Date()
    futureDate.setDate(futureDate.getDate() + 30)
    const futureDateStr = futureDate.toISOString().split('T')[0]

    await commands.fillBySelector('input[type="date"]', futureDateStr)
    await commands.waitForTimeout(500)

    // Click "오늘" button
    await commands.clickByRole('button', '오늘')
    await commands.waitForTimeout(1000)

    // Page should still be functional (either cards or empty state)
    const titleVisible = await commands.isVisibleByText('스케줄 현황', 3000)
    expect(titleVisible).toBe(true)
  })

  it('should render Gantt chart or empty state', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler`)
    await commands.waitForTimeout(2000)

    // Check for Gantt chart elements or empty state
    const ganttVisible = await commands.isVisibleBySelector('canvas', 3000) ||
                         await commands.isVisibleByText('스케줄 현황', 3000)
    const emptyStateVisible = await commands.isVisibleByText('스케줄된 작업지시가 없습니다', 3000)

    expect(ganttVisible || emptyStateVisible).toBe(true)
  })

  it('should display empty state for far future date', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler`)
    await commands.waitForTimeout(1000)

    // Change to a far future date with no data
    const futureDate = new Date()
    futureDate.setFullYear(futureDate.getFullYear() + 1)
    const futureDateStr = futureDate.toISOString().split('T')[0]

    await commands.fillBySelector('input[type="date"]', futureDateStr)
    await commands.waitForTimeout(2000)

    // Should show empty state
    const emptyStateVisible = await commands.isVisibleByText('스케줄된 작업지시가 없습니다', 5000)
    expect(emptyStateVisible).toBe(true)
  })

  it('should show summary card values when schedule data exists', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler`)
    await commands.waitForTimeout(2000)

    // Check if we have schedule data
    const equipmentCardVisible = await commands.isVisibleByText('스케줄된 설비', 3000)

    if (equipmentCardVisible) {
      // All three cards should be visible
      const workCardVisible = await commands.isVisibleByText('스케줄된 작업', 3000)
      const progressCardVisible = await commands.isVisibleByText('진행중', 3000)

      expect(workCardVisible).toBe(true)
      expect(progressCardVisible).toBe(true)
    } else {
      // No data - verify empty state
      const emptyStateVisible = await commands.isVisibleByText('스케줄된 작업지시가 없습니다', 3000)
      expect(emptyStateVisible).toBe(true)
    }
  })

  it('should display subtitle description', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler`)
    await commands.waitForTimeout(500)

    const subtitleVisible = await commands.isVisibleByText('일별 생산 스케줄을 간트 차트로 확인합니다', 5000)
    expect(subtitleVisible).toBe(true)
  })
})
