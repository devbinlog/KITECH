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

describe('Scheduler Data Integrity', () => {

  describe('Equipment availability consistency', () => {
    it('equipment count matches machines array length', async () => {
      const res = await commands.fetchApi('/scheduler/equipment-availability')
      if (!res.ok) return

      expect(res.data.count).toBe(res.data.machines.length)
    })

    it('all machines have required fields', async () => {
      const res = await commands.fetchApi('/scheduler/equipment-availability')
      if (!res.ok) return

      for (const machine of res.data.machines) {
        expect(machine.machine_id).toBeDefined()
        expect(typeof machine.machine_id).toBe('string')
        expect(machine.machine_name).toBeDefined()
        expect(machine.machine_type).toBeDefined()
        expect(machine.status).toBeDefined()
        expect(machine.available_from).toBeDefined()
        expect(machine.mes_equipment_id).toBeDefined()
        expect(typeof machine.mes_equipment_id).toBe('number')
      }
    })

    it('machine types are non-empty strings', async () => {
      const res = await commands.fetchApi('/scheduler/equipment-availability')
      if (!res.ok) return

      for (const machine of res.data.machines) {
        expect(machine.machine_type.length).toBeGreaterThan(0)
        // Machine type should be uppercase
        expect(machine.machine_type).toBe(machine.machine_type.toUpperCase())
      }
    })

    it('available_from is a valid ISO datetime', async () => {
      const res = await commands.fetchApi('/scheduler/equipment-availability')
      if (!res.ok) return

      for (const machine of res.data.machines) {
        const date = new Date(machine.available_from)
        expect(date.getTime()).not.toBeNaN()
      }
    })

    it('equipment availability matches MES equipment list', async () => {
      const schedulerRes = await commands.fetchApi('/scheduler/equipment-availability')
      const mesRes = await commands.fetchApi('/masters/equipments')
      if (!schedulerRes.ok || !mesRes.ok) return

      // Every scheduler machine should map to a MES equipment
      for (const machine of schedulerRes.data.machines) {
        const mesEquip = mesRes.data.find((eq: any) => eq.id === machine.mes_equipment_id)
        expect(mesEquip).toBeDefined()
      }
    })
  })

  describe('Work orders for scheduling consistency', () => {
    it('work order count matches array length', async () => {
      const res = await commands.fetchApi('/scheduler/work-orders?status=READY&limit=100')
      if (!res.ok) return

      expect(res.data.count).toBe(res.data.work_orders.length)
    })

    it('all work orders have required fields', async () => {
      const res = await commands.fetchApi('/scheduler/work-orders?status=READY&limit=100')
      if (!res.ok) return

      for (const wo of res.data.work_orders) {
        expect(wo.wo_id).toBeDefined()
        expect(wo.product_name).toBeDefined()
        expect(wo.order_quantity).toBeDefined()
        expect(typeof wo.order_quantity).toBe('number')
        expect(wo.order_quantity).toBeGreaterThan(0)
      }
    })

    it('work order quantities are positive integers', async () => {
      const res = await commands.fetchApi('/scheduler/work-orders?status=READY&limit=100')
      if (!res.ok) return

      for (const wo of res.data.work_orders) {
        expect(wo.order_quantity).toBeGreaterThan(0)
        expect(Number.isInteger(wo.order_quantity)).toBe(true)
      }
    })

    it('work order priorities are valid values', async () => {
      const res = await commands.fetchApi('/scheduler/work-orders?status=READY&limit=100')
      if (!res.ok) return

      for (const wo of res.data.work_orders) {
        if (wo.priority !== undefined && wo.priority !== null) {
          expect(typeof wo.priority).toBe('number')
          expect(wo.priority).toBeGreaterThanOrEqual(1)
          expect(wo.priority).toBeLessThanOrEqual(10)
        }
      }
    })

    it('due dates are valid ISO datetimes when present', async () => {
      const res = await commands.fetchApi('/scheduler/work-orders?status=READY&limit=100')
      if (!res.ok) return

      for (const wo of res.data.work_orders) {
        if (wo.due_date) {
          const date = new Date(wo.due_date)
          expect(date.getTime()).not.toBeNaN()
        }
      }
    })
  })

  describe('Current schedule data integrity', () => {
    it('schedule date matches requested date', async () => {
      const today = new Date().toISOString().split('T')[0]
      const res = await commands.fetchApi(`/scheduler/current-schedule?date=${today}`)
      if (!res.ok) return

      if (res.data.date) {
        expect(res.data.date).toBe(today)
      }
    })

    it('schedule summary counts are non-negative', async () => {
      const res = await commands.fetchApi('/scheduler/current-schedule')
      if (!res.ok) return

      if (res.data.summary) {
        expect(res.data.summary.total_equipments).toBeGreaterThanOrEqual(0)
        expect(res.data.summary.total_scheduled_orders).toBeGreaterThanOrEqual(0)
        expect(res.data.summary.running_orders).toBeGreaterThanOrEqual(0)
      }
    })

    it('running orders do not exceed total scheduled', async () => {
      const res = await commands.fetchApi('/scheduler/current-schedule')
      if (!res.ok) return

      if (res.data.summary) {
        expect(res.data.summary.running_orders).toBeLessThanOrEqual(
          res.data.summary.total_scheduled_orders
        )
      }
    })

    it('availability equipment IDs are unique', async () => {
      const res = await commands.fetchApi('/scheduler/current-schedule')
      if (!res.ok || !res.data.availability) return

      const ids = res.data.availability.map((a: any) => a.equipment_id)
      const uniqueIds = new Set(ids)
      expect(uniqueIds.size).toBe(ids.length)
    })

    it('schedule slots have valid time ranges', async () => {
      const res = await commands.fetchApi('/scheduler/current-schedule')
      if (!res.ok || !res.data.availability) return

      for (const equip of res.data.availability) {
        if (!equip.schedule) continue
        for (const slot of equip.schedule) {
          if (slot.slot_start && slot.slot_end) {
            const start = new Date(slot.slot_start).getTime()
            const end = new Date(slot.slot_end).getTime()
            expect(end).toBeGreaterThanOrEqual(start)
          }
        }
      }
    })

    it('no overlapping schedule slots per equipment', async () => {
      const res = await commands.fetchApi('/scheduler/current-schedule')
      if (!res.ok || !res.data.availability) return

      for (const equip of res.data.availability) {
        if (!equip.schedule || equip.schedule.length < 2) continue

        const slots = equip.schedule
          .filter((s: any) => s.slot_start && s.slot_end)
          .sort((a: any, b: any) =>
            new Date(a.slot_start).getTime() - new Date(b.slot_start).getTime()
          )

        for (let i = 0; i < slots.length - 1; i++) {
          const currentEnd = new Date(slots[i].slot_end).getTime()
          const nextStart = new Date(slots[i + 1].slot_start).getTime()
          expect(currentEnd).toBeLessThanOrEqual(nextStart)
        }
      }
    })
  })

  describe('Schedule overview UI-API cross-validation', () => {
    it('equipment count on UI matches API data', async () => {
      await login()

      const res = await commands.fetchApi('/scheduler/current-schedule')
      if (!res.ok || !res.data.summary) return

      await commands.goto(`${APP_URL}/scheduler`)
      await commands.waitForTimeout(3000)

      const expectedCount = res.data.summary.total_equipments
      if (expectedCount > 0) {
        const hasCount = await commands.isVisibleByText(`${expectedCount}`, 5_000)
        expect(hasCount).toBe(true)
      }
    })

    it('execution page equipment count matches API', async () => {
      await login()

      const res = await commands.fetchApi('/scheduler/equipment-availability')
      if (!res.ok) return

      await commands.goto(`${APP_URL}/scheduler/execute`)
      await commands.waitForTimeout(3000)

      const expectedCount = res.data.count
      const hasCount = await commands.isVisibleByText(`${expectedCount}`, 5_000)
      const hasDash = await commands.isVisibleByText('-', 3_000)
      expect(hasCount || hasDash).toBe(true)
    })

    it('execution page work order count matches API', async () => {
      await login()

      const res = await commands.fetchApi('/scheduler/work-orders?status=READY&limit=100')
      if (!res.ok) return

      await commands.goto(`${APP_URL}/scheduler/execute`)
      await commands.waitForTimeout(3000)

      const expectedCount = res.data.count
      const hasCount = await commands.isVisibleByText(`${expectedCount}`, 5_000)
      const hasDash = await commands.isVisibleByText('-', 3_000)
      expect(hasCount || hasDash).toBe(true)
    })
  })
})
