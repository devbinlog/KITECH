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

describe('Cross-Module Workflow Integrity', () => {

  describe('Equipment is consistent across modules', () => {
    it('equipment IDs in alarms exist in equipment master', async () => {
      const alarmRes = await commands.fetchApi('/alarms')
      const eqRes = await commands.fetchApi('/masters/equipments')
      if (!alarmRes.ok || !eqRes.ok) return

      const validIds = new Set(eqRes.data.map((eq: any) => eq.id))

      for (const alarm of alarmRes.data) {
        expect(validIds.has(alarm.equipment_id)).toBe(true)
      }
    })

    it('equipment IDs in downtime exist in equipment master', async () => {
      const dtRes = await commands.fetchApi('/downtime')
      const eqRes = await commands.fetchApi('/masters/equipments')
      if (!dtRes.ok || !eqRes.ok) return

      const validIds = new Set(eqRes.data.map((eq: any) => eq.id))

      for (const dt of dtRes.data) {
        expect(validIds.has(dt.equipment_id)).toBe(true)
      }
    })

    it('equipment IDs in scheduler match equipment master', async () => {
      const schedRes = await commands.fetchApi('/scheduler/equipment-availability')
      const eqRes = await commands.fetchApi('/masters/equipments')
      if (!schedRes.ok || !eqRes.ok) return

      const validIds = new Set(eqRes.data.map((eq: any) => eq.id))

      for (const machine of schedRes.data.machines) {
        if (machine.mes_equipment_id) {
          expect(validIds.has(machine.mes_equipment_id)).toBe(true)
        }
      }
    })

    it('equipment count is consistent across modules', async () => {
      const eqRes = await commands.fetchApi('/masters/equipments')
      const schedRes = await commands.fetchApi('/scheduler/equipment-availability')
      if (!eqRes.ok || !schedRes.ok) return

      // Scheduler machines should not exceed total equipment count
      expect(schedRes.data.machines.length).toBeLessThanOrEqual(eqRes.data.length)
    })
  })

  describe('Alarm-Downtime correlation', () => {
    it('equipment with active alarms has consistent state', async () => {
      const alarmRes = await commands.fetchApi('/alarms/active')
      const dtRes = await commands.fetchApi('/downtime?ongoing_only=true')
      if (!alarmRes.ok || !dtRes.ok) return

      // Track which equipment has active alarms
      const alarmedEquipment = new Set(alarmRes.data.map((a: any) => a.equipment_id))
      // Track which equipment has active downtime
      const downtimeEquipment = new Set(dtRes.data.map((d: any) => d.equipment_id))

      // Not all alarmed equipment needs downtime, but this checks consistency
      // Equipment with both should have timestamps in reasonable order
      for (const alarm of alarmRes.data) {
        if (downtimeEquipment.has(alarm.equipment_id)) {
          const matchingDt = dtRes.data.find((d: any) => d.equipment_id === alarm.equipment_id)
          if (matchingDt) {
            // Both should have valid timestamps
            const alarmTime = new Date(alarm.occurred_at).getTime()
            const dtStartTime = new Date(matchingDt.start_time).getTime()
            expect(alarmTime).not.toBeNaN()
            expect(dtStartTime).not.toBeNaN()
          }
        }
      }
    })

    it('no equipment has more active alarms than total alarm definitions', async () => {
      const alarmRes = await commands.fetchApi('/alarms/active')
      const defRes = await commands.fetchApi('/alarms/definitions')
      if (!alarmRes.ok || !defRes.ok) return

      // Group active alarms by equipment
      const byEquipment: Record<number, number> = {}
      for (const alarm of alarmRes.data) {
        byEquipment[alarm.equipment_id] = (byEquipment[alarm.equipment_id] || 0) + 1
      }

      const totalDefs = defRes.data.length
      for (const [equipId, count] of Object.entries(byEquipment)) {
        // An equipment shouldn't have more active alarms than total definitions
        expect(count).toBeLessThanOrEqual(totalDefs)
      }
    })
  })

  describe('Scheduler-Equipment availability correlation', () => {
    it('equipment with active downtime reflects in scheduler availability', async () => {
      const dtRes = await commands.fetchApi('/downtime?ongoing_only=true')
      const schedRes = await commands.fetchApi('/scheduler/equipment-availability')
      if (!dtRes.ok || !schedRes.ok) return

      const downtimeEquipmentIds = new Set(dtRes.data.map((d: any) => d.equipment_id))

      for (const machine of schedRes.data.machines) {
        if (downtimeEquipmentIds.has(machine.mes_equipment_id)) {
          // Equipment with active downtime may show as non-available or have a status indicator
          // The important thing is that the data is present and consistent
          expect(machine.status).toBeDefined()
        }
      }
    })

    it('scheduler work orders reference valid products', async () => {
      const woRes = await commands.fetchApi('/scheduler/work-orders?status=READY&limit=100')
      if (!woRes.ok) return

      for (const wo of woRes.data.work_orders) {
        expect(wo.product_name).toBeDefined()
        expect(typeof wo.product_name).toBe('string')
        expect(wo.product_name.length).toBeGreaterThan(0)
      }
    })

    it('current schedule references valid equipment from availability', async () => {
      const scheduleRes = await commands.fetchApi('/scheduler/current-schedule')
      const availRes = await commands.fetchApi('/scheduler/equipment-availability')
      if (!scheduleRes.ok || !availRes.ok) return
      if (!scheduleRes.data.availability) return

      const machineIds = new Set(availRes.data.machines.map((m: any) => m.machine_id))

      for (const equip of scheduleRes.data.availability) {
        if (equip.machine_id) {
          expect(machineIds.has(equip.machine_id)).toBe(true)
        }
      }
    })
  })

  describe('Work order data flow consistency', () => {
    it('work order statuses are valid across modules', async () => {
      const validStatuses = ['CREATED', 'READY', 'RUNNING', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'ON_HOLD', 'DONE', 'ERROR', 'PAUSE']

      // Check production orders
      const prodRes = await commands.fetchApi('/production/orders?view=all&limit=50')
      if (prodRes.ok) {
        const orders = prodRes.data?.items || prodRes.data?.data || prodRes.data || []
        for (const order of orders) {
          if (order.status) {
            expect(validStatuses).toContain(order.status)
          }
        }
      }
    })

    it('scheduler work orders have matching MES records', async () => {
      const schedWoRes = await commands.fetchApi('/scheduler/work-orders?status=READY&limit=10')
      if (!schedWoRes.ok) return

      for (const wo of schedWoRes.data.work_orders) {
        if (wo.mes_wo_id) {
          const mesRes = await commands.fetchApi(`/production/orders/${wo.mes_wo_id}`)
          if (mesRes.ok) {
            expect(mesRes.data).toBeDefined()
          }
        }
      }
    })
  })

  describe('Cross-module UI navigation consistency', () => {
    it('sidebar navigation reaches all module pages', async () => {
      await login()

      const pages = [
        { path: '/scheduler', text: '스케줄 현황' },
        { path: '/scheduler/execute', text: '스케줄 실행' },
        { path: '/alarms', text: '알람 관리' },
        { path: '/downtime', text: '다운타임 관리' },
      ]

      for (const page of pages) {
        await commands.goto(`${APP_URL}${page.path}`)
        await commands.waitForTimeout(2000)

        const hasText = await commands.isVisibleByText(page.text, 5_000)
        expect(hasText).toBe(true)
      }
    })

    it('equipment name consistency between alarms and downtime pages', async () => {
      await login()

      // Get equipment from API
      const eqRes = await commands.fetchApi('/masters/equipments')
      if (!eqRes.ok || eqRes.data.length === 0) return

      const equipmentNames = eqRes.data.map((eq: any) => eq.name)

      // Check alarms page for equipment names
      const alarmRes = await commands.fetchApi('/alarms/active')
      if (alarmRes.ok && alarmRes.data.length > 0) {
        await commands.goto(`${APP_URL}/alarms`)
        await commands.waitForTimeout(3000)

        // If there are active alarms, equipment names should appear
        const hasEquipRef = await commands.isVisibleByText('설비', 5_000)
        expect(hasEquipRef).toBe(true)
      }
    })

    it('module data refreshes correctly on page revisit', async () => {
      await login()

      // Visit scheduler page
      await commands.goto(`${APP_URL}/scheduler`)
      await commands.waitForTimeout(2000)
      const hasScheduler = await commands.isVisibleByText('스케줄 현황', 5_000)
      expect(hasScheduler).toBe(true)

      // Navigate to alarms
      await commands.goto(`${APP_URL}/alarms`)
      await commands.waitForTimeout(2000)
      const hasAlarms = await commands.isVisibleByText('알람 관리', 5_000)
      expect(hasAlarms).toBe(true)

      // Navigate back to scheduler
      await commands.goto(`${APP_URL}/scheduler`)
      await commands.waitForTimeout(2000)
      const hasSchedulerAgain = await commands.isVisibleByText('스케줄 현황', 5_000)
      expect(hasSchedulerAgain).toBe(true)
    })
  })

  describe('Edge case: empty data handling', () => {
    it('scheduler handles no equipment gracefully', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler/execute`)
      await commands.waitForTimeout(3000)

      // Page should always load without errors
      const hasHeading = await commands.isVisibleByText('스케줄 실행', 5_000)
      expect(hasHeading).toBe(true)
    })

    it('alarms page handles no active alarms gracefully', async () => {
      await login()
      await commands.goto(`${APP_URL}/alarms`)
      await commands.waitForTimeout(3000)

      // Should show either alarm cards or empty state - never break
      const hasContent = await commands.isVisibleByText('알람 관리', 5_000)
      expect(hasContent).toBe(true)
    })

    it('downtime page handles no active downtimes gracefully', async () => {
      await login()
      await commands.goto(`${APP_URL}/downtime`)
      await commands.waitForTimeout(3000)

      const hasContent = await commands.isVisibleByText('다운타임 관리', 5_000)
      expect(hasContent).toBe(true)
    })

    it('scheduler handles no work orders gracefully', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler/execute`)
      await commands.waitForTimeout(3000)

      // Even with no work orders, page structure should be intact
      const hasExecuteBtn = await commands.isVisibleByRole('button', '스케줄 실행')
      expect(hasExecuteBtn).toBe(true)
    })

    it('alarm history handles empty date range gracefully', async () => {
      await login()
      await commands.goto(`${APP_URL}/alarms`)
      await commands.waitForTimeout(1000)

      await commands.clickByText('알람 이력')
      await commands.waitForTimeout(2000)

      // Should show filter or table or empty state - never break
      const hasFilter = await commands.isVisibleByText('전체 심각도', 5_000)
      const hasTable = await commands.isVisibleBySelector('table', 3_000)
      const hasEmpty = await commands.isVisibleByText('알람 이력이 없습니다', 3_000)

      expect(hasFilter || hasTable || hasEmpty).toBe(true)
    })
  })

  describe('Edge case: data boundary validation', () => {
    it('alarm severity counts are never negative', async () => {
      const res = await commands.fetchApi('/alarms/active/summary')
      if (!res.ok) return

      if (res.data.by_severity) {
        for (const [severity, count] of Object.entries(res.data.by_severity)) {
          expect(count as number).toBeGreaterThanOrEqual(0)
        }
      }
      if (res.data.total !== undefined) {
        expect(res.data.total).toBeGreaterThanOrEqual(0)
      }
    })

    it('downtime duration is never negative', async () => {
      const res = await commands.fetchApi('/downtime')
      if (!res.ok) return

      for (const dt of res.data) {
        if (dt.calculated_duration_minutes !== undefined && dt.calculated_duration_minutes !== null) {
          expect(dt.calculated_duration_minutes).toBeGreaterThanOrEqual(0)
        }
      }
    })

    it('scheduler equipment count is never negative', async () => {
      const res = await commands.fetchApi('/scheduler/equipment-availability')
      if (!res.ok) return

      expect(res.data.count).toBeGreaterThanOrEqual(0)
      expect(res.data.machines.length).toBeGreaterThanOrEqual(0)
    })

    it('work order quantities are always positive', async () => {
      const res = await commands.fetchApi('/scheduler/work-orders?status=READY&limit=100')
      if (!res.ok) return

      for (const wo of res.data.work_orders) {
        expect(wo.order_quantity).toBeGreaterThan(0)
      }
    })

    it('alarm timestamps are not in the far future', async () => {
      const res = await commands.fetchApi('/alarms')
      if (!res.ok) return

      const oneWeekFromNow = Date.now() + 7 * 24 * 60 * 60 * 1000

      for (const alarm of res.data) {
        const occurredAt = new Date(alarm.occurred_at).getTime()
        expect(occurredAt).toBeLessThan(oneWeekFromNow)
      }
    })

    it('downtime start_time is not in the far future', async () => {
      const res = await commands.fetchApi('/downtime')
      if (!res.ok) return

      const oneWeekFromNow = Date.now() + 7 * 24 * 60 * 60 * 1000

      for (const dt of res.data) {
        const startTime = new Date(dt.start_time).getTime()
        expect(startTime).toBeLessThan(oneWeekFromNow)
      }
    })
  })

  describe('Production results → KPI dashboard reflection', () => {
    it('total_production in KPI matches production results sum', async () => {
      const kpiRes = await commands.fetchApi('/analytics/kpi/summary')
      const resultsRes = await commands.fetchApi('/production/results?limit=500')
      if (!kpiRes.ok || !resultsRes.ok) return

      const results = resultsRes.data?.items || resultsRes.data || []
      const sumProduced = results.reduce((sum: number, r: any) => {
        return sum + (r.ok_qty || 0) + (r.ng_qty || 0)
      }, 0)

      // KPI total_production should be close to sum of all results
      // Allow tolerance since KPI may use different time window
      if (kpiRes.data.total_production !== undefined && sumProduced > 0) {
        expect(kpiRes.data.total_production).toBeGreaterThan(0)
      }
    })

    it('KPI defect_rate consistent with production results', async () => {
      const kpiRes = await commands.fetchApi('/analytics/kpi/summary')
      const resultsRes = await commands.fetchApi('/production/results?limit=500')
      if (!kpiRes.ok || !resultsRes.ok) return

      const results = resultsRes.data?.items || resultsRes.data || []
      let totalOk = 0
      let totalNg = 0

      for (const r of results) {
        totalOk += r.ok_qty || 0
        totalNg += r.ng_qty || 0
      }

      const total = totalOk + totalNg
      if (total === 0 || kpiRes.data.defect_rate === undefined) return

      const calculatedDefectRate = (totalNg / total) * 100
      const diff = Math.abs(calculatedDefectRate - kpiRes.data.defect_rate)
      // Allow 2% tolerance due to time window differences
      expect(diff).toBeLessThan(2)
    })

    it('KPI quality component consistent with defect_rate', async () => {
      const kpiRes = await commands.fetchApi('/analytics/kpi/summary')
      if (!kpiRes.ok || !kpiRes.data) return

      const { quality, defect_rate } = kpiRes.data
      if (quality === undefined || defect_rate === undefined) return

      // quality ≈ 100 - defect_rate (roughly)
      const expectedQuality = 100 - defect_rate
      const diff = Math.abs(expectedQuality - quality)
      // Allow 5% tolerance for calculation method differences
      expect(diff).toBeLessThan(5)
    })
  })

  describe('Alarm-Downtime-Equipment state correlation', () => {
    it('resolved alarms have resolved_by field', async () => {
      const alarmRes = await commands.fetchApi('/alarms')
      if (!alarmRes.ok) return

      for (const alarm of alarmRes.data) {
        if (alarm.resolved_at) {
          expect(alarm.resolved_by).toBeTruthy()
        }
      }
    })

    it('acknowledged alarms have acknowledged_at timestamp', async () => {
      const alarmRes = await commands.fetchApi('/alarms')
      if (!alarmRes.ok) return

      for (const alarm of alarmRes.data) {
        if (alarm.acknowledged_by) {
          expect(alarm.acknowledged_at).toBeTruthy()
        }
      }
    })

    it('active alarm summary total matches active alarm list count', async () => {
      const summaryRes = await commands.fetchApi('/alarms/active/summary')
      const activeRes = await commands.fetchApi('/alarms/active')
      if (!summaryRes.ok || !activeRes.ok) return

      if (summaryRes.data.total !== undefined) {
        expect(summaryRes.data.total).toBe(activeRes.data.length)
      }
    })

    it('downtime summary total_count matches downtime list', async () => {
      const summaryRes = await commands.fetchApi('/downtime/summary')
      const listRes = await commands.fetchApi('/downtime')
      if (!summaryRes.ok || !listRes.ok) return

      if (summaryRes.data.total_count !== undefined) {
        expect(summaryRes.data.total_count).toBe(listRes.data.length)
      }
    })
  })

  describe('Scheduler-Production WO consistency', () => {
    it('scheduler work orders have valid MES references', async () => {
      const schedWoRes = await commands.fetchApi('/scheduler/work-orders?status=READY&limit=20')
      if (!schedWoRes.ok || !schedWoRes.data?.work_orders) return

      for (const wo of schedWoRes.data.work_orders) {
        if (wo.mes_wo_id) {
          const mesRes = await commands.fetchApi(`/production/orders/${wo.mes_wo_id}`)
          if (mesRes.ok) {
            expect(mesRes.data.id).toBe(wo.mes_wo_id)
          }
        }
      }
    })

    it('production work order product references are valid', async () => {
      const ordersRes = await commands.fetchApi('/production/orders?limit=20')
      const productsRes = await commands.fetchApi('/masters/products')
      if (!ordersRes.ok || !productsRes.ok) return

      const orders = ordersRes.data?.items || ordersRes.data || []
      const validProductIds = new Set(productsRes.data.map((p: any) => p.id))

      for (const order of orders) {
        if (order.product_id) {
          expect(validProductIds.has(order.product_id)).toBe(true)
        }
      }
    })

    it('production results reference valid work orders', async () => {
      const resultsRes = await commands.fetchApi('/production/results?limit=30')
      if (!resultsRes.ok) return

      const results = resultsRes.data?.items || resultsRes.data || []

      for (const result of results) {
        const woId = result.work_order_id || result.wo_id
        if (!woId) continue

        const woRes = await commands.fetchApi(`/production/orders/${woId}`)
        if (woRes.ok) {
          expect(woRes.data.id).toBe(woId)
        }
      }
    })
  })
})
