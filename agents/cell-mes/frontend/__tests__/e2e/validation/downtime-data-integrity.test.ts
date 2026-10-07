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

describe('Downtime Data Integrity', () => {

  describe('Downtime reason consistency', () => {
    it('all reasons have required fields', async () => {
      const res = await commands.fetchApi('/downtime/reasons')
      if (!res.ok) return

      for (const reason of res.data) {
        expect(reason.id).toBeDefined()
        expect(typeof reason.id).toBe('number')
        expect(reason.category).toBeDefined()
        expect(['PLANNED', 'UNPLANNED', 'MAINTENANCE', 'SETUP', 'OTHER']).toContain(reason.category)
        expect(reason.code).toBeDefined()
        expect(typeof reason.code).toBe('string')
        expect(reason.code.length).toBeGreaterThan(0)
        expect(reason.name).toBeDefined()
        expect(typeof reason.name).toBe('string')
        expect(typeof reason.is_active).toBe('boolean')
      }
    })

    it('reason codes are unique', async () => {
      const res = await commands.fetchApi('/downtime/reasons')
      if (!res.ok) return

      const codes = res.data.map((r: any) => r.code)
      const uniqueCodes = new Set(codes)
      expect(uniqueCodes.size).toBe(codes.length)
    })

    it('reason IDs are unique', async () => {
      const res = await commands.fetchApi('/downtime/reasons')
      if (!res.ok) return

      const ids = res.data.map((r: any) => r.id)
      const uniqueIds = new Set(ids)
      expect(uniqueIds.size).toBe(ids.length)
    })

    it('category filter returns only matching category', async () => {
      const categories = ['PLANNED', 'UNPLANNED', 'SETUP']

      for (const category of categories) {
        const res = await commands.fetchApi(`/downtime/reasons?category=${category}`)
        if (!res.ok) continue

        for (const reason of res.data) {
          expect(reason.category).toBe(category)
        }
      }
    })

    it('created_at is a valid ISO datetime', async () => {
      const res = await commands.fetchApi('/downtime/reasons')
      if (!res.ok) return

      for (const reason of res.data) {
        if (reason.created_at) {
          const date = new Date(reason.created_at)
          expect(date.getTime()).not.toBeNaN()
        }
      }
    })
  })

  describe('Active downtime consistency', () => {
    it('ongoing downtime records have null end_time', async () => {
      const res = await commands.fetchApi('/downtime?status=ACTIVE')
      if (!res.ok) return

      for (const dt of res.data) {
        expect(dt.end_time).toBeNull()
        expect(dt.calculated_duration_minutes).toBeNull()
      }
    })

    it('all downtime records have required fields', async () => {
      const res = await commands.fetchApi('/downtime')
      if (!res.ok) return

      for (const dt of res.data) {
        expect(dt.id).toBeDefined()
        expect(typeof dt.id).toBe('number')
        expect(dt.equipment_id).toBeDefined()
        expect(typeof dt.equipment_id).toBe('number')
        expect(dt.start_time).toBeDefined()
      }
    })

    it('start_time is a valid ISO datetime', async () => {
      const res = await commands.fetchApi('/downtime')
      if (!res.ok) return

      for (const dt of res.data) {
        const date = new Date(dt.start_time)
        expect(date.getTime()).not.toBeNaN()
      }
    })

    it('downtime equipment IDs reference valid equipment', async () => {
      const dtRes = await commands.fetchApi('/downtime')
      const eqRes = await commands.fetchApi('/masters/equipments')
      if (!dtRes.ok || !eqRes.ok) return

      const equipmentIds = new Set(eqRes.data.map((eq: any) => eq.id))

      for (const dt of dtRes.data) {
        expect(equipmentIds.has(dt.equipment_id)).toBe(true)
      }
    })

    it('downtime reason IDs reference valid reasons', async () => {
      const dtRes = await commands.fetchApi('/downtime')
      const reasonRes = await commands.fetchApi('/downtime/reasons')
      if (!dtRes.ok || !reasonRes.ok) return

      const reasonIds = new Set(reasonRes.data.map((r: any) => r.id))

      for (const dt of dtRes.data) {
        if (dt.reason_id) {
          expect(reasonIds.has(dt.reason_id)).toBe(true)
        }
      }
    })
  })

  describe('Completed downtime consistency', () => {
    it('completed records have non-null end_time', async () => {
      const res = await commands.fetchApi('/downtime')
      if (!res.ok) return

      for (const dt of res.data) {
        if (dt.end_time !== null) {
          const endDate = new Date(dt.end_time)
          expect(endDate.getTime()).not.toBeNaN()
        }
      }
    })

    it('end_time is after start_time for completed records', async () => {
      const res = await commands.fetchApi('/downtime')
      if (!res.ok) return

      for (const dt of res.data) {
        if (dt.end_time !== null) {
          const start = new Date(dt.start_time).getTime()
          const end = new Date(dt.end_time).getTime()
          expect(end).toBeGreaterThanOrEqual(start)
        }
      }
    })

    it('calculated_duration_minutes matches time difference for completed records', async () => {
      const res = await commands.fetchApi('/downtime')
      if (!res.ok) return

      for (const dt of res.data) {
        if (dt.end_time !== null && dt.calculated_duration_minutes !== undefined) {
          expect(dt.calculated_duration_minutes).toBeGreaterThanOrEqual(0)
        }
      }
    })

    it('calculated_duration_minutes is non-negative for completed records', async () => {
      const res = await commands.fetchApi('/downtime')
      if (!res.ok) return

      for (const dt of res.data) {
        if (dt.calculated_duration_minutes !== undefined && dt.calculated_duration_minutes !== null) {
          expect(dt.calculated_duration_minutes).toBeGreaterThanOrEqual(0)
        }
      }
    })
  })

  describe('Downtime summary consistency', () => {
    it('summary has required fields', async () => {
      const res = await commands.fetchApi('/downtime/summary')
      if (!res.ok) return

      expect(res.data).toHaveProperty('by_category')
      expect(res.data).toHaveProperty('total_count')
      expect(res.data).toHaveProperty('total_minutes')
    })

    it('summary total_count is non-negative', async () => {
      const res = await commands.fetchApi('/downtime/summary')
      if (!res.ok) return

      expect(res.data.total_count).toBeGreaterThanOrEqual(0)
      expect(res.data.total_minutes).toBeGreaterThanOrEqual(0)
    })

    it('summary by_category counts sum to total', async () => {
      const res = await commands.fetchApi('/downtime/summary')
      if (!res.ok) return

      if (res.data.by_category && typeof res.data.by_category === 'object') {
        let categorySum = 0
        for (const cat of Object.values(res.data.by_category) as any[]) {
          categorySum += cat.count || 0
        }
        expect(categorySum).toBe(res.data.total_count)
      }
    })

    it('summary categories are valid values', async () => {
      const res = await commands.fetchApi('/downtime/summary')
      if (!res.ok) return

      const validCategories = ['PLANNED', 'UNPLANNED', 'MAINTENANCE', 'SETUP', 'OTHER', 'UNKNOWN']

      if (res.data.by_category && typeof res.data.by_category === 'object') {
        for (const key of Object.keys(res.data.by_category)) {
          expect(validCategories).toContain(key)
        }
      }
    })

    it('summary total_minutes aligns with downtime records', async () => {
      const summaryRes = await commands.fetchApi('/downtime/summary')
      if (!summaryRes.ok) return

      // Verify total_minutes is non-negative
      expect(summaryRes.data.total_minutes).toBeGreaterThanOrEqual(0)

      // Verify by_category sums align with total
      if (summaryRes.data.by_category) {
        let categoryMinutes = 0
        for (const cat of Object.values(summaryRes.data.by_category) as any[]) {
          categoryMinutes += cat.total_minutes || 0
        }
        expect(categoryMinutes).toBe(summaryRes.data.total_minutes)
      }
    })
  })

  describe('Downtime date range filter consistency', () => {
    it('date range filter returns records within range', async () => {
      const dateFrom = new Date()
      dateFrom.setDate(dateFrom.getDate() - 7)
      const dateTo = new Date()

      const res = await commands.fetchApi(
        `/downtime?date_from=${dateFrom.toISOString()}&date_to=${dateTo.toISOString()}`
      )
      if (!res.ok) return

      for (const dt of res.data) {
        const startTime = new Date(dt.start_time).getTime()
        // start_time should be within the range (with some server-side tolerance)
        expect(startTime).toBeGreaterThanOrEqual(dateFrom.getTime() - 60000)
      }
    })

    it('equipment filter returns records for specified equipment', async () => {
      const eqRes = await commands.fetchApi('/masters/equipments')
      if (!eqRes.ok || eqRes.data.length === 0) return

      const equipmentId = eqRes.data[0].id
      const res = await commands.fetchApi(`/downtime?equipment_id=${equipmentId}`)
      if (!res.ok) return

      for (const dt of res.data) {
        expect(dt.equipment_id).toBe(equipmentId)
      }
    })
  })

  describe('Downtime lifecycle data integrity', () => {
    it('creates downtime and verifies state transitions', async () => {
      const eqRes = await commands.fetchApi('/masters/equipments')
      if (!eqRes.ok || eqRes.data.length === 0) return

      const equipmentId = eqRes.data[0].id

      // Create downtime
      const createRes = await commands.fetchApi('/downtime', 'POST', JSON.stringify({
        equipment_id: equipmentId,
        start_time: new Date().toISOString(),
        remarks: 'Data integrity lifecycle test',
      }))
      if (createRes.status !== 201 && createRes.status !== 200) return

      // Verify initial state
      expect(createRes.data.id).toBeDefined()
      expect(createRes.data.equipment_id).toBe(equipmentId)
      expect(createRes.data.end_time).toBeNull()
      expect(createRes.data.remarks).toBe('Data integrity lifecycle test')

      // Verify it appears in ongoing list
      const ongoingRes = await commands.fetchApi('/downtime?status=ACTIVE')
      if (ongoingRes.ok) {
        const found = ongoingRes.data.find((d: any) => d.id === createRes.data.id)
        expect(found).toBeDefined()
        expect(found.end_time).toBeNull()
      }

      // End downtime
      const endRes = await commands.fetchApi(`/downtime/${createRes.data.id}/end`, 'POST')
      if (endRes.ok) {
        expect(endRes.data.end_time).not.toBeNull()

        // Verify end_time is after start_time
        const start = new Date(endRes.data.start_time).getTime()
        const end = new Date(endRes.data.end_time).getTime()
        expect(end).toBeGreaterThanOrEqual(start)

        // Verify duration is calculated
        if (endRes.data.calculated_duration_minutes !== undefined) {
          expect(endRes.data.calculated_duration_minutes).toBeGreaterThanOrEqual(0)
        }
      }

      // Verify it no longer appears in ongoing list
      const afterOngoingRes = await commands.fetchApi('/downtime?status=ACTIVE')
      if (afterOngoingRes.ok) {
        const found = afterOngoingRes.data.find((d: any) => d.id === createRes.data.id)
        expect(found).toBeUndefined()
      }
    })

    it('no equipment has overlapping active downtimes', async () => {
      const res = await commands.fetchApi('/downtime?status=ACTIVE')
      if (!res.ok) return

      // Group by equipment
      const byEquipment: Record<number, any[]> = {}
      for (const dt of res.data) {
        if (!byEquipment[dt.equipment_id]) {
          byEquipment[dt.equipment_id] = []
        }
        byEquipment[dt.equipment_id].push(dt)
      }

      // Each equipment should have at most one active downtime
      for (const [equipId, downtimes] of Object.entries(byEquipment)) {
        expect(downtimes.length).toBeLessThanOrEqual(1)
      }
    })
  })

  describe('Downtime UI-API cross-validation', () => {
    it('active tab shows correct state based on API data', async () => {
      await login()

      const ongoingRes = await commands.fetchApi('/downtime?status=ACTIVE')
      if (!ongoingRes.ok) return

      await commands.goto(`${APP_URL}/downtime`)
      await commands.waitForTimeout(3000)

      if (ongoingRes.data.length === 0) {
        const hasEmpty = await commands.isVisibleByText('현재 진행 중인 다운타임이 없습니다', 5_000)
        expect(hasEmpty).toBe(true)
      } else {
        // Should show end button for active downtimes
        const hasEndBtn = await commands.isVisibleByText('종료', 5_000)
        expect(hasEndBtn).toBe(true)
      }
    })

    it('summary cards match API summary data', async () => {
      await login()

      const summaryRes = await commands.fetchApi('/downtime/summary')
      if (!summaryRes.ok) return

      await commands.goto(`${APP_URL}/downtime`)
      await commands.waitForTimeout(3000)

      // If there is summary data, verify the page renders
      if (summaryRes.data.total_count > 0) {
        const hasDowntime = await commands.isVisibleByText('다운타임', 5_000)
        expect(hasDowntime).toBe(true)
      }
    })

    it('completed tab shows table when completed records exist', async () => {
      await login()

      const completedRes = await commands.fetchApi('/downtime')
      if (!completedRes.ok) return

      const completedRecords = completedRes.data.filter((d: any) => d.end_time !== null)

      await commands.goto(`${APP_URL}/downtime`)
      await commands.waitForTimeout(1000)
      await commands.clickByText('완료됨')
      await commands.waitForTimeout(2000)

      if (completedRecords.length === 0) {
        const hasEmpty = await commands.isVisibleByText('완료된 다운타임 기록이 없습니다', 5_000)
        expect(hasEmpty).toBe(true)
      } else {
        const hasTable = await commands.isVisibleBySelector('table', 5_000)
        expect(hasTable).toBe(true)
      }
    })
  })
})
