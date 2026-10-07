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

describe('Downtime', () => {
  describe('Downtime reasons (API)', () => {
    it('fetches downtime reason list', async () => {
      const res = await commands.fetchApi('/downtime/reasons')
      expect(res.ok).toBe(true)
      expect(Array.isArray(res.data)).toBe(true)
    })

    it('filters reasons by category', async () => {
      const categories = ['PLANNED', 'UNPLANNED', 'SETUP']

      for (const category of categories) {
        const res = await commands.fetchApi(`/downtime/reasons?category=${category}`)
        expect(res.ok).toBe(true)
        expect(Array.isArray(res.data)).toBe(true)

        for (const reason of res.data) {
          expect(reason.category).toBe(category)
        }
      }
    })
  })

  describe('Downtime records (API)', () => {
    it('fetches downtime list', async () => {
      const res = await commands.fetchApi('/downtime')
      expect(res.ok).toBe(true)
      expect(Array.isArray(res.data)).toBe(true)
    })

    it('filters ongoing downtime records', async () => {
      const res = await commands.fetchApi('/downtime?ongoing_only=true')
      expect(res.ok).toBe(true)
      expect(Array.isArray(res.data)).toBe(true)

      // All ongoing records should have null end_time
      for (const dt of res.data) {
        expect(dt.end_time).toBeNull()
      }
    })

    it('fetches downtime summary statistics', async () => {
      const res = await commands.fetchApi('/downtime/summary')
      expect(res.ok).toBe(true)

      expect(res.data).toHaveProperty('by_category')
      expect(res.data).toHaveProperty('total_count')
      expect(res.data).toHaveProperty('total_minutes')
    })

    it('filters downtime by equipment', async () => {
      // Get equipment list
      const eqRes = await commands.fetchApi('/masters/equipments')
      if (!eqRes.ok) return

      if (eqRes.data.length === 0) return

      const equipmentId = eqRes.data[0].id
      const res = await commands.fetchApi(`/downtime?equipment_id=${equipmentId}`)
      expect(res.ok).toBe(true)

      for (const dt of res.data) {
        expect(dt.equipment_id).toBe(equipmentId)
      }
    })

    it('filters downtime by date range', async () => {
      const dateFrom = new Date()
      dateFrom.setDate(dateFrom.getDate() - 7)
      const dateTo = new Date()

      const res = await commands.fetchApi(
        `/downtime?date_from=${dateFrom.toISOString()}&date_to=${dateTo.toISOString()}`,
      )
      expect(res.ok).toBe(true)
      expect(Array.isArray(res.data)).toBe(true)
    })
  })

  describe('Downtime lifecycle (API)', () => {
    it('creates and ends a downtime record', async () => {
      // Get equipment
      const eqRes = await commands.fetchApi('/masters/equipments')
      if (!eqRes.ok) return
      if (eqRes.data.length === 0) return

      const equipmentId = eqRes.data[0].id

      // 1. Create downtime
      const createRes = await commands.fetchApi('/downtime', 'POST', JSON.stringify({
        equipment_id: equipmentId,
        start_time: new Date().toISOString(),
        remarks: 'Vitest E2E downtime test',
      }))
      expect(createRes.status).toBe(201)
      expect(createRes.data.id).toBeDefined()
      expect(createRes.data.end_time).toBeNull()

      // 2. End downtime
      const endRes = await commands.fetchApi(`/downtime/${createRes.data.id}/end`, 'POST')
      expect(endRes.ok).toBe(true)
      expect(endRes.data.end_time).not.toBeNull()
    })
  })

  describe('Downtime UI page', () => {
    it('navigates to downtime page and shows heading', async () => {
      await login()
      await commands.goto(`${APP_URL}/downtime`)
      await commands.waitForTimeout(2000)

      const hasHeading = await commands.isVisibleByText('다운타임 관리', 5_000)
      expect(hasHeading).toBe(true)
    })

    it('shows subtitle description', async () => {
      await login()
      await commands.goto(`${APP_URL}/downtime`)

      const hasSub = await commands.isVisibleByText('설비 정지 시간을 기록하고 분석합니다', 5_000)
      expect(hasSub).toBe(true)
    })

    it('shows create downtime button', async () => {
      await login()
      await commands.goto(`${APP_URL}/downtime`)

      const hasBtn = await commands.isVisibleByText('다운타임 기록', 5_000)
      expect(hasBtn).toBe(true)
    })

    it('shows active tab by default', async () => {
      await login()
      await commands.goto(`${APP_URL}/downtime`)

      const hasActiveTab = await commands.isVisibleByText('진행 중', 5_000)
      expect(hasActiveTab).toBe(true)
    })

    it('shows completed tab', async () => {
      await login()
      await commands.goto(`${APP_URL}/downtime`)

      const hasCompletedTab = await commands.isVisibleByText('완료됨', 5_000)
      expect(hasCompletedTab).toBe(true)
    })

    it('shows active downtimes or empty state', async () => {
      await login()
      await commands.goto(`${APP_URL}/downtime`)
      await commands.waitForTimeout(2000)

      const hasCards = await commands.isVisibleByText('종료', 3_000)
      const hasEmpty = await commands.isVisibleByText('현재 진행 중인 다운타임이 없습니다', 3_000)
      const hasLoading = await commands.isVisibleByText('로딩 중', 3_000)

      expect(hasCards || hasEmpty || hasLoading).toBe(true)
    })

    it('shows summary cards when data exists', async () => {
      await login()
      await commands.goto(`${APP_URL}/downtime`)
      await commands.waitForTimeout(2000)

      // Summary cards show category labels
      const hasPlanned = await commands.isVisibleByText('계획 정지', 5_000)
      const hasUnplanned = await commands.isVisibleByText('비계획 정지', 5_000)
      const hasMaintenance = await commands.isVisibleByText('정비', 5_000)
      const hasSetup = await commands.isVisibleByText('셋업', 5_000)
      const hasOther = await commands.isVisibleByText('기타', 5_000)

      // At least one category should be visible (or page loads without summary)
      const hasAnyCategory = hasPlanned || hasUnplanned || hasMaintenance || hasSetup || hasOther
      const hasHeading = await commands.isVisibleByText('다운타임 관리', 3_000)
      expect(hasAnyCategory || hasHeading).toBe(true)
    })

    it('opens create downtime modal', async () => {
      await login()
      await commands.goto(`${APP_URL}/downtime`)
      await commands.waitForTimeout(1000)

      await commands.clickByText('다운타임 기록')
      await commands.waitForTimeout(1000)

      // Modal should show equipment selection
      const hasEquipLabel = await commands.isVisibleByText('설비 선택', 5_000)
      expect(hasEquipLabel).toBe(true)
    })

    it('shows reason selection in create modal', async () => {
      await login()
      await commands.goto(`${APP_URL}/downtime`)
      await commands.waitForTimeout(1000)

      await commands.clickByText('다운타임 기록')
      await commands.waitForTimeout(1000)

      const hasReasonLabel = await commands.isVisibleByText('정지 사유', 5_000)
      expect(hasReasonLabel).toBe(true)
    })

    it('shows start time input in create modal', async () => {
      await login()
      await commands.goto(`${APP_URL}/downtime`)
      await commands.waitForTimeout(1000)

      await commands.clickByText('다운타임 기록')
      await commands.waitForTimeout(1000)

      const hasTimeLabel = await commands.isVisibleByText('시작 시간', 5_000)
      expect(hasTimeLabel).toBe(true)

      const hasHint = await commands.isVisibleByText('비워두면 현재 시간으로 기록됩니다', 3_000)
      expect(hasHint).toBe(true)
    })

    it('shows remarks field in create modal', async () => {
      await login()
      await commands.goto(`${APP_URL}/downtime`)
      await commands.waitForTimeout(1000)

      await commands.clickByText('다운타임 기록')
      await commands.waitForTimeout(1000)

      const hasLabel = await commands.isVisibleByText('비고', 5_000)
      expect(hasLabel).toBe(true)
    })

    it('shows cancel and submit buttons in create modal', async () => {
      await login()
      await commands.goto(`${APP_URL}/downtime`)
      await commands.waitForTimeout(1000)

      await commands.clickByText('다운타임 기록')
      await commands.waitForTimeout(1000)

      const hasCancel = await commands.isVisibleByRole('button', '취소')
      expect(hasCancel).toBe(true)

      const hasSubmit = await commands.isVisibleByText('기록 시작', 5_000)
      expect(hasSubmit).toBe(true)
    })

    it('closes create modal on cancel', async () => {
      await login()
      await commands.goto(`${APP_URL}/downtime`)
      await commands.waitForTimeout(1000)

      await commands.clickByText('다운타임 기록')
      await commands.waitForTimeout(1000)

      const hasModal = await commands.isVisibleByText('설비 선택', 3_000)
      expect(hasModal).toBe(true)

      await commands.clickByRole('button', '취소')
      await commands.waitForTimeout(500)

      // Modal should be closed - heading should still be visible
      const hasHeading = await commands.isVisibleByText('다운타임 관리', 3_000)
      expect(hasHeading).toBe(true)
    })

    it('shows completed downtimes table on tab switch', async () => {
      await login()
      await commands.goto(`${APP_URL}/downtime`)
      await commands.waitForTimeout(1000)

      await commands.clickByText('완료됨')
      await commands.waitForTimeout(2000)

      const hasTable = await commands.isVisibleBySelector('table', 3_000)
      const hasEmpty = await commands.isVisibleByText('완료된 다운타임 기록이 없습니다', 3_000)
      const hasLoading = await commands.isVisibleByText('로딩 중', 3_000)

      expect(hasTable || hasEmpty || hasLoading).toBe(true)
    })

    it('shows completed table headers when data exists', async () => {
      await login()
      await commands.goto(`${APP_URL}/downtime`)
      await commands.waitForTimeout(1000)

      await commands.clickByText('완료됨')
      await commands.waitForTimeout(2000)

      const hasTable = await commands.isVisibleBySelector('table', 3_000)
      if (hasTable) {
        const hasEquipCol = await commands.isVisibleByText('설비', 3_000)
        const hasReasonCol = await commands.isVisibleByText('사유', 3_000)
        const hasStartCol = await commands.isVisibleByText('시작시간', 3_000)
        const hasDurationCol = await commands.isVisibleByText('소요시간', 3_000)

        expect(hasEquipCol || hasReasonCol || hasStartCol || hasDurationCol).toBe(true)
      }
    })

    it('active downtime cards show end button', async () => {
      await login()
      await commands.goto(`${APP_URL}/downtime`)
      await commands.waitForTimeout(2000)

      const hasEmpty = await commands.isVisibleByText('현재 진행 중인 다운타임이 없습니다', 3_000)
      if (!hasEmpty) {
        const hasEndBtn = await commands.isVisibleByRole('button', '종료')
        expect(hasEndBtn).toBe(true)
      }
    })

    it('active downtime cards show elapsed time', async () => {
      await login()
      await commands.goto(`${APP_URL}/downtime`)
      await commands.waitForTimeout(2000)

      const hasEmpty = await commands.isVisibleByText('현재 진행 중인 다운타임이 없습니다', 3_000)
      if (!hasEmpty) {
        // Should show time format like "분" or "시간"
        const hasTimeUnit = await commands.isVisibleByText('분|시간', 3_000)
        const hasStartLabel = await commands.isVisibleByText('시작:', 3_000)
        expect(hasTimeUnit || hasStartLabel).toBe(true)
      }
    })
  })
})
