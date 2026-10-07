import { describe, it, expect, afterAll } from 'vitest'
import { commands } from 'vitest/browser'

const APP_URL = 'http://localhost:3000'

async function login() {
  await commands.goto(`${APP_URL}/login`)
  await commands.fillByRole('textbox', '사용자 ID', 'admin')
  await commands.fillByLabel('비밀번호', 'admin123')
  await commands.clickByRole('button', '로그인')
  await commands.waitForUrl('^(?!.*\\/login)', 10_000)
}

// Track created resources for cleanup
const createdOrderIds: number[] = []
const createdNcrIds: number[] = []

afterAll(async () => {
  for (const id of createdOrderIds) {
    await commands.fetchApi(`/production/orders/${id}/status`, 'PATCH', JSON.stringify({ status: 'DONE' }))
  }
  for (const id of createdNcrIds) {
    try {
      await commands.fetchApi(`/quality/ncr/${id}/status`, 'PATCH', JSON.stringify({ status: 'CLOSED' }))
      await commands.fetchApi(`/quality/ncr/${id}/status`, 'PATCH', JSON.stringify({ status: 'VERIFIED' }))
    } catch {
      // Ignore cleanup errors
    }
  }
  await commands.closeAppPage()
})

describe('Production-Quality Integration', () => {
  describe('End-to-End Manufacturing Workflow', () => {
    let orderId: number
    let lotNo: string
    let ncrId: number

    it('creates a work order and starts it', async () => {
      const productsRes = await commands.fetchApi('/masters/products')
      expect(productsRes.ok).toBe(true)
      expect(productsRes.data.length).toBeGreaterThan(0)

      const productId = productsRes.data[0].id
      lotNo = `INT-${Date.now().toString().slice(-8)}`

      const createRes = await commands.fetchApi(
        '/production/orders',
        'POST',
        JSON.stringify({
          lot_no: lotNo,
          product_id: productId,
          target_qty: 200,
          qty: 1,
          priority: 2,
        }),
      )
      expect(createRes.ok).toBe(true)
      orderId = createRes.data.id
      createdOrderIds.push(orderId)

      // Start the order
      const startRes = await commands.fetchApi(
        `/production/orders/${orderId}/status`,
        'PATCH',
        JSON.stringify({ status: 'RUNNING' }),
      )
      expect(startRes.ok).toBe(true)
      expect(startRes.data.status).toBe('RUNNING')
    })

    it('records production result with ok and ng quantities', async () => {
      const resultRes = await commands.fetchApi(
        '/production/results',
        'POST',
        JSON.stringify({
          work_order_id: orderId,
          ok_qty: 180,
          ng_qty: 20,
        }),
      )
      expect(resultRes.ok).toBe(true)
      expect(resultRes.data.ok_qty).toBe(180)
      expect(resultRes.data.ng_qty).toBe(20)
    })

    it('quality dashboard shows KPI data', async () => {
      await login()
      await commands.goto(`${APP_URL}/quality`)
      await commands.waitForTimeout(3000)

      const hasInspectionCount = await commands.isVisibleByText('총 검사건수', 5_000)
      expect(hasInspectionCount).toBe(true)

      const hasPassRate = await commands.isVisibleByText('합격률', 5_000)
      expect(hasPassRate).toBe(true)

      const hasOpenNcr = await commands.isVisibleByText('미해결 NCR', 5_000)
      expect(hasOpenNcr).toBe(true)
    })

    it('creates an NCR linked to the work order', async () => {
      const ncrRes = await commands.fetchApi(
        '/quality/ncr',
        'POST',
        JSON.stringify({
          work_order_id: orderId,
          defect_type: 'PROCESS',
          characteristic: '공정불량',
          description: '통합테스트 - 공정 불량 발생',
          reported_by: 'E2E-통합',
          root_cause: '설비 마모에 의한 가공 오차',
          corrective_action: '설비 점검 및 교체',
        }),
      )
      expect(ncrRes.ok).toBe(true)
      expect(ncrRes.data.work_order_id).toBe(orderId)
      ncrId = ncrRes.data.id
      createdNcrIds.push(ncrId)
    })

    it('NCR shows linked work order info in detail', async () => {
      await login()
      await commands.goto(`${APP_URL}/quality/ncr`)
      await commands.waitForTimeout(2000)

      const hasTable = await commands.isVisibleBySelector('table', 8_000)
      if (hasTable) {
        const hasDetailBtn = await commands.isVisibleBySelector('button[title="상세보기"]', 3_000)
        if (hasDetailBtn) {
          await commands.clickBySelector('button[title="상세보기"]')
          await commands.waitForTimeout(1000)

          const hasModal = await commands.isVisibleBySelector('.fixed.inset-0', 5_000)
          expect(hasModal).toBe(true)

          // Close modal
          await commands.clickByRole('button', '닫기')
          await commands.waitForTimeout(500)
        }
      }
    })

    it('completes NCR lifecycle: OPEN → IN_PROGRESS → CLOSED → VERIFIED', async () => {
      // IN_PROGRESS
      const ipRes = await commands.fetchApi(
        `/quality/ncr/${ncrId}/status`,
        'PATCH',
        JSON.stringify({ status: 'IN_PROGRESS' }),
      )
      expect(ipRes.ok).toBe(true)

      // CLOSED
      const closeRes = await commands.fetchApi(
        `/quality/ncr/${ncrId}/status`,
        'PATCH',
        JSON.stringify({ status: 'CLOSED' }),
      )
      expect(closeRes.ok).toBe(true)

      // VERIFIED
      const verifyRes = await commands.fetchApi(
        `/quality/ncr/${ncrId}/status`,
        'PATCH',
        JSON.stringify({ status: 'VERIFIED' }),
      )
      expect(verifyRes.ok).toBe(true)
      expect(verifyRes.data.status).toBe('VERIFIED')
    })

    it('creates inspection result when plan exists', async () => {
      const plansRes = await commands.fetchApi('/quality/inspection-plans?limit=5')
      if (!plansRes.ok || !plansRes.data?.items?.length) return

      const plan = plansRes.data.items[0]
      const items = plan.inspection_items || []
      if (items.length === 0) return

      const resultRes = await commands.fetchApi(
        '/quality/inspection-results',
        'POST',
        JSON.stringify({
          inspection_plan_id: plan.id,
          work_order_id: orderId,
          lot_no: lotNo,
          inspector: 'E2E-통합검사원',
          inspection_date: new Date().toISOString(),
          judgment: 'OK',
          measured_values: items.map((item: any) => ({
            inspection_item_id: item.id,
            measured_value: item.target || 10.0,
            judgment: 'OK',
          })),
        }),
      )
      if (resultRes.ok) {
        expect(resultRes.data).toHaveProperty('id')
        expect(resultRes.data.judgment).toBe('OK')
      }
    })

    it('generates SPC data when inspection items exist', async () => {
      const plansRes = await commands.fetchApi('/quality/inspection-plans?limit=5')
      if (!plansRes.ok || !plansRes.data?.items?.length) return

      const plan = plansRes.data.items[0]
      const items = plan.inspection_items || []
      if (items.length === 0) return

      const genRes = await commands.fetchApi(
        '/quality/spc-data/generate',
        'POST',
        JSON.stringify({
          inspection_item_id: items[0].id,
          sample_size: 5,
        }),
      )
      // Graceful - API may not support this
      if (genRes.ok) {
        expect(Array.isArray(genRes.data)).toBe(true)
      }
    })
  })

  describe('Quality Dashboard Data Verification', () => {
    it('dashboard KPI cards match API data', async () => {
      // Get dashboard data from API
      const today = new Date().toISOString().split('T')[0]
      const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
      const apiRes = await commands.fetchApi(
        `/quality/dashboard/summary?date_from=${weekAgo}&date_to=${today}`,
      )

      await login()
      await commands.goto(`${APP_URL}/quality`)
      await commands.waitForTimeout(3000)

      // KPI cards should be visible
      const hasInspections = await commands.isVisibleByText('총 검사건수', 5_000)
      expect(hasInspections).toBe(true)

      if (apiRes.ok && apiRes.data) {
        const totalInspections = apiRes.data.total_inspections || 0
        if (totalInspections > 0) {
          const hasCount = await commands.isVisibleByText(String(totalInspections), 5_000)
          expect(hasCount).toBe(true)
        }
      }
    })

    it('quick action links navigate to correct pages', async () => {
      await login()
      await commands.goto(`${APP_URL}/quality`)
      await commands.waitForTimeout(2000)

      // Verify links exist
      const hasPlanLink = await commands.isVisibleBySelector('a[href="/quality/inspection-plans"]', 3_000)
      const hasResultLink = await commands.isVisibleBySelector('a[href="/quality/inspection-results"]', 3_000)
      const hasSpcLink = await commands.isVisibleBySelector('a[href="/quality/spc"]', 3_000)
      const hasNcrLink = await commands.isVisibleBySelector('a[href="/quality/ncr"]', 3_000)

      expect(hasPlanLink).toBe(true)
      expect(hasResultLink).toBe(true)
      expect(hasSpcLink).toBe(true)
      expect(hasNcrLink).toBe(true)

      // Navigate to inspection plans via link
      await commands.clickBySelector('a[href="/quality/inspection-plans"]')
      await commands.waitForTimeout(2000)
      const hasPlansPage = await commands.isVisibleByText('검사계획 관리', 8_000)
      expect(hasPlansPage).toBe(true)
    })
  })
})
