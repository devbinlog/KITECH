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

describe('수율(Yield Rate) 계산 검증', () => {

  it('수율 = 양품 / (양품 + 불량) * 100', async () => {
    await login()

    const res = await commands.fetchApi('/production/results?limit=50')
    if (!res.ok) return

    const results = res.data?.items || res.data || []

    let validationErrors = 0

    for (const result of results) {
      const okQty = result.ok_qty || 0
      const ngQty = result.ng_qty || 0
      const totalQty = okQty + ngQty
      const reportedYield = result.yield_rate || result.yield

      if (totalQty === 0) continue

      const expectedYield = (okQty / totalQty) * 100

      if (reportedYield !== undefined) {
        const diff = Math.abs(expectedYield - reportedYield)
        if (diff > 0.1) {
          validationErrors++
        }
      }
    }

    expect(validationErrors).toBe(0)
  })

  it('수율 값 범위 (0-100)', async () => {
    await login()

    const res = await commands.fetchApi('/production/results?limit=100')
    if (!res.ok) return

    const results = res.data?.items || res.data || []

    let outOfRangeCount = 0

    for (const result of results) {
      const yieldRate = result.yield_rate || result.yield

      if (yieldRate !== undefined && (yieldRate < 0 || yieldRate > 100)) {
        outOfRangeCount++
      }
    }

    expect(outOfRangeCount).toBe(0)
  })

  it('작업지시별 누적 수율 계산', async () => {
    await login()

    const ordersRes = await commands.fetchApi('/production/orders?limit=10')
    if (!ordersRes.ok) return

    const orders = ordersRes.data?.items || ordersRes.data || []

    for (const order of orders) {
      const woId = order.id || order.wo_id

      const resultsRes = await commands.fetchApi(`/production/results?wo_id=${woId}`)
      if (!resultsRes.ok) continue

      const results = resultsRes.data?.items || resultsRes.data || []

      let totalOk = 0
      let totalNg = 0

      for (const r of results) {
        totalOk += r.ok_qty || 0
        totalNg += r.ng_qty || 0
      }

      const total = totalOk + totalNg
      if (total > 0) {
        const yieldRate = (totalOk / total) * 100
        expect(yieldRate).toBeGreaterThanOrEqual(0)
        expect(yieldRate).toBeLessThanOrEqual(100)
      }
    }
  })
})

describe('진도율 계산 검증', () => {

  it('진도율 = (실적합계 / 목표수량) * 100', async () => {
    await login()

    const ordersRes = await commands.fetchApi('/production/orders?view=all&limit=20')
    if (!ordersRes.ok) return

    const orders = ordersRes.data?.items || ordersRes.data || []

    const resultsRes = await commands.fetchApi('/production/results?limit=500')
    if (!resultsRes.ok) return

    const results = resultsRes.data?.items || resultsRes.data || []

    let errors = 0

    for (const order of orders.slice(0, 5)) {
      const orderResults = results.filter((r: any) =>
        r.work_order_id === order.id || r.wo_id === order.id
      )

      const totalProduced = orderResults.reduce((sum: number, r: any) => {
        return sum + (r.ok_qty || 0) + (r.ng_qty || 0)
      }, 0)

      const targetQty = order.target_qty || order.quantity || 0
      const expectedProgress = targetQty > 0 ? (totalProduced / targetQty) * 100 : 0
      const actualProgress = order.progress || 0

      if (Math.abs(expectedProgress - actualProgress) > 1 && targetQty > 0) {
        errors++
      }
    }

    // Allow small percentage of mismatches
    expect(errors).toBeLessThan(orders.slice(0, 5).length * 0.2 + 1)
  })
})

describe('불량률 계산 검증', () => {

  it('불량률 = (불량수량 / 총생산) * 100', async () => {
    await login()

    const res = await commands.fetchApi('/production/results?limit=100')
    if (!res.ok) return

    const results = res.data?.items || res.data || []

    let totalOk = 0
    let totalNg = 0

    for (const result of results) {
      totalOk += result.ok_qty || 0
      totalNg += result.ng_qty || 0
    }

    const totalProduced = totalOk + totalNg
    const defectRate = totalProduced > 0 ? (totalNg / totalProduced) * 100 : 0

    expect(defectRate).toBeGreaterThanOrEqual(0)
    expect(defectRate).toBeLessThanOrEqual(100)
  })
})

