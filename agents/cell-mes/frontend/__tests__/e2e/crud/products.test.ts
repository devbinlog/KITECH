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

describe('Products CRUD', () => {
  describe('Read: Product list', () => {
    it('loads product management page with heading', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/products`)

      const hasHeading = await commands.isVisibleByRole('heading', '제품 관리')
      expect(hasHeading).toBe(true)
    })

    it('shows product table or empty state', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/products`)
      await commands.waitForTimeout(2000)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      const hasEmpty = await commands.isVisibleByText('등록된 제품이 없습니다', 3_000)

      expect(hasTable || hasEmpty).toBe(true)
    })

    it('shows table column headers when data exists', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/products`)
      await commands.waitForTimeout(2000)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      if (hasTable) {
        const headers = ['제품코드', '제품명', '카테고리', '단위', '등록일', '액션']
        for (const header of headers) {
          const hasHeader = await commands.isVisibleByText(header, 3_000)
          expect(hasHeader).toBe(true)
        }
      }
    })

    it('shows "제품 추가" button', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/products`)

      const hasAddButton = await commands.isVisibleByRole('button', '제품 추가')
      expect(hasAddButton).toBe(true)
    })
  })

  describe('Read: API verification', () => {
    it('GET /products returns valid array', async () => {
      const result = await commands.fetchApi('/masters/products')
      expect(result.ok).toBe(true)
      expect(result.status).toBe(200)
      expect(Array.isArray(result.data)).toBe(true)
    })

    it('product items have required fields', async () => {
      const result = await commands.fetchApi('/masters/products')
      expect(result.ok).toBe(true)

      if (result.data.length > 0) {
        const product = result.data[0]
        expect(product).toHaveProperty('id')
        expect(product).toHaveProperty('code')
        expect(product).toHaveProperty('name')
        expect(product).toHaveProperty('unit')
        expect(product).toHaveProperty('created_at')
      }
    })
  })

  describe('Create: Product creation modal', () => {
    it('opens add product modal when button is clicked', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/products`)
      await commands.waitForTimeout(1000)

      await commands.clickByRole('button', '제품 추가')
      await commands.waitForTimeout(500)

      const hasModal = await commands.isVisibleByText('제품 추가', 5_000)
      expect(hasModal).toBe(true)
    })

    it('shows all form fields in the creation modal', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/products`)
      await commands.waitForTimeout(1000)

      await commands.clickByRole('button', '제품 추가')
      await commands.waitForTimeout(500)

      // Modal overlay
      const hasModal = await commands.isVisibleBySelector('.fixed.inset-0', 5_000)
      expect(hasModal).toBe(true)

      // Labels
      const hasCodeLabel = await commands.isVisibleByText('제품 코드', 3_000)
      expect(hasCodeLabel).toBe(true)

      const hasNameLabel = await commands.isVisibleByText('제품명', 3_000)
      expect(hasNameLabel).toBe(true)

      const hasCategoryLabel = await commands.isVisibleByText('제품 카테고리', 3_000)
      expect(hasCategoryLabel).toBe(true)

      const hasUnitLabel = await commands.isVisibleByText('단위', 3_000)
      expect(hasUnitLabel).toBe(true)

      // Input fields
      const hasInputs = await commands.isVisibleBySelector('input', 3_000)
      expect(hasInputs).toBe(true)

      // Selects for category and unit
      const hasSelect = await commands.isVisibleBySelector('select', 3_000)
      expect(hasSelect).toBe(true)

      // Save and Cancel buttons
      const hasSaveButton = await commands.isVisibleByRole('button', '저장')
      expect(hasSaveButton).toBe(true)

      const hasCancelButton = await commands.isVisibleByRole('button', '취소')
      expect(hasCancelButton).toBe(true)

      await commands.clickByRole('button', '취소')
      await commands.waitForTimeout(500)
    })

    it('prevents submission with empty required fields (HTML5 validation)', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/products`)
      await commands.waitForTimeout(1000)

      await commands.clickByRole('button', '제품 추가')
      await commands.waitForTimeout(500)

      // Try to submit empty form
      await commands.clickByRole('button', '저장')
      await commands.waitForTimeout(500)

      // Modal should still be open (HTML5 validation prevents submission)
      const hasModal = await commands.isVisibleBySelector('.fixed.inset-0', 3_000)
      expect(hasModal).toBe(true)

      await commands.clickByRole('button', '취소')
      await commands.waitForTimeout(500)
    })
  })

  describe('Create & Delete: Full CRUD flow via API', () => {
    it('creates a product via API, verifies in UI, then deletes', async () => {
      const productCode = `VT-${Date.now()}`
      const productName = `Vitest_Product_${Date.now()}`

      // Create via API
      const createResult = await commands.fetchApi(
        '/masters/products',
        'POST',
        JSON.stringify({
          code: productCode,
          name: productName,
          unit: 'EA',
          product_category: 'BRACKET',
        })
      )
      expect(createResult.ok).toBe(true)
      expect(createResult.data).toHaveProperty('id')
      const createdId = createResult.data.id

      // Verify in API list
      const listResult = await commands.fetchApi('/masters/products')
      expect(listResult.ok).toBe(true)
      const found = listResult.data.find((p: any) => p.code === productCode)
      expect(found).toBeDefined()
      expect(found.name).toBe(productName)
      expect(found.unit).toBe('EA')

      // Verify in UI
      await login()
      await commands.goto(`${APP_URL}/master/products`)
      await commands.waitForTimeout(2000)

      const hasCode = await commands.isVisibleByText(productCode, 5_000)
      const hasName = await commands.isVisibleByText(productName, 3_000)
      expect(hasCode || hasName).toBe(true)

      // Delete via API
      const deleteResult = await commands.fetchApi(`/masters/products/${createdId}`, 'DELETE')
      expect(deleteResult.ok).toBe(true)

      // Verify deleted from API
      const afterDelete = await commands.fetchApi('/masters/products')
      const notFound = afterDelete.data.find((p: any) => p.code === productCode)
      expect(notFound).toBeUndefined()
    })
  })

  describe('Update: Edit product via API', () => {
    it('updates product name via API', async () => {
      const code = `VT-UPD-${Date.now()}`

      // Create
      const createResult = await commands.fetchApi(
        '/masters/products',
        'POST',
        JSON.stringify({ code, name: 'Original Name', unit: 'EA' })
      )
      expect(createResult.ok).toBe(true)
      const id = createResult.data.id

      // Update (API uses PATCH, not PUT)
      const updateResult = await commands.fetchApi(
        `/masters/products/${id}`,
        'PATCH',
        JSON.stringify({ name: 'Updated Name', unit: 'SET' })
      )
      expect(updateResult.ok).toBe(true)

      // Verify
      const getResult = await commands.fetchApi(`/masters/products/${id}`)
      expect(getResult.ok).toBe(true)
      expect(getResult.data.name).toBe('Updated Name')
      expect(getResult.data.unit).toBe('SET')

      // Cleanup
      await commands.fetchApi(`/masters/products/${id}`, 'DELETE')
    })
  })

  describe('Sorting', () => {
    it('table has sortable column headers', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/products`)
      await commands.waitForTimeout(2000)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      if (hasTable) {
        // Sortable headers include sort icons (ArrowUpDown or ArrowUp/Down)
        const hasSortableHeaders = await commands.isVisibleBySelector('table th button', 3_000)
        expect(hasSortableHeaders).toBe(true)
      }
    })
  })
})
