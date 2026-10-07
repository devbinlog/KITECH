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

describe('Dashboard', () => {
  describe('KPI cards', () => {
    it('displays KPI metric cards after login', async () => {
      await login()
      await commands.goto(`${APP_URL}/`)

      // Wait for dashboard to load and verify KPI cards
      const hasEquipmentTotal = await commands.isVisibleByText('전체 설비', 10_000)
      expect(hasEquipmentTotal).toBe(true)

      const hasRunningEquipment = await commands.isVisibleByText('가동중 설비')
      expect(hasRunningEquipment).toBe(true)

      const hasActiveWork = await commands.isVisibleByText('진행중 작업')
      expect(hasActiveWork).toBe(true)

      const hasCompletedWork = await commands.isVisibleByText('완료 작업')
      expect(hasCompletedWork).toBe(true)
    })
  })

  describe('Equipment status section', () => {
    it('displays equipment status heading', async () => {
      await login()
      await commands.goto(`${APP_URL}/`)

      const hasSection = await commands.isVisibleByText('설비 현황', 10_000)
      expect(hasSection).toBe(true)
    })

    it('shows equipment data or empty/loading state', async () => {
      await login()
      await commands.goto(`${APP_URL}/`)
      await commands.waitForTimeout(2000)

      // Should have either equipment cards, a grid layout, or a loading/empty state
      const hasGrid = await commands.isVisibleBySelector('[class*="grid"]', 5_000)
      const hasLoading = await commands.isVisibleByText('로딩', 2_000)
      const hasEmpty = await commands.isVisibleByText('설비.*없|No equipment', 2_000)

      expect(hasGrid || hasLoading || hasEmpty).toBe(true)
    })
  })

  describe('Recent work orders section', () => {
    it('displays recent work orders or empty state', async () => {
      await login()
      await commands.goto(`${APP_URL}/`)
      await commands.waitForTimeout(2000)

      // Look for the work orders section, table, or empty message
      const hasSection = await commands.isVisibleByText('최근.*작업지시|작업지시', 5_000)
      const hasTable = await commands.isVisibleBySelector('table', 3_000)
      const hasEmpty = await commands.isVisibleByText('작업지시.*없|등록된.*없', 2_000)
      const hasContent = await commands.isVisibleBySelector('[class*="card"]', 2_000)

      expect(hasSection || hasTable || hasEmpty || hasContent).toBe(true)
    })
  })

  describe('AI Insights section', () => {
    it('displays AI insights heading', async () => {
      await login()
      await commands.goto(`${APP_URL}/`)

      const hasInsights = await commands.isVisibleByText('AI 인사이트', 10_000)
      expect(hasInsights).toBe(true)
    })
  })
})
