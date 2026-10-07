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

describe('Alarms', () => {
  describe('Alarm definitions (API)', () => {
    it('fetches alarm definitions list', async () => {
      const res = await commands.fetchApi('/alarms/definitions')
      expect(res.ok).toBe(true)
      expect(Array.isArray(res.data)).toBe(true)
    })

    it('filters definitions by severity', async () => {
      const severities = ['INFO', 'WARNING', 'ERROR', 'CRITICAL']

      for (const severity of severities) {
        const res = await commands.fetchApi(`/alarms/definitions?severity=${severity}`)
        expect(res.ok).toBe(true)
        expect(Array.isArray(res.data)).toBe(true)

        // Every returned item must match the requested severity
        for (const def of res.data) {
          expect(def.severity).toBe(severity)
        }
      }
    })
  })

  describe('Active alarms (API)', () => {
    it('fetches active alarms list', async () => {
      const res = await commands.fetchApi('/alarms/active')
      expect(res.ok).toBe(true)
      expect(Array.isArray(res.data)).toBe(true)

      // Active alarms should have ACTIVE or ACKNOWLEDGED status
      for (const alarm of res.data) {
        expect(['ACTIVE', 'ACKNOWLEDGED']).toContain(alarm.status)
      }
    })

    it('fetches active alarm summary statistics', async () => {
      const res = await commands.fetchApi('/alarms/active/summary')
      expect(res.ok).toBe(true)

      expect(res.data).toHaveProperty('total')
      expect(res.data).toHaveProperty('by_severity')
      expect(res.data).toHaveProperty('by_equipment')
    })
  })

  describe('Alarm history (API)', () => {
    it('fetches all alarms list', async () => {
      const res = await commands.fetchApi('/alarms')
      expect(res.ok).toBe(true)
      expect(Array.isArray(res.data)).toBe(true)
    })

    it('filters alarms by status', async () => {
      const statuses = ['ACTIVE', 'ACKNOWLEDGED', 'RESOLVED']

      for (const status of statuses) {
        const res = await commands.fetchApi(`/alarms?status=${status}`)
        expect(res.ok).toBe(true)
        expect(Array.isArray(res.data)).toBe(true)

        for (const alarm of res.data) {
          expect(alarm.status).toBe(status)
        }
      }
    })

    it('filters alarms by date range', async () => {
      const dateFrom = new Date()
      dateFrom.setDate(dateFrom.getDate() - 7)
      const dateTo = new Date()

      const res = await commands.fetchApi(
        `/alarms?date_from=${dateFrom.toISOString()}&date_to=${dateTo.toISOString()}`,
      )
      expect(res.ok).toBe(true)
      expect(Array.isArray(res.data)).toBe(true)
    })
  })

  describe('Alarm lifecycle (API)', () => {
    it('creates, acknowledges, and resolves an alarm', async () => {
      // Get equipment
      const eqRes = await commands.fetchApi('/masters/equipments')
      if (!eqRes.ok) return // skip if no equipment endpoint

      if (eqRes.data.length === 0) return // skip if no equipment data

      const equipmentId = eqRes.data[0].id

      // Get alarm definitions
      const defRes = await commands.fetchApi('/alarms/definitions')
      if (!defRes.ok) return
      if (defRes.data.length === 0) return

      const definitionId = defRes.data[0].id

      // 1. Create alarm (ACTIVE)
      const createRes = await commands.fetchApi('/alarms', 'POST', JSON.stringify({
        equipment_id: equipmentId,
        definition_id: definitionId,
        occurred_at: new Date().toISOString(),
        message: 'Vitest E2E alarm lifecycle test',
      }))
      expect(createRes.status).toBe(201)
      expect(createRes.data.status).toBe('ACTIVE')

      // 2. Acknowledge alarm
      const ackRes = await commands.fetchApi(`/alarms/${createRes.data.id}/acknowledge`, 'POST', JSON.stringify({ acknowledged_by: 'vitest-e2e' }))
      expect(ackRes.ok).toBe(true)
      expect(ackRes.data.status).toBe('ACKNOWLEDGED')

      // 3. Resolve alarm
      const resolveRes = await commands.fetchApi(`/alarms/${createRes.data.id}/resolve`, 'POST', JSON.stringify({
        resolved_by: 'vitest-e2e',
        resolution_note: 'Test complete',
      }))
      expect(resolveRes.ok).toBe(true)
      expect(resolveRes.data.status).toBe('RESOLVED')
    })
  })

  describe('Alarm UI page', () => {
    it('navigates to alarms page and shows heading', async () => {
      await login()
      await commands.goto(`${APP_URL}/alarms`)
      await commands.waitForTimeout(2000)

      const hasHeading = await commands.isVisibleByText('알람 관리', 5_000)
      expect(hasHeading).toBe(true)
    })

    it('shows subtitle description', async () => {
      await login()
      await commands.goto(`${APP_URL}/alarms`)

      const hasSub = await commands.isVisibleByText('설비 알람을 모니터링하고 관리합니다', 5_000)
      expect(hasSub).toBe(true)
    })

    it('shows refresh button', async () => {
      await login()
      await commands.goto(`${APP_URL}/alarms`)

      const hasRefresh = await commands.isVisibleByText('새로고침', 5_000)
      expect(hasRefresh).toBe(true)
    })

    it('shows severity summary cards', async () => {
      await login()
      await commands.goto(`${APP_URL}/alarms`)
      await commands.waitForTimeout(2000)

      // Should show at least some severity labels from SEVERITY_CONFIG
      const hasCritical = await commands.isVisibleByText('심각', 5_000)
      const hasWarning = await commands.isVisibleByText('경고', 5_000)
      const hasInfo = await commands.isVisibleByText('정보', 5_000)

      expect(hasCritical || hasWarning || hasInfo).toBe(true)
    })

    it('shows active alarms tab', async () => {
      await login()
      await commands.goto(`${APP_URL}/alarms`)

      const hasActiveTab = await commands.isVisibleByText('활성 알람', 5_000)
      expect(hasActiveTab).toBe(true)
    })

    it('shows history tab', async () => {
      await login()
      await commands.goto(`${APP_URL}/alarms`)

      const hasHistoryTab = await commands.isVisibleByText('알람 이력', 5_000)
      expect(hasHistoryTab).toBe(true)
    })

    it('shows active alarms or empty state by default', async () => {
      await login()
      await commands.goto(`${APP_URL}/alarms`)
      await commands.waitForTimeout(2000)

      // Should show either alarm cards or empty state
      const hasAlarmCards = await commands.isVisibleByText('확인', 3_000)
      const hasEmptyState = await commands.isVisibleByText('활성화된 알람이 없습니다', 3_000)
      const hasLoading = await commands.isVisibleByText('로딩 중', 3_000)

      expect(hasAlarmCards || hasEmptyState || hasLoading).toBe(true)
    })

    it('shows severity grouped sections when alarms exist', async () => {
      await login()
      await commands.goto(`${APP_URL}/alarms`)
      await commands.waitForTimeout(2000)

      // Check for grouped severity headings or empty state
      const hasSeverityGroup = await commands.isVisibleByText('심각|중요|경고|경미|정보', 3_000)
      const hasEmpty = await commands.isVisibleByText('활성화된 알람이 없습니다', 3_000)

      expect(hasSeverityGroup || hasEmpty).toBe(true)
    })

    it('shows alarm history tab with table', async () => {
      await login()
      await commands.goto(`${APP_URL}/alarms`)
      await commands.waitForTimeout(1000)

      // Click history tab
      await commands.clickByText('알람 이력')
      await commands.waitForTimeout(2000)

      // Should show filter or table or empty state
      const hasFilter = await commands.isVisibleByText('전체 심각도', 5_000)
      const hasTable = await commands.isVisibleBySelector('table', 3_000)
      const hasEmpty = await commands.isVisibleByText('알람 이력이 없습니다', 3_000)

      expect(hasFilter || hasTable || hasEmpty).toBe(true)
    })

    it('shows severity filter dropdown in history tab', async () => {
      await login()
      await commands.goto(`${APP_URL}/alarms`)
      await commands.waitForTimeout(1000)

      await commands.clickByText('알람 이력')
      await commands.waitForTimeout(1000)

      // The severity filter is a <select> element - check for the select or surrounding filter area
      const hasSelect = await commands.isVisibleBySelector('select', 5_000)
      const hasFilterText = await commands.isVisibleByText('심각도', 5_000)
      expect(hasSelect || hasFilterText).toBe(true)
    })

    it('shows history table headers when data exists', async () => {
      await login()
      await commands.goto(`${APP_URL}/alarms`)
      await commands.waitForTimeout(1000)

      await commands.clickByText('알람 이력')
      await commands.waitForTimeout(2000)

      const hasTable = await commands.isVisibleBySelector('table', 3_000)
      if (hasTable) {
        const hasSeverityCol = await commands.isVisibleByText('심각도', 3_000)
        const hasEquipCol = await commands.isVisibleByText('설비', 3_000)
        const hasCodeCol = await commands.isVisibleByText('알람 코드', 3_000)

        expect(hasSeverityCol || hasEquipCol || hasCodeCol).toBe(true)
      }
    })

    it('shows occurred time and resolve info in history', async () => {
      await login()
      await commands.goto(`${APP_URL}/alarms`)
      await commands.waitForTimeout(1000)

      await commands.clickByText('알람 이력')
      await commands.waitForTimeout(2000)

      const hasTable = await commands.isVisibleBySelector('table', 3_000)
      if (hasTable) {
        const hasOccurCol = await commands.isVisibleByText('발생 시간', 3_000)
        const hasResolveCol = await commands.isVisibleByText('해제 시간', 3_000)
        const hasHandlerCol = await commands.isVisibleByText('처리자', 3_000)

        expect(hasOccurCol || hasResolveCol || hasHandlerCol).toBe(true)
      }
    })

    it('alarm cards show equipment name and alarm code', async () => {
      await login()
      await commands.goto(`${APP_URL}/alarms`)
      await commands.waitForTimeout(2000)

      const hasEmpty = await commands.isVisibleByText('활성화된 알람이 없습니다', 3_000)
      if (!hasEmpty) {
        // If there are active alarms, check for equipment name display
        const hasEquipName = await commands.isVisibleByText('설비', 3_000)
        const hasTimestamp = await commands.isVisibleByText('발생:', 3_000)
        expect(hasEquipName || hasTimestamp).toBe(true)
      }
    })

    it('alarm cards show acknowledge and resolve buttons', async () => {
      await login()
      await commands.goto(`${APP_URL}/alarms`)
      await commands.waitForTimeout(2000)

      const hasEmpty = await commands.isVisibleByText('활성화된 알람이 없습니다', 3_000)
      if (!hasEmpty) {
        const hasAckBtn = await commands.isVisibleByText('확인', 3_000)
        const hasResolveBtn = await commands.isVisibleByText('해제', 3_000)
        expect(hasAckBtn || hasResolveBtn).toBe(true)
      }
    })
  })
})