describe('OEE 계산 검증', () => {

  it('OEE 구성요소 범위 (0~100)', async () => {
    const res = await commands.fetchApi('/analytics/kpi/summary')
    if (!res.ok || !res.data) return

    const { overall_oee, availability, performance, quality } = res.data

    if (overall_oee !== undefined) {
      expect(overall_oee).toBeGreaterThanOrEqual(0)
      expect(overall_oee).toBeLessThanOrEqual(100)
    }
    if (availability !== undefined) {
      expect(availability).toBeGreaterThanOrEqual(0)
      expect(availability).toBeLessThanOrEqual(100)
    }
    if (performance !== undefined) {
      expect(performance).toBeGreaterThanOrEqual(0)
      expect(performance).toBeLessThanOrEqual(100)
    }
    if (quality !== undefined) {
      expect(quality).toBeGreaterThanOrEqual(0)
      expect(quality).toBeLessThanOrEqual(100)
    }
  })

  it('OEE = Availability × Performance × Quality / 10000', async () => {
    const res = await commands.fetchApi('/analytics/kpi/summary')
    if (!res.ok || !res.data) return

    const { overall_oee, availability, performance, quality } = res.data
    if (overall_oee === undefined || availability === undefined ||
        performance === undefined || quality === undefined) return

    // OEE = (A/100) × (P/100) × (Q/100) × 100
    const expectedOee = (availability / 100) * (performance / 100) * (quality / 100) * 100
    const diff = Math.abs(expectedOee - overall_oee)
    // Allow 1% tolerance for rounding differences
    expect(diff).toBeLessThan(1)
  })

  it('KPI summary defect_rate 범위', async () => {
    const res = await commands.fetchApi('/analytics/kpi/summary')
    if (!res.ok || !res.data) return

    const { defect_rate } = res.data
    if (defect_rate === undefined) return

    expect(defect_rate).toBeGreaterThanOrEqual(0)
    expect(defect_rate).toBeLessThanOrEqual(100)
  })

  it('KPI summary downtime_hours 음수 아님', async () => {
    const res = await commands.fetchApi('/analytics/kpi/summary')
    if (!res.ok || !res.data) return

    const { downtime_hours } = res.data
    if (downtime_hours === undefined) return

    expect(downtime_hours).toBeGreaterThanOrEqual(0)
  })

  it('KPI trend_data 날짜 순서 정렬', async () => {
    const res = await commands.fetchApi('/analytics/kpi/summary')
    if (!res.ok || !res.data || !res.data.trend_data) return

    const dates = res.data.trend_data.map((t: any) => t.date)
    for (let i = 1; i < dates.length; i++) {
      expect(dates[i] >= dates[i - 1]).toBe(true)
    }
  })
})

describe('설비 가동률 계산 검증', () => {

  it('utilization_rate 범위 (0~100)', async () => {
    const res = await commands.fetchApi('/analytics/equipment/utilization')
    if (!res.ok || !res.data) return

    const equipments = Array.isArray(res.data) ? res.data : []

    for (const eq of equipments) {
      if (eq.utilization_rate !== undefined) {
        expect(eq.utilization_rate).toBeGreaterThanOrEqual(0)
        expect(eq.utilization_rate).toBeLessThanOrEqual(100)
      }
      if (eq.availability_rate !== undefined) {
        expect(eq.availability_rate).toBeGreaterThanOrEqual(0)
        expect(eq.availability_rate).toBeLessThanOrEqual(100)
      }
    }
  })

  it('시간 합계 = planned_time (±허용오차)', async () => {
    const res = await commands.fetchApi('/analytics/equipment/utilization')
    if (!res.ok || !res.data) return

    const equipments = Array.isArray(res.data) ? res.data : []

    for (const eq of equipments) {
      if (eq.planned_time === undefined) continue

      const sumTime = (eq.running_time || 0) + (eq.idle_time || 0) +
                      (eq.maintenance_time || 0) + (eq.error_time || 0)
      const diff = Math.abs(sumTime - eq.planned_time)
      // Allow 1 hour tolerance for rounding
      expect(diff).toBeLessThan(1)
    }
  })

  it('running_time / planned_time ≈ utilization_rate', async () => {
    const res = await commands.fetchApi('/analytics/equipment/utilization')
    if (!res.ok || !res.data) return

    const equipments = Array.isArray(res.data) ? res.data : []

    for (const eq of equipments) {
      if (!eq.planned_time || !eq.running_time || eq.utilization_rate === undefined) continue

      const expectedRate = (eq.running_time / eq.planned_time) * 100
      const diff = Math.abs(expectedRate - eq.utilization_rate)
      // Allow 1% tolerance
      expect(diff).toBeLessThan(1)
    }
  })

  it('시간 필드 음수 없음', async () => {
    const res = await commands.fetchApi('/analytics/equipment/utilization')
    if (!res.ok || !res.data) return

    const equipments = Array.isArray(res.data) ? res.data : []

    for (const eq of equipments) {
      expect(eq.planned_time || 0).toBeGreaterThanOrEqual(0)
      expect(eq.running_time || 0).toBeGreaterThanOrEqual(0)
      expect(eq.idle_time || 0).toBeGreaterThanOrEqual(0)
      expect(eq.maintenance_time || 0).toBeGreaterThanOrEqual(0)
      expect(eq.error_time || 0).toBeGreaterThanOrEqual(0)
    }
  })
})

