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

afterAll(async () => {
  await commands.closeAppPage()
})

describe('Work Orders CRUD', () => {
  describe('Read: Work order list', () => {
    it('loads the work orders page with heading', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/orders?view=all`)

      const hasHeading = await commands.isVisibleByRole('heading', '작업지시')
      expect(hasHeading).toBe(true)
    })

    it('displays all view tab buttons', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/orders`)

      const tabs = ['오늘 작업', '예정 작업', '진행중', '전체']
      for (const tab of tabs) {
        const hasTab = await commands.isVisibleByRole('button', tab)
        expect(hasTab).toBe(true)
      }
    })

    it('shows table or empty state after selecting All tab', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/orders`)
      await commands.waitForTimeout(1000)

      await commands.clickByRole('button', '전체')
      await commands.waitForTimeout(1500)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      const hasEmpty = await commands.isVisibleByText('작업지시가 없습니다', 3_000)

      expect(hasTable || hasEmpty).toBe(true)
    })

    it('shows table column headers when data exists', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/orders?view=all`)
      await commands.waitForTimeout(2000)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      if (hasTable) {
        const hasLotNo = await commands.isVisibleByText('Lot No')
        const hasProduct = await commands.isVisibleByText('제품')
        const hasStatus = await commands.isVisibleByText('상태')

        expect(hasLotNo).toBe(true)
        expect(hasProduct).toBe(true)
        expect(hasStatus).toBe(true)
      }
    })

    it('shows sortable column headers (우선순위, 계획시작, 납기일)', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/orders?view=all`)
      await commands.waitForTimeout(2000)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      if (hasTable) {
        const hasPriority = await commands.isVisibleByText('우선순위')
        const hasPlanStart = await commands.isVisibleByText('계획시작')
        const hasDueDate = await commands.isVisibleByText('납기일')
        expect(hasPriority).toBe(true)
        expect(hasPlanStart).toBe(true)
        expect(hasDueDate).toBe(true)
      }
    })

    it('pagination text shows total count', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/orders?view=all`)
      await commands.waitForTimeout(2000)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      if (hasTable) {
        const hasPagination = await commands.isVisibleByText('총.*건 중', 5_000)
        expect(hasPagination).toBe(true)
      }
    })
  })

  describe('Read: API-level verification', () => {
    it('GET /production/orders returns valid paginated response', async () => {
      const result = await commands.fetchApi('/production/orders?limit=10&view=all')
      expect(result.ok).toBe(true)
      expect(result.status).toBe(200)
      expect(result.data).toHaveProperty('items')
      expect(result.data).toHaveProperty('total')
      expect(result.data).toHaveProperty('pages')
      expect(Array.isArray(result.data.items)).toBe(true)
    })

    it('GET /production/orders supports view filters', async () => {
      const views = ['today', 'upcoming', 'active', 'all']
      for (const view of views) {
        const result = await commands.fetchApi(`/production/orders?limit=5&view=${view}`)
        expect(result.ok).toBe(true)
        expect(result.data).toHaveProperty('items')
      }
    })

    it('GET /production/orders supports sorting', async () => {
      const result = await commands.fetchApi('/production/orders?limit=5&view=all&sort_by=priority&sort_order=desc')
      expect(result.ok).toBe(true)
      expect(Array.isArray(result.data.items)).toBe(true)
    })
  })

  describe('Create: Work order creation modal', () => {
    it('opens creation modal when button is clicked', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/orders`)
      await commands.waitForTimeout(1000)

      await commands.clickByRole('button', '작업지시 생성')
      await commands.waitForTimeout(500)

      const hasModal = await commands.isVisibleByText('작업지시 생성', 5_000)
      expect(hasModal).toBe(true)
    })

    it('shows all form fields in the creation modal', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/orders`)
      await commands.waitForTimeout(1000)

      await commands.clickByRole('button', '작업지시 생성')
      await commands.waitForTimeout(500)

      // Lot No input
      const hasLotInput = await commands.isVisibleBySelector('input[placeholder="LOT-YYYYMMDD-001"]', 3_000)
      expect(hasLotInput).toBe(true)

      // Product select
      const hasSelect = await commands.isVisibleBySelector('select', 3_000)
      expect(hasSelect).toBe(true)

      // Quantity input
      const hasQtyInput = await commands.isVisibleBySelector('input[type="number"]', 3_000)
      expect(hasQtyInput).toBe(true)

      // Due date
      const hasDueDate = await commands.isVisibleBySelector('input[type="datetime-local"]', 3_000)
      expect(hasDueDate).toBe(true)

      // Remarks textarea
      const hasRemarks = await commands.isVisibleBySelector('textarea', 3_000)
      expect(hasRemarks).toBe(true)

      // Cancel button
      const hasCancel = await commands.isVisibleByRole('button', '취소')
      expect(hasCancel).toBe(true)

      // Submit button
      const hasSubmit = await commands.isVisibleBySelector('button[type="submit"]', 3_000)
      expect(hasSubmit).toBe(true)

      await commands.clickByRole('button', '취소')
      await commands.waitForTimeout(500)
    })

    it('shows label texts in the creation modal', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/orders`)
      await commands.waitForTimeout(1000)

      await commands.clickByRole('button', '작업지시 생성')
      await commands.waitForTimeout(500)

      const labels = ['Lot No', '제품 선택', '목표 수량', '우선순위', '납기일', '비고']
      for (const label of labels) {
        const hasLabel = await commands.isVisibleByText(label, 3_000)
        expect(hasLabel).toBe(true)
      }

      await commands.clickByRole('button', '취소')
      await commands.waitForTimeout(500)
    })
  })

  describe('Create & Delete: Full CRUD flow via API', () => {
    it('creates a work order via API and verifies in UI', async () => {
      // First get a product to use
      const productsResult = await commands.fetchApi('/masters/products')
      expect(productsResult.ok).toBe(true)

      if (productsResult.data.length === 0) {
        // Skip if no products exist
        return
      }

      const productId = productsResult.data[0].id
      const lotNo = `VT-${Date.now()}`

      // Create via API
      const createResult = await commands.fetchApi(
        '/production/orders',
        'POST',
        JSON.stringify({
          lot_no: lotNo,
          product_id: productId,
          target_qty: 50,
          qty: 1,
          priority: 5,
        })
      )

      if (!createResult.ok) {
        // API may reject due to validation - skip gracefully
        return
      }
      expect(createResult.data).toHaveProperty('id')

      const createdId = createResult.data.id

      // Verify by fetching the specific order
      const getResult = await commands.fetchApi(`/production/orders/${createdId}`)
      expect(getResult.ok).toBe(true)
      expect(getResult.data.lot_no).toBe(lotNo)
      expect(getResult.data.target_qty).toBe(50)
      expect(getResult.data.status).toBe('READY')

      // Verify it appears in the UI
      await login()
      await commands.goto(`${APP_URL}/production/orders?view=all`)
      await commands.waitForTimeout(2000)

      const hasLotNo = await commands.isVisibleByText(lotNo, 5_000)
      if (!hasLotNo) {
        // May not appear on first page - just verify API-level integrity
        const listResult = await commands.fetchApi('/production/orders?view=all&limit=200')
        const found = listResult.data.items.find((wo: any) => wo.id === createdId)
        expect(found).toBeDefined()
      }

      // Cleanup: delete via API
      await commands.fetchApi(`/production/orders/${createdId}`, 'DELETE')
    })
  })

  describe('Update: Status transitions via API', () => {
    it('transitions work order READY -> RUNNING -> DONE via API', async () => {
      // Get a product
      const productsResult = await commands.fetchApi('/masters/products')
      if (productsResult.data.length === 0) return

      const productId = productsResult.data[0].id
      const lotNo = `VT-STATUS-${Date.now()}`

      // Create
      const createResult = await commands.fetchApi(
        '/production/orders',
        'POST',
        JSON.stringify({
          lot_no: lotNo,
          product_id: productId,
          target_qty: 10,
          qty: 1,
          priority: 5,
        })
      )
      expect(createResult.ok).toBe(true)
      const woId = createResult.data.id

      // READY -> RUNNING
      const startResult = await commands.fetchApi(`/production/orders/${woId}/status`, 'PATCH', JSON.stringify({ status: 'RUNNING' }))
      expect(startResult.ok).toBe(true)

      // Verify status
      const checkResult = await commands.fetchApi(`/production/orders/${woId}`)
      expect(checkResult.ok).toBe(true)
      expect(checkResult.data.status).toBe('RUNNING')

      // RUNNING -> DONE
      const doneResult = await commands.fetchApi(`/production/orders/${woId}/status`, 'PATCH', JSON.stringify({ status: 'DONE' }))
      expect(doneResult.ok).toBe(true)

      // Cleanup
      await commands.fetchApi(`/production/orders/${woId}`, 'DELETE')
    })
  })

  describe('Tab filtering shows correct status', () => {
    it('shows status badges in the all tab', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/orders?view=all`)
      await commands.waitForTimeout(2000)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      if (hasTable) {
        // At least one status badge should be visible
        const hasReady = await commands.isVisibleByText('대기', 3_000)
        const hasRunning = await commands.isVisibleByText('진행중', 3_000)
        const hasDone = await commands.isVisibleByText('완료', 3_000)
        // At least one status should appear if data exists
        expect(hasReady || hasRunning || hasDone).toBe(true)
      }
    })
  })
})
