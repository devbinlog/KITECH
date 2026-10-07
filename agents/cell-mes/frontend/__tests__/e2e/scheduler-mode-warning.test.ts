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

describe('Scheduler Mode Selection and Warnings', () => {
  it('should display mode selection section with all three modes', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/execute`)

    // Check section header
    const headerVisible = await commands.isVisibleByText('스케줄링 모드', 5000)
    expect(headerVisible).toBe(true)

    // Check all three mode cards are visible
    const newModeVisible = await commands.isVisibleByText('신규 수립', 5000)
    expect(newModeVisible).toBe(true)

    const rescheduleModeVisible = await commands.isVisibleByText('재스케줄링', 5000)
    expect(rescheduleModeVisible).toBe(true)

    const fullRebalanceModeVisible = await commands.isVisibleByText('전체 재배치', 5000)
    expect(fullRebalanceModeVisible).toBe(true)
  })

  it('should have "신규 수립" mode selected by default with no warning banner', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/execute`)

    // Check that new mode card is visible
    const newModeCard = await commands.isVisibleBySelector('[data-testid="mode-new"]', 5000)
    expect(newModeCard).toBe(true)

    // Check no warning banner is visible
    const warningBannerVisible = await commands.isVisibleByText('재스케줄링 모드', 2000)
    expect(warningBannerVisible).toBe(false)

    const dangerBannerVisible = await commands.isVisibleByText('전체 재배치 모드', 2000)
    expect(dangerBannerVisible).toBe(false)
  })

  it('should show yellow warning banner when "재스케줄링" mode is selected', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/execute`)

    // Click reschedule mode
    await commands.clickByText('재스케줄링')
    await commands.waitForTimeout(500)

    // Check warning banner is visible
    const warningTitleVisible = await commands.isVisibleByText('재스케줄링 모드', 5000)
    expect(warningTitleVisible).toBe(true)

    const warningMessageVisible = await commands.isVisibleByText('기존 스케줄이 새 결과로 덮어씌워집니다', 5000)
    expect(warningMessageVisible).toBe(true)
  })

  it('should show red danger banner when "전체 재배치" mode is selected', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/execute`)

    // Click full rebalance mode
    await commands.clickByText('전체 재배치')
    await commands.waitForTimeout(500)

    // Check danger banner is visible
    const dangerTitleVisible = await commands.isVisibleByText('전체 재배치 모드', 5000)
    expect(dangerTitleVisible).toBe(true)

    const dangerMessageVisible = await commands.isVisibleByText('진행중 작업까지 재배치됩니다', 5000)
    expect(dangerMessageVisible).toBe(true)
  })

  it('should hide banners when switching back to "신규 수립" mode', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/execute`)

    // First select full rebalance mode to show danger banner
    await commands.clickByText('전체 재배치')
    await commands.waitForTimeout(500)

    // Verify danger banner is visible
    const dangerBannerVisible = await commands.isVisibleByText('전체 재배치 모드', 5000)
    expect(dangerBannerVisible).toBe(true)

    // Switch back to new mode
    await commands.clickByText('신규 수립')
    await commands.waitForTimeout(500)

    // Verify banners are hidden
    const warningBannerHidden = await commands.isVisibleByText('재스케줄링 모드', 2000)
    expect(warningBannerHidden).toBe(false)

    const dangerBannerHidden = await commands.isVisibleByText('전체 재배치 모드', 2000)
    expect(dangerBannerHidden).toBe(false)
  })

  it('should display correct mode tags for each mode', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/execute`)

    // Check tags in default "신규 수립" mode
    const inProgressExcludedVisible = await commands.isVisibleByText('진행중: 제외', 5000)
    expect(inProgressExcludedVisible).toBe(true)

    const existingScheduleExcludedVisible = await commands.isVisibleByText('기스케줄: 제외', 5000)
    expect(existingScheduleExcludedVisible).toBe(true)

    // Switch to "재스케줄링" mode and check tags
    await commands.clickByText('재스케줄링')
    await commands.waitForTimeout(500)

    const rescheduleModeInProgressExcluded = await commands.isVisibleByText('진행중: 제외', 5000)
    expect(rescheduleModeInProgressExcluded).toBe(true)

    const rescheduleModeExistingScheduleIncluded = await commands.isVisibleByText('기스케줄: 포함', 5000)
    expect(rescheduleModeExistingScheduleIncluded).toBe(true)

    // Switch to "전체 재배치" mode and check tags
    await commands.clickByText('전체 재배치')
    await commands.waitForTimeout(500)

    const fullRebalanceModeInProgressIncluded = await commands.isVisibleByText('진행중: 포함', 5000)
    expect(fullRebalanceModeInProgressIncluded).toBe(true)

    const fullRebalanceModeExistingScheduleIncluded = await commands.isVisibleByText('기스케줄: 포함', 5000)
    expect(fullRebalanceModeExistingScheduleIncluded).toBe(true)
  })
})
