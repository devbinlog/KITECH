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

describe('Production', () => {
  describe('Work order list', () => {
    it('loads work orders page with heading', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/orders`)

      const hasHeading = await commands.isVisibleByRole('heading', '작업지시')
      expect(hasHeading).toBe(true)
    })

    it('shows loading state then content or empty', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/orders`)

      // Either table or empty message should eventually be visible
      const hasTable = await commands.isVisibleBySelector('table', 8_000)
      const hasEmpty = await commands.isVisibleByText('없습니다', 3_000)

      expect(hasTable || hasEmpty).toBe(true)
    })

    it('displays all four view tab buttons', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/orders`)

      const tabs = ['오늘 작업', '예정 작업', '진행중', '전체']
      for (const tab of tabs) {
        const hasTab = await commands.isVisibleByRole('button', tab)
        expect(hasTab).toBe(true)
      }
    })

    it('switches tabs and loads content for each tab', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/orders`)
      await commands.waitForTimeout(1000)

      const tabs = ['전체', '진행중', '예정 작업', '오늘 작업']
      for (const tab of tabs) {
        await commands.clickByRole('button', tab)
        await commands.waitForTimeout(1000)

        // After tab switch, page should show content (table or empty)
        const hasTable = await commands.isVisibleBySelector('table', 5_000)
        const hasEmpty = await commands.isVisibleByText('없습니다', 3_000)
        const hasHeading = await commands.isVisibleByRole('heading', '작업지시')
        expect(hasTable || hasEmpty).toBe(true)
        expect(hasHeading).toBe(true)
      }
    })

    it('shows correct table column headers when data exists', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/orders?view=all`)
      await commands.waitForTimeout(2000)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      if (hasTable) {
        const headers = ['Lot No', '제품', '목표수량', '상태']
        for (const header of headers) {
          const hasHeader = await commands.isVisibleByText(header)
          expect(hasHeader).toBe(true)
        }
      }
    })

    it('shows "작업지시 생성" button in header', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/orders`)

      const hasCreateBtn = await commands.isVisibleByRole('button', '작업지시 생성')
      expect(hasCreateBtn).toBe(true)
    })
  })

  describe('Work order creation modal', () => {
    it('opens creation modal with all expected form fields', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/orders`)
      await commands.waitForTimeout(1000)

      await commands.clickByRole('button', '작업지시 생성')
      await commands.waitForTimeout(500)

      // Modal heading should appear
      const hasModalHeading = await commands.isVisibleByText('작업지시 생성', 5_000)
      expect(hasModalHeading).toBe(true)

      // Check form fields exist
      const hasLotInput = await commands.isVisibleBySelector('input[placeholder="LOT-YYYYMMDD-001"]', 3_000)
      expect(hasLotInput).toBe(true)

      const hasSelect = await commands.isVisibleBySelector('select', 3_000)
      expect(hasSelect).toBe(true)

      const hasNumberInput = await commands.isVisibleBySelector('input[type="number"]', 3_000)
      expect(hasNumberInput).toBe(true)

      // Check buttons
      const hasCancelBtn = await commands.isVisibleByRole('button', '취소')
      expect(hasCancelBtn).toBe(true)

      const hasSubmitBtn = await commands.isVisibleBySelector('button[type="submit"]', 3_000)
      expect(hasSubmitBtn).toBe(true)

      // Close the modal
      await commands.clickByRole('button', '취소')
      await commands.waitForTimeout(500)
    })

    it('closes modal when cancel button is clicked', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/orders`)
      await commands.waitForTimeout(1000)

      await commands.clickByRole('button', '작업지시 생성')
      await commands.waitForTimeout(500)

      // Modal should be visible
      const hasModal = await commands.isVisibleBySelector('.fixed.inset-0', 3_000)
      expect(hasModal).toBe(true)

      // Click cancel
      await commands.clickByRole('button', '취소')
      await commands.waitForTimeout(500)

      // Modal should no longer be visible (heading reverts to page heading)
      const hasHeading = await commands.isVisibleByRole('heading', '작업지시')
      expect(hasHeading).toBe(true)
    })
  })

  describe('Work orders API verification', () => {
    it('API returns valid work orders list', async () => {
      const result = await commands.fetchApi('/production/orders?limit=5&view=all')
      expect(result.ok).toBe(true)
      expect(result.status).toBe(200)
      expect(result.data).toHaveProperty('items')
      expect(result.data).toHaveProperty('total')
      expect(Array.isArray(result.data.items)).toBe(true)
    })

    it('API returns products list for dropdown', async () => {
      const result = await commands.fetchApi('/masters/products')
      expect(result.ok).toBe(true)
      expect(result.status).toBe(200)
      expect(Array.isArray(result.data)).toBe(true)
    })
  })

  describe('Production results page', () => {
    it('loads production results with heading', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/results`)

      const hasHeading = await commands.isVisibleByRole('heading', '생산 실적')
      expect(hasHeading).toBe(true)
    })

    it('displays all four statistics cards', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/results`)
      await commands.waitForTimeout(2000)

      const cards = ['총 실적 건수', '양품 수량', '불량 수량', '수율']
      for (const card of cards) {
        const hasCard = await commands.isVisibleByText(card, 5_000)
        expect(hasCard).toBe(true)
      }
    })

    it('displays yield percentage with % sign', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/results`)
      await commands.waitForTimeout(2000)

      const hasPercent = await commands.isVisibleByText('%', 5_000)
      expect(hasPercent).toBe(true)
    })

    it('shows table with correct headers or empty state', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/results`)
      await commands.waitForTimeout(2000)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      const hasEmpty = await commands.isVisibleByText('생산 실적이 없습니다', 3_000)
      expect(hasTable || hasEmpty).toBe(true)

      if (hasTable) {
        const headers = ['Lot No', '양품', '불량', '수율']
        for (const header of headers) {
          const hasHeader = await commands.isVisibleByText(header, 3_000)
          expect(hasHeader).toBe(true)
        }
      }
    })

    it('shows "실적 등록" button', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/results`)

      const hasBtn = await commands.isVisibleByRole('button', '실적 등록')
      expect(hasBtn).toBe(true)
    })

    it('opens create result modal with form fields', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/results`)
      await commands.waitForTimeout(1000)

      await commands.clickByRole('button', '실적 등록')
      await commands.waitForTimeout(500)

      const hasModalTitle = await commands.isVisibleByText('생산 실적 등록', 5_000)
      expect(hasModalTitle).toBe(true)

      const hasWorkOrderSelect = await commands.isVisibleBySelector('select', 3_000)
      expect(hasWorkOrderSelect).toBe(true)

      const hasOkQtyInput = await commands.isVisibleBySelector('input[type="number"]', 3_000)
      expect(hasOkQtyInput).toBe(true)

      // Close modal
      await commands.clickByRole('button', '취소')
      await commands.waitForTimeout(500)
    })

    it('API returns valid results list', async () => {
      const result = await commands.fetchApi('/production/results?limit=5')
      expect(result.ok).toBe(true)
      expect(result.status).toBe(200)
      expect(result.data).toHaveProperty('items')
      expect(result.data).toHaveProperty('total')
    })
  })

  describe('Pagination', () => {
    it('shows pagination controls when data exists on orders page', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/orders?view=all`)
      await commands.waitForTimeout(2000)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      if (hasTable) {
        // Pagination text "총 N건 중"
        const hasPaginationText = await commands.isVisibleByText('총.*건 중', 5_000)
        expect(hasPaginationText).toBe(true)
      }
    })
  })
})
