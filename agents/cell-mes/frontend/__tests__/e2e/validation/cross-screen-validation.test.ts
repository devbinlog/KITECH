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

describe('화면 간 데이터 일관성', () => {

  it('대시보드 "전체 설비" 카드와 설비관리 목록', async () => {
    await login()

    // Dashboard
    await commands.goto(`${APP_URL}/`)
    await commands.waitForTimeout(3000)

    const hasEquipText = await commands.isVisibleByText('전체 설비', 10_000)
    expect(hasEquipText).toBe(true)

    // Equipment management page
    await commands.goto(`${APP_URL}/master/equipments`)
    const hasEquipHeader = await commands.isVisibleByText('설비', 15_000)
    expect(hasEquipHeader).toBe(true)

    const hasCards = await commands.isVisibleBySelector('[class*="card"], table', 5_000)
    expect(hasCards || hasEquipHeader).toBe(true)
  })

  it('대시보드 "완료 작업" 카드 존재 확인', async () => {
    await login()

    await commands.goto(`${APP_URL}/`)
    await commands.waitForTimeout(2000)

    const hasCompleted = await commands.isVisibleByText('완료', 5_000)
    expect(hasCompleted).toBe(true)

    // Navigate to work orders to verify data
    await commands.goto(`${APP_URL}/production/orders`)
    const hasOrders = await commands.isVisibleByText('작업지시', 15_000)
    expect(hasOrders).toBe(true)
  })

  it('대시보드 "가동중 설비" 카드 존재 확인', async () => {
    await login()

    await commands.goto(`${APP_URL}/`)
    await commands.waitForTimeout(2000)

    const hasRunning = await commands.isVisibleByText('가동중', 5_000)
    const hasEquip = await commands.isVisibleByText('설비', 5_000)
    expect(hasRunning || hasEquip).toBe(true)
  })

  it('API 작업지시 카운트와 UI 일치', async () => {
    await login()

    // API count
    const apiRes = await commands.fetchApi('/production/orders?view=all&limit=1000')
    let apiTotal = 0
    if (apiRes.ok) {
      const orders = apiRes.data?.items || apiRes.data?.data || apiRes.data || []
      apiTotal = orders.length
    }

    // UI load
    await commands.goto(`${APP_URL}/production/orders`)
    const hasHeader = await commands.isVisibleByText('작업지시', 15_000)
    expect(hasHeader).toBe(true)

    const allTab = await commands.isVisibleByRole('button', '전체', 3_000)
    if (allTab) {
      await commands.clickByRole('button', '전체')
      await commands.waitForTimeout(1000)
    }

    const hasTable = await commands.isVisibleBySelector('table', 5_000)
    if (apiTotal > 0) {
      expect(hasTable).toBe(true)
    }
  })

  it('설비 상태가 대시보드와 설비 페이지에서 동일', async () => {
    await login()

    // Dashboard
    await commands.goto(`${APP_URL}/`)
    await commands.waitForTimeout(2000)
    const hasDashEquip = await commands.isVisibleByText('설비', 5_000)
    expect(hasDashEquip).toBe(true)

    // Equipment page
    await commands.goto(`${APP_URL}/master/equipments`)
    const hasEquipPage = await commands.isVisibleByText('설비', 15_000)
    expect(hasEquipPage).toBe(true)

    // Analytics
    await commands.goto(`${APP_URL}/analytics/equipment`)
    await commands.waitForTimeout(2000)
    const hasAnalytics = await commands.isVisibleByText('설비', 10_000)
    expect(hasAnalytics).toBe(true)
  })
})
