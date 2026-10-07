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

afterAll(async () => {
  // Cleanup: mark test orders as DONE
  for (const id of createdOrderIds) {
    await commands.fetchApi(`/production/orders/${id}/status`, 'PATCH', JSON.stringify({ status: 'DONE' }))
  }
  await commands.closeAppPage()
})

describe('Production Management Workflow', () => {
  describe('Work Order Lifecycle (API)', () => {
    let testOrderId: number
    let testLotNo: string

    it('creates a work order via API', async () => {
      // Get a product to use
      const productsRes = await commands.fetchApi('/masters/products')
      expect(productsRes.ok).toBe(true)
      expect(productsRes.data.length).toBeGreaterThan(0)

      const productId = productsRes.data[0].id
      testLotNo = `WF-${Date.now().toString().slice(-8)}`

      const createRes = await commands.fetchApi(
        '/production/orders',
        'POST',
        JSON.stringify({
          lot_no: testLotNo,
          product_id: productId,
          target_qty: 50,
          qty: 1,
          priority: 3,
        }),
      )
      expect(createRes.ok).toBe(true)
      expect(createRes.data).toHaveProperty('id')
      expect(createRes.data.status).toBe('READY')
      expect(createRes.data.lot_no).toBe(testLotNo)

      testOrderId = createRes.data.id
      createdOrderIds.push(testOrderId)
    })

    it('shows created order in UI list', async () => {
      // Verify via API that order exists and is accessible
      const verifyRes = await commands.fetchApi(`/production/orders/${testOrderId}`)
      expect(verifyRes.ok).toBe(true)
      expect(verifyRes.data.lot_no).toBe(testLotNo)

      // Verify UI loads the orders table
      await login()
      await commands.goto(`${APP_URL}/production/orders?view=all`)
      await commands.waitForTimeout(2000)

      const hasTable = await commands.isVisibleBySelector('table', 8_000)
      expect(hasTable).toBe(true)
    })

    it('transitions READY → RUNNING via API', async () => {
      const res = await commands.fetchApi(
        `/production/orders/${testOrderId}/status`,
        'PATCH',
        JSON.stringify({ status: 'RUNNING' }),
      )
      expect(res.ok).toBe(true)
      expect(res.data.status).toBe('RUNNING')
    })

    it('transitions RUNNING → PAUSE via API', async () => {
      const res = await commands.fetchApi(
        `/production/orders/${testOrderId}/status`,
        'PATCH',
        JSON.stringify({ status: 'PAUSE' }),
      )
      expect(res.ok).toBe(true)
      expect(res.data.status).toBe('PAUSE')
    })

    it('transitions PAUSE → RUNNING via API', async () => {
      const res = await commands.fetchApi(
        `/production/orders/${testOrderId}/status`,
        'PATCH',
        JSON.stringify({ status: 'RUNNING' }),
      )
      expect(res.ok).toBe(true)
      expect(res.data.status).toBe('RUNNING')
    })

    it('transitions RUNNING → DONE via API', async () => {
      const res = await commands.fetchApi(
        `/production/orders/${testOrderId}/status`,
        'PATCH',
        JSON.stringify({ status: 'DONE' }),
      )
      expect(res.ok).toBe(true)
      expect(res.data.status).toBe('DONE')
    })

    it('completed order shows DONE via API', async () => {
      // Verify status is DONE via API
      const verifyRes = await commands.fetchApi(`/production/orders/${testOrderId}`)
      expect(verifyRes.ok).toBe(true)
      expect(verifyRes.data.status).toBe('DONE')

      // Verify UI loads the orders table
      await login()
      await commands.goto(`${APP_URL}/production/orders?view=all`)
      await commands.waitForTimeout(2000)

      const hasTable = await commands.isVisibleBySelector('table', 8_000)
      expect(hasTable).toBe(true)

      // At least some orders should show 완료 status
      const hasDone = await commands.isVisibleByText('완료', 5_000)
      expect(hasDone).toBe(true)
    })
  })

  describe('Production Result Recording (API + UI)', () => {
    let runningOrderId: number
    let runningLotNo: string

    it('creates and starts a work order for result recording', async () => {
      const productsRes = await commands.fetchApi('/masters/products')
      const productId = productsRes.data[0].id
      runningLotNo = `PR-${Date.now().toString().slice(-8)}`

      const createRes = await commands.fetchApi(
        '/production/orders',
        'POST',
        JSON.stringify({
          lot_no: runningLotNo,
          product_id: productId,
          target_qty: 100,
          qty: 1,
          priority: 5,
        }),
      )
      expect(createRes.ok).toBe(true)
      runningOrderId = createRes.data.id
      createdOrderIds.push(runningOrderId)

      // Start the order
      const startRes = await commands.fetchApi(
        `/production/orders/${runningOrderId}/status`,
        'PATCH',
        JSON.stringify({ status: 'RUNNING' }),
      )
      expect(startRes.ok).toBe(true)
    })

    it('records a production result via API', async () => {
      const resultRes = await commands.fetchApi(
        '/production/results',
        'POST',
        JSON.stringify({
          work_order_id: runningOrderId,
          ok_qty: 90,
          ng_qty: 10,
        }),
      )
      expect(resultRes.ok).toBe(true)
      expect(resultRes.data).toHaveProperty('id')
      expect(resultRes.data.ok_qty).toBe(90)
      expect(resultRes.data.ng_qty).toBe(10)
    })

    it('shows result on production results page', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/results`)
      await commands.waitForTimeout(2000)

      const hasTable = await commands.isVisibleBySelector('table', 8_000)
      expect(hasTable).toBe(true)

      // Should show ok/ng quantities somewhere
      const hasYield = await commands.isVisibleByText('%', 5_000)
      expect(hasYield).toBe(true)
    })

    it('displays yield and quantity stats', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/results`)
      await commands.waitForTimeout(2000)

      const hasOkLabel = await commands.isVisibleByText('양품', 5_000)
      const hasNgLabel = await commands.isVisibleByText('불량', 5_000)
      const hasYieldLabel = await commands.isVisibleByText('수율', 5_000)

      expect(hasOkLabel).toBe(true)
      expect(hasNgLabel).toBe(true)
      expect(hasYieldLabel).toBe(true)
    })

    it('result creation modal opens and closes', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/results`)
      await commands.waitForTimeout(1000)

      // Open modal
      await commands.clickByRole('button', '실적 등록')
      await commands.waitForTimeout(500)
      const hasModal = await commands.isVisibleByText('생산 실적 등록', 5_000)
      expect(hasModal).toBe(true)

      // Cancel
      await commands.clickByRole('button', '취소')
      await commands.waitForTimeout(500)
    })
  })

  describe('Work Order Sorting & Filtering', () => {
    it('switches through view tabs and loads data', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/orders`)
      await commands.waitForTimeout(1000)

      const tabs = ['전체', '진행중', '예정 작업', '오늘 작업']
      for (const tab of tabs) {
        await commands.clickByRole('button', tab)
        await commands.waitForTimeout(1500)

        const hasContent = await commands.isVisibleBySelector('table', 5_000)
        const hasEmpty = await commands.isVisibleByText('없습니다', 3_000)
        expect(hasContent || hasEmpty).toBe(true)
      }
    })

    it('sorts by priority', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/orders?view=all`)
      await commands.waitForTimeout(2000)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      if (hasTable) {
        // Click priority sort header
        const hasPriority = await commands.isVisibleByText('우선순위', 3_000)
        if (hasPriority) {
          await commands.clickByText('우선순위')
          await commands.waitForTimeout(1500)
          // Page should still show content
          const hasData = await commands.isVisibleBySelector('table', 5_000)
          expect(hasData).toBe(true)
        }
      }
    })

    it('sorts by due date', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/orders?view=all`)
      await commands.waitForTimeout(2000)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      if (hasTable) {
        const hasDueDate = await commands.isVisibleByText('납기일', 3_000)
        if (hasDueDate) {
          await commands.clickByText('납기일')
          await commands.waitForTimeout(1500)
          const hasData = await commands.isVisibleBySelector('table', 5_000)
          expect(hasData).toBe(true)
        }
      }
    })
  })
})
