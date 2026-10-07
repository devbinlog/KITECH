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

async function solveViaApi() {
  const res = await commands.fetchApi(
    '/scheduler/solve',
    'POST',
    JSON.stringify({
      horizon_hours: 24,
      include_running: false,
      solver_type: 'OR_TOOLS',
      time_limit_sec: 60,
      auto_apply: false,
    })
  )
  return res
}

describe('Scheduler Data Integrity', () => {
  it('no machine time overlap in schedule', async () => {
    await login()

    const res = await solveViaApi()
    if (!res.ok || !res.data?.scheduling_result) return

    const result = res.data.scheduling_result
    const tasksByMachine: Record<string, { start: number; end: number }[]> = {}

    for (const task of result.scheduled_tasks) {
      if (!tasksByMachine[task.machine_id]) tasksByMachine[task.machine_id] = []
      tasksByMachine[task.machine_id].push({
        start: task.start_time,
        end: task.end_time,
      })
    }

    for (const [machineId, tasks] of Object.entries(tasksByMachine)) {
      const sorted = tasks.sort((a, b) => a.start - b.start)
      for (let i = 1; i < sorted.length; i++) {
        expect(sorted[i].start).toBeGreaterThanOrEqual(sorted[i - 1].end)
      }
    }
  })

  it('makespan > 0', async () => {
    await login()

    const res = await solveViaApi()
    if (!res.ok || !res.data?.scheduling_result) return

    const result = res.data.scheduling_result
    expect(result.statistics.makespan_seconds).toBeGreaterThan(0)
  })

  it('start_time < end_time for all tasks', async () => {
    await login()

    const res = await solveViaApi()
    if (!res.ok || !res.data?.scheduling_result) return

    const result = res.data.scheduling_result
    for (const task of result.scheduled_tasks) {
      expect(task.start_time).toBeLessThan(task.end_time)
    }
  })

  it('quantity > 0 for all tasks', async () => {
    await login()

    const res = await solveViaApi()
    if (!res.ok || !res.data?.scheduling_result) return

    const result = res.data.scheduling_result
    for (const task of result.scheduled_tasks) {
      expect(task.quantity).toBeGreaterThan(0)
    }
  })

  it('scheduled WO IDs exist in actual work orders', async () => {
    await login()

    const res = await solveViaApi()
    if (!res.ok || !res.data?.scheduling_result) return

    const result = res.data.scheduling_result
    const scheduledWoIds = result.scheduled_tasks.map((t: any) => t.work_order_id)

    const woRes = await commands.fetchApi('/scheduler/work-orders?status=READY&limit=1000')
    if (!woRes.ok) return

    const actualWoIds = new Set(woRes.data.items.map((wo: any) => wo.id))

    for (const woId of scheduledWoIds) {
      expect(actualWoIds.has(woId)).toBe(true)
    }
  })

  it('assigned machines exist in equipment availability', async () => {
    await login()

    const res = await solveViaApi()
    if (!res.ok || !res.data?.scheduling_result) return

    const result = res.data.scheduling_result
    const scheduledMachineIds = result.scheduled_tasks.map((t: any) => t.machine_id)

    const eqRes = await commands.fetchApi('/scheduler/equipment-availability')
    if (!eqRes.ok) return

    const actualMachineIds = new Set(eqRes.data.map((eq: any) => eq.machine_id))

    for (const machineId of scheduledMachineIds) {
      expect(actualMachineIds.has(machineId)).toBe(true)
    }
  })

  it('machine_utilization values are 0-100% range', async () => {
    await login()

    const res = await solveViaApi()
    if (!res.ok || !res.data?.scheduling_result) return

    const result = res.data.scheduling_result
    if (!result.statistics.machine_utilization) return

    for (const [machineId, utilization] of Object.entries(
      result.statistics.machine_utilization
    )) {
      const util = utilization as number
      expect(util).toBeGreaterThanOrEqual(0)
      expect(util).toBeLessThanOrEqual(100)
    }
  })

  it('total_tasks matches scheduled_tasks array length', async () => {
    await login()

    const res = await solveViaApi()
    if (!res.ok || !res.data?.scheduling_result) return

    const result = res.data.scheduling_result
    expect(result.statistics.total_tasks).toBe(result.scheduled_tasks.length)
  })
})
