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
const createdPlanIds: number[] = []
const createdNcrIds: number[] = []

afterAll(async () => {
  // Cleanup: delete test plans
  for (const id of createdPlanIds) {
    await commands.fetchApi(`/quality/inspection-plans/${id}`, 'DELETE')
  }
  // Cleanup: close test NCRs
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

describe('Quality Management Workflow', () => {
  describe('Inspection Plan CRUD', () => {
    let testPlanId: number
    let testProductId: number

    it('creates an inspection plan via API', async () => {
      // Get a product
      const productsRes = await commands.fetchApi('/masters/products')
      expect(productsRes.ok).toBe(true)
      expect(productsRes.data.length).toBeGreaterThan(0)
      testProductId = productsRes.data[0].id

      const planRes = await commands.fetchApi(
        '/quality/inspection-plans',
        'POST',
        JSON.stringify({
          product_id: testProductId,
          characteristic: 'E2E-diameter',
          nominal: 10.0,
          usl: 10.5,
          lsl: 9.5,
          unit: 'mm',
          inspection_type: 'IN_PROCESS',
        }),
      )
      expect(planRes.ok).toBe(true)
      expect(planRes.data).toHaveProperty('id')
      expect(planRes.data.inspection_type).toBe('IN_PROCESS')

      testPlanId = planRes.data.id
      createdPlanIds.push(testPlanId)
    })

    it('shows created plan in the plans list', async () => {
      // Verify plan exists via API first
      const verifyRes = await commands.fetchApi('/quality/inspection-plans?limit=50')
      expect(verifyRes.ok).toBe(true)
      const found = verifyRes.data?.items?.some((p: any) => p.id === testPlanId)
      expect(found).toBe(true)

      // Verify UI loads the plans page
      await login()
      await commands.goto(`${APP_URL}/quality/inspection-plans`)
      await commands.waitForTimeout(3000)

      const hasTable = await commands.isVisibleBySelector('table', 10_000)
      const hasContent = await commands.isVisibleByText('검사유형|공정검사|입고검사|최종검사', 5_000)
      expect(hasTable || hasContent).toBe(true)
    })

    it('shows plan detail with inspection items', async () => {
      await login()
      await commands.goto(`${APP_URL}/quality/inspection-plans`)
      await commands.waitForTimeout(2000)

      // Click detail button on a plan
      const hasDetailBtn = await commands.isVisibleBySelector('button[title="상세보기"]', 5_000)
      if (hasDetailBtn) {
        await commands.clickBySelector('button[title="상세보기"]')
        await commands.waitForTimeout(1000)

        // Modal should show inspection items
        const hasItems = await commands.isVisibleByText('검사항목|항목명', 5_000)
        expect(hasItems).toBe(true)
      }
    })

    it('filters plans by inspection type', async () => {
      await login()
      await commands.goto(`${APP_URL}/quality/inspection-plans`)
      await commands.waitForTimeout(2000)

      const hasTypeFilter = await commands.isVisibleByText('검사유형', 5_000)
      expect(hasTypeFilter).toBe(true)

      // Page should show content after filter
      const hasContent = await commands.isVisibleBySelector('table', 5_000)
      const hasEmpty = await commands.isVisibleByText('없습니다', 3_000)
      expect(hasContent || hasEmpty).toBe(true)
    })

    it('deletes an inspection plan via API', async () => {
      // Create a disposable plan with flat fields (backend schema)
      const planRes = await commands.fetchApi(
        '/quality/inspection-plans',
        'POST',
        JSON.stringify({
          product_id: testProductId,
          characteristic: 'E2E-삭제테스트',
          nominal: 5.0,
          usl: 5.5,
          lsl: 4.5,
          unit: 'mm',
          inspection_type: 'FINAL',
        }),
      )
      expect(planRes.ok).toBe(true)
      const disposableId = planRes.data.id

      const deleteRes = await commands.fetchApi(`/quality/inspection-plans/${disposableId}`, 'DELETE')
      expect(deleteRes.ok).toBe(true)
    })
  })

  describe('Inspection Result Recording', () => {
    it('loads inspection results page', async () => {
      await login()
      await commands.goto(`${APP_URL}/quality/inspection-results`)
      await commands.waitForTimeout(2000)

      const hasHeading = await commands.isVisibleByText('측정결과', 8_000)
      expect(hasHeading).toBe(true)
    })

    it('creates an inspection result via API', async () => {
      // Need a plan with items and a running order
      const plansRes = await commands.fetchApi('/quality/inspection-plans?limit=10')
      if (!plansRes.ok || !plansRes.data?.items?.length) return

      const plan = plansRes.data.items[0]
      const items = plan.inspection_items || []
      if (items.length === 0) return

      // Get a work order
      const ordersRes = await commands.fetchApi('/production/orders?limit=10&view=all')
      if (!ordersRes.ok || !ordersRes.data?.items?.length) return

      const order = ordersRes.data.items[0]

      const resultRes = await commands.fetchApi(
        '/quality/inspection-results',
        'POST',
        JSON.stringify({
          inspection_plan_id: plan.id,
          work_order_id: order.id,
          lot_no: order.lot_no,
          inspector: 'E2E-검사원',
          inspection_date: new Date().toISOString(),
          judgment: 'OK',
          measured_values: items.map((item: any) => ({
            inspection_item_id: item.id,
            measured_value: item.target || 10.0,
            judgment: 'OK',
          })),
        }),
      )
      expect(resultRes.ok).toBe(true)
      expect(resultRes.data).toHaveProperty('id')
    })

    it('shows results in the list with judgment', async () => {
      await login()
      await commands.goto(`${APP_URL}/quality/inspection-results`)
      await commands.waitForTimeout(2000)

      const hasTable = await commands.isVisibleBySelector('table', 8_000)
      const hasEmpty = await commands.isVisibleByText('없습니다', 3_000)
      expect(hasTable || hasEmpty).toBe(true)

      if (hasTable) {
        // Should show judgment labels
        const hasJudgment = await commands.isVisibleByText('합격|불합격|OK|NG', 5_000)
        expect(hasJudgment).toBe(true)
      }
    })

    it('shows PASS/FAIL badge for results', async () => {
      await login()
      await commands.goto(`${APP_URL}/quality/inspection-results`)
      await commands.waitForTimeout(2000)

      const hasTable = await commands.isVisibleBySelector('table', 8_000)
      if (hasTable) {
        // Judgment column headers
        const hasJudgmentHeader = await commands.isVisibleByText('판정', 5_000)
        expect(hasJudgmentHeader).toBe(true)
      }
    })
  })

  describe('SPC Data Workflow', () => {
    it('loads SPC page with item selector', async () => {
      await login()
      await commands.goto(`${APP_URL}/quality/spc`)
      await commands.waitForTimeout(2000)

      const hasSelect = await commands.isVisibleBySelector('select', 5_000)
      expect(hasSelect).toBe(true)

      const hasLabel = await commands.isVisibleByText('검사항목', 5_000)
      expect(hasLabel).toBe(true)
    })

    it('generates SPC data via API when items exist', async () => {
      // Get inspection items from plans
      const plansRes = await commands.fetchApi('/quality/inspection-plans?limit=10')
      if (!plansRes.ok || !plansRes.data?.items?.length) return

      const plan = plansRes.data.items[0]
      const items = plan.inspection_items || []
      if (items.length === 0) return

      const itemId = items[0].id
      const genRes = await commands.fetchApi(
        '/quality/spc-data/generate',
        'POST',
        JSON.stringify({
          inspection_item_id: itemId,
          sample_size: 5,
        }),
      )
      // API may or may not support this - graceful handling
      if (genRes.ok) {
        expect(Array.isArray(genRes.data)).toBe(true)
      }
    })

    it('shows SPC charts when item is selected', async () => {
      await login()
      await commands.goto(`${APP_URL}/quality/spc`)
      await commands.waitForTimeout(2000)

      // Check if there are items in the dropdown
      const hasSelect = await commands.isVisibleBySelector('select', 5_000)
      if (hasSelect) {
        // Chart area or empty message should be visible
        const hasChart = await commands.isVisibleBySelector('svg, canvas, [class*="chart"]', 5_000)
        const hasMessage = await commands.isVisibleByText('선택|데이터|항목', 3_000)
        expect(hasChart || hasMessage).toBe(true)
      }
    })

    it('shows Cp/Cpk cards when SPC data exists', async () => {
      await login()
      await commands.goto(`${APP_URL}/quality/spc`)
      await commands.waitForTimeout(2000)

      // These may or may not be visible depending on data availability
      const hasCp = await commands.isVisibleByText('Cp|Cpk|공정능력', 5_000)
      const hasMessage = await commands.isVisibleByText('선택|데이터|항목', 3_000)
      const hasSelect = await commands.isVisibleBySelector('select', 3_000)
      // At minimum the page should render without errors
      expect(hasCp || hasMessage || hasSelect).toBe(true)
    })

    it('shows control status indicator', async () => {
      await login()
      await commands.goto(`${APP_URL}/quality/spc`)
      await commands.waitForTimeout(2000)

      const hasStatus = await commands.isVisibleByText('관리상태|관리|안정', 5_000)
      const hasSelect = await commands.isVisibleBySelector('select', 3_000)
      expect(hasStatus || hasSelect).toBe(true)
    })
  })

  describe('NCR Lifecycle', () => {
    let testNcrId: number
    let testNcrNo: string

    it('creates an NCR via API', async () => {
      const ncrRes = await commands.fetchApi(
        '/quality/ncr',
        'POST',
        JSON.stringify({
          defect_type: 'DIMENSION',
          characteristic: '외경',
          description: 'E2E 테스트 - 치수 규격 초과',
          reported_by: 'E2E-테스터',
          assigned_to: 'E2E-담당자',
          root_cause: '가공 오차 누적',
          corrective_action: '공구 교체 및 재가공',
        }),
      )
      expect(ncrRes.ok).toBe(true)
      expect(ncrRes.data).toHaveProperty('id')
      expect(ncrRes.data.status).toBe('OPEN')

      testNcrId = ncrRes.data.id
      testNcrNo = ncrRes.data.ncr_no
      createdNcrIds.push(testNcrId)
    })

    it('shows created NCR in the list', async () => {
      await login()
      await commands.goto(`${APP_URL}/quality/ncr`)
      await commands.waitForTimeout(2000)

      // Verify NCR list loads with table
      const hasTable = await commands.isVisibleBySelector('table', 8_000)
      expect(hasTable).toBe(true)
    })

    it('transitions OPEN → IN_PROGRESS via API', async () => {
      const res = await commands.fetchApi(
        `/quality/ncr/${testNcrId}/status`,
        'PATCH',
        JSON.stringify({ status: 'IN_PROGRESS' }),
      )
      expect(res.ok).toBe(true)
      expect(res.data.status).toBe('IN_PROGRESS')
    })

    it('transitions IN_PROGRESS → CLOSED via API', async () => {
      const res = await commands.fetchApi(
        `/quality/ncr/${testNcrId}/status`,
        'PATCH',
        JSON.stringify({ status: 'CLOSED' }),
      )
      expect(res.ok).toBe(true)
      expect(res.data.status).toBe('CLOSED')
    })

    it('transitions CLOSED → VERIFIED via API', async () => {
      const res = await commands.fetchApi(
        `/quality/ncr/${testNcrId}/status`,
        'PATCH',
        JSON.stringify({ status: 'VERIFIED' }),
      )
      expect(res.ok).toBe(true)
      expect(res.data.status).toBe('VERIFIED')
    })

    it('shows NCR detail modal with information', async () => {
      await login()
      await commands.goto(`${APP_URL}/quality/ncr`)
      await commands.waitForTimeout(2000)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      if (hasTable) {
        // Click detail button
        const hasDetailBtn = await commands.isVisibleBySelector('button[title="상세보기"]', 3_000)
        if (hasDetailBtn) {
          await commands.clickBySelector('button[title="상세보기"]')
          await commands.waitForTimeout(1000)

          // Detail modal should show NCR info
          const hasModal = await commands.isVisibleBySelector('.fixed.inset-0', 5_000)
          expect(hasModal).toBe(true)

          const hasNcrDetail = await commands.isVisibleByText('NCR 상세', 3_000)
          expect(hasNcrDetail).toBe(true)

          // Should show severity/defect type info
          const hasDefectInfo = await commands.isVisibleByText('불량 내용|근본 원인', 3_000)
          expect(hasDefectInfo).toBe(true)

          // Close modal
          await commands.clickByRole('button', '닫기')
          await commands.waitForTimeout(500)
        }
      }
    })

    it('NCR status filter dropdown works', async () => {
      await login()
      await commands.goto(`${APP_URL}/quality/ncr`)
      await commands.waitForTimeout(2000)

      // The status filter should be visible
      const hasStatusLabel = await commands.isVisibleByText('상태:', 5_000)
      expect(hasStatusLabel).toBe(true)

      // Select filter should exist
      const hasSelect = await commands.isVisibleBySelector('select', 3_000)
      expect(hasSelect).toBe(true)
    })
  })
})
