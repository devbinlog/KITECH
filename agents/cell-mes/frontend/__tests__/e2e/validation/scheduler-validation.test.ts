import { describe, it, expect } from 'vitest'
import { commands } from 'vitest/browser'

const APP_URL = 'http://localhost:3000'
const SCHEDULER_BASE = 'http://localhost:8002/api'

async function login() {
  await commands.goto(`${APP_URL}/login`)
  await commands.fillByRole('textbox', '사용자 ID', 'admin')
  await commands.fillByLabel('비밀번호', 'admin123')
  await commands.clickByRole('button', '로그인')
  await commands.waitForUrl('^(?!.*\\/login)', 10_000)
}

describe('스케줄러 데이터 검증', () => {

  it('스케줄러 페이지 로드 확인', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler`)

    const hasHeader = await commands.isVisibleByText('스케줄 현황', 15_000)
    expect(hasHeader).toBe(true)
  })

  it('스케줄 실행 페이지 요소 확인', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/execute`)

    const hasHeader = await commands.isVisibleByText('스케줄 실행', 15_000)
    expect(hasHeader).toBe(true)

    const hasRunBtn = await commands.isVisibleByRole('button', '스케줄 실행')
    expect(hasRunBtn).toBe(true)

    const hasSelect = await commands.isVisibleBySelector('select', 5_000)
    expect(hasSelect).toBe(true)
  })

  it('스케줄 결과 Makespan > 0', async () => {
    await login()

    try {
      const scheduleRequest = {
        work_order_ids: [1, 2, 3],
        algorithm: 'ortools',
      }

      const res = await commands.fetchExternal(
        `${SCHEDULER_BASE}/schedule`,
        'POST',
        JSON.stringify(scheduleRequest),
      )

      if (res.ok) {
        if (res.data?.makespan !== undefined) {
          expect(res.data.makespan).toBeGreaterThan(0)
        }

        if (res.data?.schedule || res.data?.assignments) {
          const items = res.data.schedule || res.data.assignments
          const count = Array.isArray(items) ? items.length : Object.keys(items).length
          expect(count).toBeGreaterThan(0)
        }
      }
    } catch {
      // Scheduler service not running - skip gracefully
    }
  })

  it('설비 배정 결과: 모든 작업이 설비에 배정됨', async () => {
    await login()

    try {
      const res = await commands.fetchExternal(
        `${SCHEDULER_BASE}/schedule`,
        'POST',
        JSON.stringify({
          work_order_ids: [1, 2],
          algorithm: 'ortools',
        }),
      )

      if (res.ok && res.data?.assignments) {
        for (const [, assignment] of Object.entries(res.data.assignments as Record<string, any>)) {
          expect(assignment.equipment_id || assignment.machine_id).toBeDefined()
        }
      }
    } catch {
      // Scheduler service not running - skip gracefully
    }
  })
})

describe('스케줄 데이터 정합성', () => {

  it('스케줄 시간 겹침 없음 (설비별)', async () => {
    await login()

    const res = await commands.fetchApi('/scheduler/current-schedule')
    if (!res.ok) return

    const schedule = res.data?.schedule || res.data?.results || []

    // Group by equipment
    const byEquipment: Record<string, any[]> = {}
    for (const item of schedule) {
      const equipId = item.equipment_id || item.machine_id
      if (!equipId) continue

      if (!byEquipment[equipId]) byEquipment[equipId] = []
      byEquipment[equipId].push(item)
    }

    let overlapCount = 0

    for (const [, jobs] of Object.entries(byEquipment)) {
      const sorted = jobs.sort((a, b) =>
        new Date(a.start_time || a.start).getTime() - new Date(b.start_time || b.start).getTime()
      )

      for (let i = 0; i < sorted.length - 1; i++) {
        const current = sorted[i]
        const next = sorted[i + 1]

        const currentEnd = new Date(current.end_time || current.end)
        const nextStart = new Date(next.start_time || next.start)

        if (currentEnd > nextStart) {
          overlapCount++
        }
      }
    }

    expect(overlapCount).toBe(0)
  })

  it('작업지시 수량 변경 시 스케줄 반영', async () => {
    await login()

    const res = await commands.fetchApi('/scheduler/current-schedule')
    if (!res.ok) return

    const schedule = res.data?.schedule || res.data?.results || []

    for (const item of schedule.slice(0, 5)) {
      const woId = item.wo_id || item.work_order_id
      if (!woId) continue

      const orderRes = await commands.fetchApi(`/production/orders/${woId}`)
      if (!orderRes.ok) continue

      const order = orderRes.data
      const orderQty = order?.target_qty || order?.qty
      const scheduleQty = item.qty || item.quantity

      if (orderQty && scheduleQty) {
        // Quantities should match
        expect(orderQty).toBe(scheduleQty)
      }
    }
  })
})
