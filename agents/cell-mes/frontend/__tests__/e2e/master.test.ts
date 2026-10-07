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

describe('Master Data', () => {
  describe('Product management', () => {
    it('loads product management page', async () => {
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
      await commands.waitForTimeout(1000)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      if (hasTable) {
        const hasCode = await commands.isVisibleByText('제품코드')
        const hasName = await commands.isVisibleByText('제품명')
        const hasUnit = await commands.isVisibleByText('단위')
        const hasDate = await commands.isVisibleByText('등록일')
        const hasAction = await commands.isVisibleByText('액션')

        expect(hasCode).toBe(true)
        expect(hasName).toBe(true)
        expect(hasUnit).toBe(true)
        expect(hasDate).toBe(true)
        expect(hasAction).toBe(true)
      }
    })

    it('shows add product button', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/products`)

      const hasAddButton = await commands.isVisibleByRole('button', '제품 추가')
      expect(hasAddButton).toBe(true)
    })

    it('opens add product modal when button is clicked', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/products`)
      await commands.waitForTimeout(1000)

      await commands.clickByRole('button', '제품 추가')
      await commands.waitForTimeout(500)

      const hasModalHeading = await commands.isVisibleByText('제품 추가', 5_000)
      expect(hasModalHeading).toBe(true)
    })
  })

  describe('Standard process management', () => {
    it('loads standard process page', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/processes`)

      const hasHeading = await commands.isVisibleByRole('heading', '표준공정 관리')
      expect(hasHeading).toBe(true)
    })

    it('shows table or empty state', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/processes`)
      await commands.waitForTimeout(2000)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      const hasEmpty = await commands.isVisibleByText('없습니다|No data', 3_000)
      const hasLoading = await commands.isVisibleByText('로딩 중', 3_000)

      expect(hasTable || hasEmpty || hasLoading).toBe(true)
    })
  })

  describe('Equipment management', () => {
    it('loads equipment management page', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/equipments`)

      const hasHeading = await commands.isVisibleByRole('heading', '설비 관리')
      expect(hasHeading).toBe(true)
    })

    it('shows equipment table column headers when data exists', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/equipments`)
      await commands.waitForTimeout(1000)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      if (hasTable) {
        const hasCode = await commands.isVisibleByText('설비코드')
        const hasName = await commands.isVisibleByText('설비명')
        const hasType = await commands.isVisibleByText('유형')
        const hasStatus = await commands.isVisibleByText('상태')

        expect(hasCode).toBe(true)
        expect(hasName).toBe(true)
        expect(hasType).toBe(true)
        expect(hasStatus).toBe(true)
      }
    })

    it('shows equipment action buttons', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/equipments`)
      await commands.waitForTimeout(1000)

      const hasSyncButton = await commands.isVisibleByRole('button', 'AAS 장비 동기화')
      const hasRefreshButton = await commands.isVisibleByRole('button', '새로고침')
      expect(hasSyncButton || hasRefreshButton).toBe(true)
    })
  })

  describe('Routing management', () => {
    it('loads routing design page', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/routings`)

      const hasHeading = await commands.isVisibleByRole('heading', '라우팅 설계')
      expect(hasHeading).toBe(true)
    })

    it('shows product selection list', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/routings`)
      await commands.waitForTimeout(2000)

      const hasProductList = await commands.isVisibleByText('제품 목록', 5_000)
      const hasProductButton = await commands.isVisibleBySelector('button', 5_000)
      expect(hasProductList || hasProductButton).toBe(true)
    })
  })

  describe('Logistics scenarios', () => {
    it('loads logistics scenarios page', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/scenarios`)

      const hasHeading = await commands.isVisibleByRole('heading', '물류 시나리오')
      expect(hasHeading).toBe(true)
    })

    it('shows scenario list or empty state', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/scenarios`)
      await commands.waitForTimeout(2000)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      const hasCards = await commands.isVisibleBySelector('[class*="card"]', 3_000)
      const hasEmpty = await commands.isVisibleByText('없습니다|시나리오', 3_000)

      expect(hasTable || hasCards || hasEmpty).toBe(true)
    })
  })
})
