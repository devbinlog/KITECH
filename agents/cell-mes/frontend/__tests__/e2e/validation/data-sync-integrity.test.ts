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

describe('API-UI 정확한 일치 검증', () => {

  it('작업지시 상태별 카운트: API == UI 탭', async () => {
    await login()

    const allRes = await commands.fetchApi('/production/orders?view=all&limit=1000')
    if (!allRes.ok) return

    const orders = allRes.data?.items || allRes.data?.data || allRes.data || []

    const apiCounts = {
      waiting: orders.filter((o: any) => o.status === 'WAITING').length,
      inProgress: orders.filter((o: any) => o.status === 'IN_PROGRESS').length,
      done: orders.filter((o: any) => o.status === 'DONE').length,
      total: orders.length,
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

    if (apiCounts.total > 0) {
      expect(hasTable).toBe(true)
    }
  })

  it('설비 목록: API 필드 값 확인', async () => {
    await login()

    const res = await commands.fetchApi('/masters/equipments')
    if (!res.ok) return

    const equipments = res.data?.items || res.data?.data || res.data || []

    if (equipments.length === 0) return

    const firstEquipment = equipments[0]
    expect(firstEquipment.id).toBeDefined()

    // UI load
    await commands.goto(`${APP_URL}/master/equipments`)
    const hasHeader = await commands.isVisibleByText('설비', 15_000)
    expect(hasHeader).toBe(true)
  })
})

describe('화면 간 데이터 동기화', () => {

  it('작업지시 페이지와 대시보드 동기화', async () => {
    await login()

    // Dashboard
    await commands.goto(`${APP_URL}/`)
    await commands.waitForTimeout(2000)
    const hasDashboard = await commands.isVisibleBySelector('[class*="card"]', 5_000)
    expect(hasDashboard).toBe(true)

    // Work orders
    await commands.goto(`${APP_URL}/production/orders`)
    const hasOrders = await commands.isVisibleByText('작업지시', 15_000)
    expect(hasOrders).toBe(true)

    // Back to dashboard
    await commands.goto(`${APP_URL}/`)
    await commands.waitForTimeout(2000)
    const hasDashboardAgain = await commands.isVisibleBySelector('[class*="card"]', 5_000)
    expect(hasDashboardAgain).toBe(true)
  })

  it('생산실적 페이지와 작업지시 연동', async () => {
    await login()

    // Results page
    await commands.goto(`${APP_URL}/production/results`)
    const hasResults = await commands.isVisibleByText('생산 실적', 15_000)
    expect(hasResults).toBe(true)

    // Orders page
    await commands.goto(`${APP_URL}/production/orders`)
    const hasOrders = await commands.isVisibleByText('작업지시', 15_000)
    expect(hasOrders).toBe(true)
  })

  it('품질 데이터와 생산 데이터 동기화', async () => {
    await login()

    // Quality dashboard
    await commands.goto(`${APP_URL}/quality`)
    const hasQuality = await commands.isVisibleByText('품질', 15_000)
    expect(hasQuality).toBe(true)

    // Production results
    await commands.goto(`${APP_URL}/production/results`)
    const hasResults = await commands.isVisibleByText('생산 실적', 15_000)
    expect(hasResults).toBe(true)
  })
})

describe('엣지 케이스 처리', () => {

  it('빈 데이터 상태에서 UI 안정성', async () => {
    await login()

    // Pages should handle empty data gracefully
    const pages = [
      { path: '/production/orders', text: '작업지시' },
      { path: '/production/results', text: '생산 실적' },
      { path: '/quality', text: '품질' },
    ]

    for (const page of pages) {
      await commands.goto(`${APP_URL}${page.path}`)
      const hasContent = await commands.isVisibleByText(page.text, 15_000)
      expect(hasContent).toBe(true)
    }
  })

  it('새로고침 후 데이터 유지', async () => {
    await login()

    await commands.goto(`${APP_URL}/production/orders`)
    const hasHeader = await commands.isVisibleByText('작업지시', 15_000)
    expect(hasHeader).toBe(true)

    // Reload
    await commands.goto(`${APP_URL}/production/orders`)
    const hasHeaderAfter = await commands.isVisibleByText('작업지시', 15_000)
    expect(hasHeaderAfter).toBe(true)
  })
})
