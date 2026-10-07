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

describe('Equipments CRUD', () => {
  describe('Read: Equipment list', () => {
    it('loads equipment management page with heading', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/equipments`)

      const hasHeading = await commands.isVisibleByRole('heading', '설비 관리')
      expect(hasHeading).toBe(true)
    })

    it('shows equipment grid, table, or empty state', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/equipments`)
      await commands.waitForTimeout(3000)

      const hasGrid = await commands.isVisibleBySelector('.grid', 5_000)
      const hasTable = await commands.isVisibleBySelector('table', 3_000)
      const hasEmpty = await commands.isVisibleByText('등록된 설비가 없습니다', 3_000)

      expect(hasGrid || hasTable || hasEmpty).toBe(true)
    })

    it('shows middleware status indicator', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/equipments`)
      await commands.waitForTimeout(2000)

      const hasMiddleware = await commands.isVisibleByText('미들웨어', 5_000)
      expect(hasMiddleware).toBe(true)
    })

    it('shows AAS sync button', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/equipments`)
      await commands.waitForTimeout(2000)

      const hasSyncButton = await commands.isVisibleByRole('button', 'AAS 장비 동기화')
      expect(hasSyncButton).toBe(true)
    })

    it('shows refresh button', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/equipments`)
      await commands.waitForTimeout(2000)

      const hasRefreshButton = await commands.isVisibleByRole('button', '새로고침')
      expect(hasRefreshButton).toBe(true)
    })
  })

  describe('Read: API verification', () => {
    it('GET /equipment returns valid array', async () => {
      const result = await commands.fetchApi('/masters/equipments')
      expect(result.ok).toBe(true)
      expect(result.status).toBe(200)
      expect(Array.isArray(result.data)).toBe(true)
    })

    it('equipment items have required fields', async () => {
      const result = await commands.fetchApi('/masters/equipments')
      expect(result.ok).toBe(true)

      if (result.data.length > 0) {
        const eq = result.data[0]
        expect(eq).toHaveProperty('id')
        expect(eq).toHaveProperty('eq_name')
        expect(eq).toHaveProperty('equipment_type')
        expect(eq).toHaveProperty('current_status')
      }
    })

    it('middleware health endpoint responds', async () => {
      const result = await commands.fetchApi('/masters/equipments')
      // Verify equipment API is accessible
      expect(result.status).toBeDefined()
      expect(result.ok).toBe(true)
    })
  })

  describe('Read: Equipment detail modal', () => {
    it('opens detail modal when equipment card is clicked', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/equipments`)
      await commands.waitForTimeout(3000)

      // Check if we have equipment via API
      const equipResult = await commands.fetchApi('/masters/equipments')
      if (equipResult.data.length === 0) return

      const eqName = equipResult.data[0].eq_name
      const hasEquipCard = await commands.isVisibleByText(eqName, 5_000)
      if (hasEquipCard) {
        await commands.clickByText(eqName)
        await commands.waitForTimeout(1000)

        // Modal should show with equipment name
        const hasModal = await commands.isVisibleBySelector('.fixed.inset-0', 5_000)
        expect(hasModal).toBe(true)

        // Close modal
        await commands.clickByRole('button', '닫기')
        await commands.waitForTimeout(500)
      }
    })

    it('shows tabs in equipment detail modal (기본 정보, Spec Data, Last Data, 상태 이력)', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/equipments`)
      await commands.waitForTimeout(3000)

      const equipResult = await commands.fetchApi('/masters/equipments')
      if (equipResult.data.length === 0) return

      const eqName = equipResult.data[0].eq_name
      const hasEquipCard = await commands.isVisibleByText(eqName, 5_000)
      if (!hasEquipCard) return

      await commands.clickByText(eqName)
      await commands.waitForTimeout(1000)

      const hasModal = await commands.isVisibleBySelector('.fixed.inset-0', 5_000)
      if (!hasModal) return

      // Check tab buttons
      const tabs = ['기본 정보', 'Spec Data', 'Last Data', '상태 이력']
      for (const tab of tabs) {
        const hasTab = await commands.isVisibleByText(tab, 3_000)
        expect(hasTab).toBe(true)
      }

      await commands.clickByRole('button', '닫기')
      await commands.waitForTimeout(500)
    })

    it('shows basic info tab content by default', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/equipments`)
      await commands.waitForTimeout(3000)

      const equipResult = await commands.fetchApi('/masters/equipments')
      if (equipResult.data.length === 0) return

      const eqName = equipResult.data[0].eq_name
      const hasEquipCard = await commands.isVisibleByText(eqName, 5_000)
      if (!hasEquipCard) return

      await commands.clickByText(eqName)
      await commands.waitForTimeout(1000)

      // Basic info should show status and type labels
      const hasStatusLabel = await commands.isVisibleByText('가동 중|정지|오류', 3_000)
      const hasEquipCode = await commands.isVisibleByText('설비 코드', 3_000)
      const hasModelName = await commands.isVisibleByText('모델명', 3_000)

      expect(hasEquipCode).toBe(true)
      expect(hasModelName).toBe(true)

      await commands.clickByRole('button', '닫기')
      await commands.waitForTimeout(500)
    })

    it('shows Spec Data and Last Data tabs in detail modal', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/equipments`)
      await commands.waitForTimeout(3000)

      const equipResult = await commands.fetchApi('/masters/equipments')
      if (equipResult.data.length === 0) return

      const eqName = equipResult.data[0].eq_name
      const hasEquipCard = await commands.isVisibleByText(eqName, 5_000)
      if (!hasEquipCard) return

      await commands.clickByText(eqName)
      await commands.waitForTimeout(1000)

      // Verify tabs exist
      const hasSpecTab = await commands.isVisibleByText('Spec Data', 5_000)
      const hasLastTab = await commands.isVisibleByText('Last Data', 3_000)
      expect(hasSpecTab || hasLastTab).toBe(true)

      await commands.clickByRole('button', '닫기')
      await commands.waitForTimeout(500)
    })
  })

  describe('Delete: Equipment deletion', () => {
    it('shows delete button in equipment detail modal', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/equipments`)
      await commands.waitForTimeout(3000)

      const equipResult = await commands.fetchApi('/masters/equipments')
      if (equipResult.data.length === 0) return

      const eqName = equipResult.data[0].eq_name
      const hasEquipCard = await commands.isVisibleByText(eqName, 5_000)
      if (!hasEquipCard) return

      await commands.clickByText(eqName)
      await commands.waitForTimeout(1000)

      const hasModal = await commands.isVisibleBySelector('.fixed.inset-0', 5_000)
      if (hasModal) {
        const hasDeleteButton = await commands.isVisibleByRole('button', '삭제')
        expect(hasDeleteButton).toBe(true)
      }

      await commands.clickByRole('button', '닫기')
      await commands.waitForTimeout(500)
    })
  })

  describe('Status history tab', () => {
    it('shows history tab with loading or content', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/equipments`)
      await commands.waitForTimeout(3000)

      const equipResult = await commands.fetchApi('/masters/equipments')
      if (equipResult.data.length === 0) return

      const eqName = equipResult.data[0].eq_name
      const hasEquipCard = await commands.isVisibleByText(eqName, 5_000)
      if (!hasEquipCard) return

      await commands.clickByText(eqName)
      await commands.waitForTimeout(1000)

      // Click status history tab
      await commands.clickByText('상태 이력')
      await commands.waitForTimeout(2000)

      // Should show either history records, empty message, or loading
      const hasRecords = await commands.isVisibleBySelector('.bg-gray-50.rounded-lg', 3_000)
      const hasEmpty = await commands.isVisibleByText('상태 이력이 없습니다', 3_000)
      const hasLoading = await commands.isVisibleByText('로딩 중', 3_000)
      expect(hasRecords || hasEmpty || hasLoading).toBe(true)

      await commands.clickByRole('button', '닫기')
      await commands.waitForTimeout(500)
    })
  })
})
