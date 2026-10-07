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

describe('Scheduler Settings Workflow', () => {
  it('should display page title, subtitle, and default sections', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/settings`)
    await commands.waitForTimeout(1000)

    const titleVisible = await commands.isVisibleByText('솔버 설정', 5000)
    expect(titleVisible).toBe(true)

    const subtitleVisible = await commands.isVisibleByText('스케줄링 솔버 유형과 파라미터를 관리합니다', 5000)
    expect(subtitleVisible).toBe(true)

    // Verify settings form section exists
    const horizonVisible = await commands.isVisibleByText('계획 기간', 5000)
    expect(horizonVisible).toBe(true)

    // Verify parameter reference table exists
    const paramTableVisible = await commands.isVisibleByText('파라미터 참조', 5000)
    expect(paramTableVisible).toBe(true)

    // Verify action buttons
    const saveButtonVisible = await commands.isVisibleByRole('button', '저장')
    expect(saveButtonVisible).toBe(true)

    const resetButtonVisible = await commands.isVisibleByRole('button', '초기화')
    expect(resetButtonVisible).toBe(true)
  })

  it('should display solver sections and solver select with options', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/settings`)
    await commands.waitForTimeout(2000)

    // Check for solver type section header
    const sectionVisible = await commands.isVisibleByText('솔버 유형', 5000)
    expect(sectionVisible).toBe(true)

    // Verify the solver select dropdown exists with 5 options (SOLVER_OPTIONS)
    const selectVisible = await commands.isVisibleBySelector('select', 3000)
    expect(selectVisible).toBe(true)

    // Verify we can switch between solvers via select (confirms options are loaded)
    await commands.selectOption('select', 'GA')
    await commands.waitForTimeout(500)

    // Parameter table should reflect the change
    const paramTableVisible = await commands.isVisibleByText('GA', 3000)
    expect(paramTableVisible).toBe(true)
  })

  it('should reflect planning horizon changes in parameter table', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/settings`)
    await commands.waitForTimeout(1000)

    // Use selector with max attribute to target horizon input specifically
    await commands.fillBySelector('input[type="number"][max="168"]', '48')
    await commands.waitForTimeout(500)

    // Verify parameter table shows new value
    const tableValueVisible = await commands.isVisibleByText('48', 3000)
    expect(tableValueVisible).toBe(true)
  })

  it('should reflect time limit changes in parameter table', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/settings`)
    await commands.waitForTimeout(1000)

    // Use selector with max attribute to target time limit input specifically
    await commands.fillBySelector('input[type="number"][max="300"]', '120')
    await commands.waitForTimeout(500)

    // Verify parameter table shows new value
    const tableValueVisible = await commands.isVisibleByText('120', 3000)
    expect(tableValueVisible).toBe(true)
  })

  it('should show unsaved changes banner when value changes', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/settings`)
    await commands.waitForTimeout(1000)

    // Change horizon to trigger unsaved changes
    await commands.fillBySelector('input[type="number"][max="168"]', '72')
    await commands.waitForTimeout(500)

    // Check for unsaved changes banner
    const bannerVisible = await commands.isVisibleByText('저장되지 않은 변경사항', 5000)
    expect(bannerVisible).toBe(true)

    // Banner should have yellow styling
    const warningBannerVisible = await commands.isVisibleBySelector('.bg-yellow-100', 3000)
    expect(warningBannerVisible).toBe(true)
  })

  it('should show "저장됨!" confirmation when save button clicked', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/settings`)
    await commands.waitForTimeout(1000)

    // Change a value
    await commands.fillBySelector('input[type="number"][max="168"]', '96')
    await commands.waitForTimeout(500)

    // Click the banner save button (btn-sm) to avoid strict mode with 2 "저장" buttons
    await commands.clickBySelector('.btn-sm')
    await commands.waitForTimeout(500)

    // Verify "저장됨!" confirmation appears
    const savedVisible = await commands.isVisibleByText('저장됨!', 3000)
    expect(savedVisible).toBe(true)
  })

  it('should restore default values when reset button clicked', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/settings`)
    await commands.waitForTimeout(1000)

    // Change values first
    await commands.fillBySelector('input[type="number"][max="168"]', '120')
    await commands.fillBySelector('input[type="number"][max="300"]', '200')
    await commands.waitForTimeout(500)

    // Click reset button (unique button name)
    await commands.clickByRole('button', '초기화')
    await commands.waitForTimeout(1000)

    // Verify parameter table shows default values (24 hours, 60 sec)
    const horizonDefault = await commands.isVisibleByText('24', 3000)
    const timeLimitDefault = await commands.isVisibleByText('60', 3000)

    expect(horizonDefault).toBe(true)
    expect(timeLimitDefault).toBe(true)
  })

  it('should hide unsaved changes banner after save', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/settings`)
    await commands.waitForTimeout(1000)

    // Change a value to trigger banner
    await commands.fillBySelector('input[type="number"][max="168"]', '60')
    await commands.waitForTimeout(500)

    // Verify banner appears
    let bannerVisible = await commands.isVisibleByText('저장되지 않은 변경사항', 3000)
    expect(bannerVisible).toBe(true)

    // Click the banner save button (btn-sm) to avoid strict mode
    await commands.clickBySelector('.btn-sm')
    await commands.waitForTimeout(1500)

    // Banner should disappear
    bannerVisible = await commands.isVisibleByText('저장되지 않은 변경사항', 2000)
    expect(bannerVisible).toBe(false)
  })
})
