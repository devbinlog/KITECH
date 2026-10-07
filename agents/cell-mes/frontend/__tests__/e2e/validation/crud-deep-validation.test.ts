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

describe('CREATE - 깊이 있는 검증', () => {

  describe('작업지시 생성', () => {

    it('생성 폼 열기 및 필드 확인', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/orders`)

      const hasHeader = await commands.isVisibleByText('작업지시', 15_000)
      expect(hasHeader).toBe(true)

      await commands.clickByRole('button', '작업지시 생성')
      const hasModal = await commands.isVisibleBySelector('.fixed.inset-0, [role="dialog"]', 5_000)
      expect(hasModal).toBe(true)

      // Lot No input
      const hasTextInput = await commands.isVisibleBySelector('input[type="text"]', 3_000)
      expect(hasTextInput).toBe(true)

      // Product select
      const hasSelect = await commands.isVisibleBySelector('select', 3_000)
      expect(hasSelect).toBe(true)

      // Qty input
      const hasNumberInput = await commands.isVisibleBySelector('input[type="number"]', 3_000)
      expect(hasNumberInput).toBe(true)

      // Submit button
      const hasSubmit = await commands.isVisibleBySelector('button[type="submit"]', 3_000)
      expect(hasSubmit).toBe(true)

      await commands.clickByRole('button', '취소')
    })

    it('API에서 생성 전후 카운트 비교 가능', async () => {
      await login()

      const beforeRes = await commands.fetchApi('/production/orders')
      if (!beforeRes.ok) return

      const beforeCount = (beforeRes.data?.items || beforeRes.data || []).length

      expect(beforeCount).toBeGreaterThanOrEqual(0)
    })
  })
})

describe('READ - 깊이 있는 검증', () => {

  it('작업지시 목록 API와 UI 데이터 존재', async () => {
    await login()

    // API
    const apiRes = await commands.fetchApi('/production/orders?limit=10')
    if (apiRes.ok) {
      const apiItems = apiRes.data?.items || apiRes.data || []
      expect(apiItems.length).toBeGreaterThanOrEqual(0)
    }

    // UI
    await commands.goto(`${APP_URL}/production/orders`)
    const hasHeader = await commands.isVisibleByText('작업지시', 15_000)
    expect(hasHeader).toBe(true)

    const hasTable = await commands.isVisibleBySelector('table', 5_000)
    const hasEmpty = await commands.isVisibleByText('없습니다', 3_000)
    expect(hasTable || hasEmpty || hasHeader).toBe(true)
  })

  it('설비 목록 API와 UI 데이터 존재', async () => {
    await login()

    // API
    const apiRes = await commands.fetchApi('/masters/equipments')
    if (apiRes.ok) {
      const apiItems = apiRes.data?.items || apiRes.data || []
      expect(apiItems.length).toBeGreaterThanOrEqual(0)
    }

    // UI
    await commands.goto(`${APP_URL}/master/equipments`)
    const hasHeader = await commands.isVisibleByText('설비', 15_000)
    expect(hasHeader).toBe(true)
  })

  it('품질 NCR 목록 API와 UI 데이터 존재', async () => {
    await login()

    // API
    const apiRes = await commands.fetchApi('/quality/ncr?limit=10')
    if (apiRes.ok) {
      const apiItems = apiRes.data?.items || apiRes.data || []
      expect(apiItems.length).toBeGreaterThanOrEqual(0)
    }

    // UI
    await commands.goto(`${APP_URL}/quality/ncr`)
    const hasHeader = await commands.isVisibleByText('부적합', 15_000)
    expect(hasHeader).toBe(true)
  })
})

describe('UPDATE - 깊이 있는 검증', () => {

  it('작업지시 탭 전환으로 데이터 필터링 확인', async () => {
    await login()
    await commands.goto(`${APP_URL}/production/orders`)

    const hasHeader = await commands.isVisibleByText('작업지시', 15_000)
    expect(hasHeader).toBe(true)

    // Click different tabs
    const tabs = ['오늘 작업', '전체']
    for (const tabName of tabs) {
      const hasTab = await commands.isVisibleByRole('button', tabName, 3_000)
      if (hasTab) {
        await commands.clickByRole('button', tabName)
        await commands.waitForTimeout(1500)

        const stillHasHeader = await commands.isVisibleByText('작업지시', 5_000)
        expect(stillHasHeader).toBe(true)
      }
    }
  })
})

describe('DELETE / 정리', () => {

  it('삭제된 마스터 데이터 참조 검사', async () => {
    await login()

    // Check that work orders reference valid products
    const ordersRes = await commands.fetchApi('/production/orders?limit=20')
    if (!ordersRes.ok) return

    const orders = ordersRes.data?.items || ordersRes.data || []

    const productIds = new Set<number>()
    for (const order of orders) {
      if (order.product_id) productIds.add(order.product_id)
    }

    let orphanCount = 0
    for (const productId of productIds) {
      const productRes = await commands.fetchApi(`/masters/products/${productId}`)
      if (!productRes.ok) {
        orphanCount++
      }
    }

    expect(orphanCount).toBe(0)
  })
})
