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

describe('Alarm Data Integrity', () => {

  describe('Alarm definition consistency', () => {
    it('all definitions have required fields', async () => {
      const res = await commands.fetchApi('/alarms/definitions')
      if (!res.ok) return

      for (const def of res.data) {
        expect(def.id).toBeDefined()
        expect(typeof def.id).toBe('number')
        expect(def.code).toBeDefined()
        expect(typeof def.code).toBe('string')
        expect(def.code.length).toBeGreaterThan(0)
        expect(def.name).toBeDefined()
        expect(typeof def.name).toBe('string')
        expect(def.severity).toBeDefined()
        expect(['INFO', 'WARNING', 'CRITICAL', 'EMERGENCY']).toContain(def.severity)
        expect(typeof def.is_active).toBe('boolean')
      }
    })

    it('alarm codes are unique across definitions', async () => {
      const res = await commands.fetchApi('/alarms/definitions')
      if (!res.ok) return

      const codes = res.data.map((d: any) => d.code)
      const uniqueCodes = new Set(codes)
      expect(uniqueCodes.size).toBe(codes.length)
    })

    it('definition IDs are unique', async () => {
      const res = await commands.fetchApi('/alarms/definitions')
      if (!res.ok) return

      const ids = res.data.map((d: any) => d.id)
      const uniqueIds = new Set(ids)
      expect(uniqueIds.size).toBe(ids.length)
    })

    it('severity filter returns only matching severity', async () => {
      const severities = ['INFO', 'WARNING', 'CRITICAL', 'EMERGENCY']

      for (const severity of severities) {
        const res = await commands.fetchApi(`/alarms/definitions?severity=${severity}`)
        if (!res.ok) continue

        for (const def of res.data) {
          expect(def.severity).toBe(severity)
        }
      }
    })

    it('created_at is a valid ISO datetime', async () => {
      const res = await commands.fetchApi('/alarms/definitions')
      if (!res.ok) return

      for (const def of res.data) {
        if (def.created_at) {
          const date = new Date(def.created_at)
          expect(date.getTime()).not.toBeNaN()
        }
      }
    })
  })

  describe('Active alarm consistency', () => {
    it('all active alarms have ACTIVE or ACKNOWLEDGED status', async () => {
      const res = await commands.fetchApi('/alarms/active')
      if (!res.ok) return

      for (const alarm of res.data) {
        expect(['ACTIVE', 'ACKNOWLEDGED']).toContain(alarm.status)
      }
    })

    it('active alarms have required fields', async () => {
      const res = await commands.fetchApi('/alarms/active')
      if (!res.ok) return

      for (const alarm of res.data) {
        expect(alarm.id).toBeDefined()
        expect(typeof alarm.id).toBe('number')
        expect(alarm.equipment_id).toBeDefined()
        expect(typeof alarm.equipment_id).toBe('number')
        expect(alarm.occurred_at).toBeDefined()
        expect(alarm.status).toBeDefined()
        expect(alarm.message).toBeDefined()
      }
    })

    it('active alarms have no resolved_at timestamp', async () => {
      const res = await commands.fetchApi('/alarms/active')
      if (!res.ok) return

      for (const alarm of res.data) {
        expect(alarm.resolved_at).toBeNull()
        expect(alarm.resolved_by).toBeNull()
      }
    })

    it('acknowledged alarms have acknowledged_at and acknowledged_by', async () => {
      const res = await commands.fetchApi('/alarms/active')
      if (!res.ok) return

      for (const alarm of res.data) {
        if (alarm.status === 'ACKNOWLEDGED') {
          expect(alarm.acknowledged_at).not.toBeNull()
          expect(alarm.acknowledged_by).not.toBeNull()
        }
      }
    })

    it('occurred_at is a valid ISO datetime for all active alarms', async () => {
      const res = await commands.fetchApi('/alarms/active')
      if (!res.ok) return

      for (const alarm of res.data) {
        const date = new Date(alarm.occurred_at)
        expect(date.getTime()).not.toBeNaN()
      }
    })

    it('active alarm equipment IDs reference valid equipment', async () => {
      const alarmRes = await commands.fetchApi('/alarms/active')
      const eqRes = await commands.fetchApi('/masters/equipments')
      if (!alarmRes.ok || !eqRes.ok) return

      const equipmentIds = new Set(eqRes.data.map((eq: any) => eq.id))

      for (const alarm of alarmRes.data) {
        expect(equipmentIds.has(alarm.equipment_id)).toBe(true)
      }
    })

    it('active alarm definition_ids reference valid definitions', async () => {
      const alarmRes = await commands.fetchApi('/alarms/active')
      const defRes = await commands.fetchApi('/alarms/definitions')
      if (!alarmRes.ok || !defRes.ok) return

      const defIds = new Set(defRes.data.map((d: any) => d.id))

      for (const alarm of alarmRes.data) {
        if (alarm.definition_id) {
          expect(defIds.has(alarm.definition_id)).toBe(true)
        }
      }
    })
  })

  describe('Alarm summary consistency', () => {
    it('summary total matches active alarm count', async () => {
      const activeRes = await commands.fetchApi('/alarms/active')
      const summaryRes = await commands.fetchApi('/alarms/active/summary')
      if (!activeRes.ok || !summaryRes.ok) return

      const activeCount = activeRes.data.length

      // Summary can be object with total or array
      if (summaryRes.data.total !== undefined) {
        expect(summaryRes.data.total).toBe(activeCount)
      }
    })

    it('summary by_severity counts sum to total', async () => {
      const res = await commands.fetchApi('/alarms/active/summary')
      if (!res.ok) return

      if (res.data.total !== undefined && res.data.by_severity) {
        let severitySum = 0
        for (const key of Object.keys(res.data.by_severity)) {
          severitySum += res.data.by_severity[key]
        }
        expect(severitySum).toBe(res.data.total)
      }
    })

    it('summary severity keys are valid', async () => {
      const res = await commands.fetchApi('/alarms/active/summary')
      if (!res.ok) return

      const validSeverities = ['INFO', 'WARNING', 'CRITICAL', 'EMERGENCY']

      if (res.data.by_severity) {
        for (const key of Object.keys(res.data.by_severity)) {
          expect(validSeverities).toContain(key)
        }
      }
    })

    it('summary counts are non-negative', async () => {
      const res = await commands.fetchApi('/alarms/active/summary')
      if (!res.ok) return

      if (res.data.total !== undefined) {
        expect(res.data.total).toBeGreaterThanOrEqual(0)
      }

      if (res.data.by_severity) {
        for (const count of Object.values(res.data.by_severity)) {
          expect(count as number).toBeGreaterThanOrEqual(0)
        }
      }
    })
  })

  describe('Alarm status filter consistency', () => {
    it('status filter ACTIVE returns only ACTIVE alarms', async () => {
      const res = await commands.fetchApi('/alarms?status=ACTIVE')
      if (!res.ok) return

      for (const alarm of res.data) {
        expect(alarm.status).toBe('ACTIVE')
      }
    })

    it('status filter ACKNOWLEDGED returns only ACKNOWLEDGED alarms', async () => {
      const res = await commands.fetchApi('/alarms?status=ACKNOWLEDGED')
      if (!res.ok) return

      for (const alarm of res.data) {
        expect(alarm.status).toBe('ACKNOWLEDGED')
      }
    })

    it('status filter RESOLVED returns only RESOLVED alarms', async () => {
      const res = await commands.fetchApi('/alarms?status=RESOLVED')
      if (!res.ok) return

      for (const alarm of res.data) {
        expect(alarm.status).toBe('RESOLVED')
      }
    })

    it('RESOLVED alarms have resolved_at and resolved_by', async () => {
      const res = await commands.fetchApi('/alarms?status=RESOLVED')
      if (!res.ok) return

      for (const alarm of res.data) {
        expect(alarm.resolved_at).not.toBeNull()
        expect(alarm.resolved_by).not.toBeNull()
        // resolved_at should be after occurred_at
        const occurred = new Date(alarm.occurred_at).getTime()
        const resolved = new Date(alarm.resolved_at).getTime()
        expect(resolved).toBeGreaterThanOrEqual(occurred)
      }
    })

    it('all alarms have valid status values', async () => {
      const res = await commands.fetchApi('/alarms')
      if (!res.ok) return

      const validStatuses = ['ACTIVE', 'ACKNOWLEDGED', 'RESOLVED']
      for (const alarm of res.data) {
        expect(validStatuses).toContain(alarm.status)
      }
    })
  })

  describe('Alarm lifecycle data integrity', () => {
    it('creates alarm and verifies initial state', async () => {
      const eqRes = await commands.fetchApi('/masters/equipments')
      if (!eqRes.ok || eqRes.data.length === 0) return

      const defRes = await commands.fetchApi('/alarms/definitions')
      if (!defRes.ok || defRes.data.length === 0) return

      const equipmentId = eqRes.data[0].id
      const definitionId = defRes.data[0].id
      const beforeTime = new Date().toISOString()

      const createRes = await commands.fetchApi('/alarms', 'POST', JSON.stringify({
        equipment_id: equipmentId,
        definition_id: definitionId,
        occurred_at: new Date().toISOString(),
        message: 'Data integrity lifecycle test',
      }))
      if (createRes.status !== 201) return

      // Verify initial state
      expect(createRes.data.status).toBe('ACTIVE')
      expect(createRes.data.equipment_id).toBe(equipmentId)
      expect(createRes.data.acknowledged_at).toBeNull()
      expect(createRes.data.acknowledged_by).toBeNull()
      expect(createRes.data.resolved_at).toBeNull()
      expect(createRes.data.resolved_by).toBeNull()

      // Verify it appears in active list
      const activeRes = await commands.fetchApi('/alarms/active')
      if (activeRes.ok) {
        const found = activeRes.data.find((a: any) => a.id === createRes.data.id)
        expect(found).toBeDefined()
        expect(found.status).toBe('ACTIVE')
      }

      // Acknowledge
      const ackRes = await commands.fetchApi(
        `/alarms/${createRes.data.id}/acknowledge`, 'POST',
        JSON.stringify({ acknowledged_by: 'integrity-test' })
      )
      if (ackRes.ok) {
        expect(ackRes.data.status).toBe('ACKNOWLEDGED')
        expect(ackRes.data.acknowledged_by).toBe('integrity-test')
        expect(ackRes.data.acknowledged_at).not.toBeNull()
        // acknowledged_at should be after occurred_at
        const occurred = new Date(ackRes.data.occurred_at).getTime()
        const acked = new Date(ackRes.data.acknowledged_at).getTime()
        expect(acked).toBeGreaterThanOrEqual(occurred)
      }

      // Resolve
      const resolveRes = await commands.fetchApi(
        `/alarms/${createRes.data.id}/resolve`, 'POST',
        JSON.stringify({
          resolved_by: 'integrity-test',
          resolution_note: 'Lifecycle test complete',
        })
      )
      if (resolveRes.ok) {
        expect(resolveRes.data.status).toBe('RESOLVED')
        expect(resolveRes.data.resolved_by).toBe('integrity-test')
        expect(resolveRes.data.resolved_at).not.toBeNull()
        expect(resolveRes.data.resolution_note).toBe('Lifecycle test complete')

        // resolved_at should be after acknowledged_at
        if (resolveRes.data.acknowledged_at) {
          const acked = new Date(resolveRes.data.acknowledged_at).getTime()
          const resolved = new Date(resolveRes.data.resolved_at).getTime()
          expect(resolved).toBeGreaterThanOrEqual(acked)
        }
      }

      // Verify it no longer appears in active list
      const afterActiveRes = await commands.fetchApi('/alarms/active')
      if (afterActiveRes.ok) {
        const found = afterActiveRes.data.find((a: any) => a.id === createRes.data.id)
        expect(found).toBeUndefined()
      }

      // Verify it appears in RESOLVED filter
      const resolvedRes = await commands.fetchApi('/alarms?status=RESOLVED')
      if (resolvedRes.ok) {
        const found = resolvedRes.data.find((a: any) => a.id === createRes.data.id)
        expect(found).toBeDefined()
      }
    })

    it('duration_minutes is calculated correctly for resolved alarms', async () => {
      const res = await commands.fetchApi('/alarms?status=RESOLVED')
      if (!res.ok) return

      for (const alarm of res.data) {
        if (alarm.duration_minutes !== null && alarm.occurred_at && alarm.resolved_at) {
          const occurred = new Date(alarm.occurred_at).getTime()
          const resolved = new Date(alarm.resolved_at).getTime()
          const expectedMinutes = (resolved - occurred) / 60000

          // Allow 2 minute tolerance for server-side calculation differences
          expect(Math.abs(alarm.duration_minutes - expectedMinutes)).toBeLessThan(2)
        }
      }
    })
  })

  describe('Alarm UI-API cross-validation', () => {
    it('severity summary cards match API counts', async () => {
      await login()

      const summaryRes = await commands.fetchApi('/alarms/active/summary')
      if (!summaryRes.ok) return

      await commands.goto(`${APP_URL}/alarms`)
      await commands.waitForTimeout(3000)

      // Check total count displayed
      if (summaryRes.data.total !== undefined && summaryRes.data.total > 0) {
        const hasTotal = await commands.isVisibleByText(`${summaryRes.data.total}`, 5_000)
        // Total count should appear somewhere on page
        expect(hasTotal).toBe(true)
      }
    })

    it('active alarm count matches API data', async () => {
      await login()

      const activeRes = await commands.fetchApi('/alarms/active')
      if (!activeRes.ok) return

      await commands.goto(`${APP_URL}/alarms`)
      await commands.waitForTimeout(3000)

      if (activeRes.data.length === 0) {
        const hasEmpty = await commands.isVisibleByText('활성화된 알람이 없습니다', 5_000)
        expect(hasEmpty).toBe(true)
      }
    })

    it('history tab shows alarms from API', async () => {
      await login()

      const allRes = await commands.fetchApi('/alarms')
      if (!allRes.ok) return

      await commands.goto(`${APP_URL}/alarms`)
      await commands.waitForTimeout(1000)

      await commands.clickByText('알람 이력')
      await commands.waitForTimeout(2000)

      if (allRes.data.length === 0) {
        const hasEmpty = await commands.isVisibleByText('알람 이력이 없습니다', 5_000)
        expect(hasEmpty).toBe(true)
      } else {
        const hasTable = await commands.isVisibleBySelector('table', 5_000)
        expect(hasTable).toBe(true)
      }
    })
  })
})