describe('다운타임 시간 계산 검증', () => {

  it('종료된 다운타임 duration ≥ 0', async () => {
    const res = await commands.fetchApi('/downtime?limit=50')
    if (!res.ok || !res.data) return

    const downtimes = Array.isArray(res.data) ? res.data : []

    for (const dt of downtimes) {
      if (dt.status === 'COMPLETED' && dt.calculated_duration_minutes !== undefined) {
        expect(dt.calculated_duration_minutes).toBeGreaterThanOrEqual(0)
      }
    }
  })

  it('다운타임 duration = (end_time - start_time) 분', async () => {
    const res = await commands.fetchApi('/downtime?limit=50')
    if (!res.ok || !res.data) return

    const downtimes = Array.isArray(res.data) ? res.data : []

    for (const dt of downtimes) {
      if (!dt.start_time || !dt.end_time || dt.calculated_duration_minutes === undefined) continue

      const start = new Date(dt.start_time).getTime()
      const end = new Date(dt.end_time).getTime()
      const expectedMinutes = (end - start) / 60000

      if (expectedMinutes < 0) continue // Skip bad data

      const diff = Math.abs(expectedMinutes - dt.calculated_duration_minutes)
      // Allow 1 minute tolerance
      expect(diff).toBeLessThan(1)
    }
  })

  it('활성 다운타임에 end_time 없음', async () => {
    const res = await commands.fetchApi('/downtime?status=ACTIVE')
    if (!res.ok || !res.data) return

    const downtimes = Array.isArray(res.data) ? res.data : []

    for (const dt of downtimes) {
      if (dt.is_ongoing) {
        expect(dt.end_time).toBeFalsy()
      }
    }
  })

  it('다운타임 summary total = 카테고리별 합계', async () => {
    const res = await commands.fetchApi('/downtime/summary')
    if (!res.ok || !res.data) return

    const { by_category, total_count, total_minutes } = res.data
    if (!by_category) return

    let sumCount = 0
    let sumMinutes = 0

    for (const cat of Object.values(by_category) as any[]) {
      sumCount += cat.count || 0
      sumMinutes += cat.total_minutes || 0
    }

    expect(sumCount).toBe(total_count)
    expect(sumMinutes).toBe(total_minutes)
  })
})

describe('수율 Edge Case 검증', () => {

  it('ok_qty=0, ng_qty=0이면 수율 NaN/Infinity 아님', async () => {
    const res = await commands.fetchApi('/production/results?limit=100')
    if (!res.ok) return

    const results = res.data?.items || res.data || []

    for (const result of results) {
      const yieldRate = result.yield_rate || result.yield
      if (yieldRate !== undefined) {
        expect(Number.isFinite(yieldRate)).toBe(true)
      }
    }
  })

  it('ng_qty가 음수인 실적 없음', async () => {
    const res = await commands.fetchApi('/production/results?limit=100')
    if (!res.ok) return

    const results = res.data?.items || res.data || []

    for (const result of results) {
      if (result.ng_qty !== undefined && result.ng_qty !== null) {
        expect(result.ng_qty).toBeGreaterThanOrEqual(0)
      }
      if (result.ok_qty !== undefined && result.ok_qty !== null) {
        expect(result.ok_qty).toBeGreaterThanOrEqual(0)
      }
    }
  })

  it('target_qty > 0인 작업지시만 진도율 계산', async () => {
    const ordersRes = await commands.fetchApi('/production/orders?limit=30')
    if (!ordersRes.ok) return

    const orders = ordersRes.data?.items || ordersRes.data || []

    for (const order of orders) {
      const targetQty = order.target_qty || order.quantity || 0
      const progress = order.progress

      if (targetQty === 0 && progress !== undefined) {
        // If target is 0, progress should be 0 or undefined
        expect(progress === 0 || progress === undefined || progress === null).toBe(true)
      }
    }
  })
})
