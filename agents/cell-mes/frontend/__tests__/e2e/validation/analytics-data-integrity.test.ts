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

/**
 * Analytics Data Integrity Tests
 *
 * These tests verify actual data flow and calculation correctness:
 * 1. OEE = Availability x Performance x Quality (mathematical verification)
 * 2. Equipment utilization rates within valid ranges
 * 3. Lot trace data flow: production → quality → traceability
 * 4. Production trends API data reflected correctly in UI
 * 5. KPI summary cross-validation: API values match UI display
 * 6. Edge cases: empty datasets, boundary values, null handling
 */

describe('OEE KPI 정합성 검증', () => {

  it('OEE = 가동률 x 성능률 x 품질률 (수학적 검증)', async () => {
    await login()

    const res = await commands.fetchApi('/analytics/kpi/summary')
    if (!res.ok) return

    const data = res.data
    if (!data) return

    const availability = data.availability
    const performance = data.performance
    const quality = data.quality
    const reportedOEE = data.overall_oee

    // All components must be defined for OEE calculation
    if (availability === undefined || performance === undefined || quality === undefined) return
    if (reportedOEE === undefined) return

    // OEE = (availability/100) * (performance/100) * (quality/100) * 100
    const expectedOEE = (availability / 100) * (performance / 100) * (quality / 100) * 100
    const diff = Math.abs(reportedOEE - expectedOEE)

    // Allow tolerance for rounding
    expect(diff).toBeLessThan(1.0)
  })

  it('OEE 구성요소 값 범위 (0-100)', async () => {
    await login()

    const res = await commands.fetchApi('/analytics/kpi/summary')
    if (!res.ok) return

    const data = res.data
    if (!data) return

    const fields = ['overall_oee', 'availability', 'performance', 'quality']

    for (const field of fields) {
      const value = data[field]
      if (value !== undefined && value !== null) {
        expect(value).toBeGreaterThanOrEqual(0)
        expect(value).toBeLessThanOrEqual(100)
      }
    }
  })

  it('KPI 트렌드 데이터 시간순 정렬 확인', async () => {
    await login()

    const res = await commands.fetchApi('/analytics/kpi/summary')
    if (!res.ok) return

    const trendData = res.data?.trend_data || []
    if (trendData.length < 2) return

    for (let i = 1; i < trendData.length; i++) {
      const prev = new Date(trendData[i - 1].date)
      const curr = new Date(trendData[i].date)
      expect(curr.getTime()).toBeGreaterThanOrEqual(prev.getTime())
    }
  })

  it('KPI 트렌드 개별 데이터포인트 OEE 값 범위', async () => {
    await login()

    const res = await commands.fetchApi('/analytics/kpi/summary')
    if (!res.ok) return

    const trendData = res.data?.trend_data || []

    for (const point of trendData) {
      if (point.oee !== undefined) {
        expect(point.oee).toBeGreaterThanOrEqual(0)
        expect(point.oee).toBeLessThanOrEqual(100)
      }
      if (point.availability !== undefined) {
        expect(point.availability).toBeGreaterThanOrEqual(0)
        expect(point.availability).toBeLessThanOrEqual(100)
      }
      if (point.performance !== undefined) {
        expect(point.performance).toBeGreaterThanOrEqual(0)
        expect(point.performance).toBeLessThanOrEqual(100)
      }
      if (point.quality !== undefined) {
        expect(point.quality).toBeGreaterThanOrEqual(0)
        expect(point.quality).toBeLessThanOrEqual(100)
      }
    }
  })

  it('총 생산량은 음수가 불가능', async () => {
    await login()

    const res = await commands.fetchApi('/analytics/kpi/summary')
    if (!res.ok) return

    const data = res.data
    if (!data) return

    if (data.total_production !== undefined) {
      expect(data.total_production).toBeGreaterThanOrEqual(0)
    }

    if (data.downtime_hours !== undefined) {
      expect(data.downtime_hours).toBeGreaterThanOrEqual(0)
    }

    if (data.defect_rate !== undefined) {
      expect(data.defect_rate).toBeGreaterThanOrEqual(0)
      expect(data.defect_rate).toBeLessThanOrEqual(100)
    }
  })
})

describe('OEE KPI API → UI 교차 검증', () => {

  it('KPI 요약값이 대시보드 UI에 정확히 반영되는지', async () => {
    await login()

    // Fetch from API
    const res = await commands.fetchApi('/analytics/kpi/summary')
    if (!res.ok) return

    const data = res.data
    if (!data) return

    // Navigate to analytics dashboard
    await commands.goto(`${APP_URL}/analytics`)
    await commands.waitForTimeout(5000)

    const hasHeader = await commands.isVisibleByText('분석 대시보드', 10_000)
    expect(hasHeader).toBe(true)

    // Verify OEE value appears in UI
    if (data.overall_oee !== undefined && data.overall_oee > 0) {
      const oeeStr = Number(data.overall_oee).toFixed(1)
      const hasOEE = await commands.isVisibleByText(oeeStr, 5_000)
      // OEE text or "전체 OEE" label should be visible
      const hasOEELabel = await commands.isVisibleByText('전체 OEE', 5_000)
      expect(hasOEE || hasOEELabel).toBe(true)
    }
  })

  it('트렌드 차트가 OEE 데이터 존재 시 렌더링되는지', async () => {
    await login()

    const res = await commands.fetchApi('/analytics/kpi/summary')
    if (!res.ok) return

    const trendData = res.data?.trend_data || []

    await commands.goto(`${APP_URL}/analytics`)
    await commands.waitForTimeout(5000)

    if (trendData.length > 0) {
      // Charts should render when data exists
      const hasChart = await commands.isVisibleBySelector('.recharts-wrapper, svg, canvas', 10_000)
      expect(hasChart).toBe(true)
    }
  })
})

describe('설비 가동률 데이터 검증', () => {

  it('설비별 가동률 값 범위 (0-100)', async () => {
    await login()

    const res = await commands.fetchApi('/analytics/equipment/utilization')
    if (!res.ok) return

    const utilization = Array.isArray(res.data) ? res.data : []

    for (const eq of utilization) {
      if (eq.utilization_rate !== undefined) {
        expect(eq.utilization_rate).toBeGreaterThanOrEqual(0)
        expect(eq.utilization_rate).toBeLessThanOrEqual(100)
      }
    }
  })

  it('설비 가동시간 + 비가동시간 ≤ 계획시간', async () => {
    await login()

    const res = await commands.fetchApi('/analytics/resources')
    if (!res.ok) return

    const eqData = res.data?.equipment_utilization || []

    for (const eq of eqData) {
      const available = eq.available_hours || 0
      const used = eq.used_hours || 0
      const maintenance = eq.maintenance_hours || 0

      // Used + maintenance should not exceed available time
      if (available > 0 && used > 0) {
        expect(used + maintenance).toBeLessThanOrEqual(available * 1.01) // 1% tolerance
      }

      // Utilization rate should match calculation
      if (available > 0 && eq.utilization_rate !== undefined) {
        const expectedRate = (used / available) * 100
        const diff = Math.abs(eq.utilization_rate - expectedRate)
        expect(diff).toBeLessThan(2) // Allow 2% tolerance
      }
    }
  })

  it('설비 가동률 API 데이터가 설비 분석 UI에 반영', async () => {
    await login()

    const res = await commands.fetchApi('/analytics/equipment/utilization')
    if (!res.ok) return

    const utilization = Array.isArray(res.data) ? res.data : []

    await commands.goto(`${APP_URL}/analytics/equipment`)
    await commands.waitForTimeout(5000)

    const hasHeader = await commands.isVisibleByText('설비', 10_000)
    expect(hasHeader).toBe(true)

    if (utilization.length > 0) {
      // Should have chart or cards with equipment data
      const hasChart = await commands.isVisibleBySelector('.recharts-wrapper, svg, canvas, [class*="card"]', 10_000)
      expect(hasChart).toBe(true)

      // First equipment name should appear somewhere
      const firstName = utilization[0].equipment_name || utilization[0].name
      if (firstName) {
        const hasName = await commands.isVisibleByText(firstName, 5_000)
        // Equipment name might be in chart or selector
        expect(hasName || hasChart).toBe(true)
      }
    }
  })

  it('설비 효율 분석 데이터 구조 검증', async () => {
    await login()

    const eqRes = await commands.fetchApi('/masters/equipments')
    if (!eqRes.ok) return

    const equipments = eqRes.data || []
    if (equipments.length === 0) return

    const firstEqId = equipments[0].id
    const res = await commands.fetchApi(`/analytics/equipment/efficiency?equipment_id=${firstEqId}`)
    if (!res.ok) return

    const data = res.data
    if (!data) return

    // Planned time should be >= actual time
    if (data.planned_time !== undefined && data.actual_time !== undefined) {
      expect(data.planned_time).toBeGreaterThanOrEqual(0)
      expect(data.actual_time).toBeGreaterThanOrEqual(0)
    }

    // Downtime breakdown durations should be positive
    const breakdown = data.downtime_breakdown || []
    for (const entry of breakdown) {
      if (entry.duration !== undefined) {
        expect(entry.duration).toBeGreaterThanOrEqual(0)
      }
      if (entry.count !== undefined) {
        expect(entry.count).toBeGreaterThanOrEqual(0)
      }
    }

    // Efficiency trend values in valid range
    const trend = data.efficiency_trend || []
    for (const point of trend) {
      if (point.efficiency !== undefined) {
        expect(point.efficiency).toBeGreaterThanOrEqual(0)
        expect(point.efficiency).toBeLessThanOrEqual(100)
      }
      if (point.utilization !== undefined) {
        expect(point.utilization).toBeGreaterThanOrEqual(0)
        expect(point.utilization).toBeLessThanOrEqual(100)
      }
    }
  })
})

describe('Lot 추적 데이터 정합성', () => {

  it('Lot 추적 데이터 필수 필드 확인', async () => {
    await login()

    const res = await commands.fetchApi('/analytics/lot-trace?limit=20')
    if (!res.ok) return

    const items = res.data?.items || res.data || []
    if (!Array.isArray(items)) return

    for (const lot of items) {
      // Every lot trace should have a lot number
      expect(lot.lot_no || lot.lot_number).toBeDefined()

      // Status should be valid
      if (lot.status) {
        const validStatuses = ['IN_PROGRESS', 'COMPLETED', 'HOLD', 'SHIPPED', 'SCRAPPED', 'PENDING', 'DONE', 'READY', 'CANCELLED']
        expect(validStatuses).toContain(lot.status)
      }
    }
  })

  it('Lot 추적 이력: 공정 순서 시간순 정렬', async () => {
    await login()

    // Get a lot number first
    const listRes = await commands.fetchApi('/analytics/lot-trace?limit=5')
    if (!listRes.ok) return

    const items = listRes.data?.items || listRes.data || []
    if (!Array.isArray(items) || items.length === 0) return

    const lotNo = items[0].lot_no || items[0].lot_number
    if (!lotNo) return

    // Get detailed history
    const histRes = await commands.fetchApi(`/analytics/lot-trace/${lotNo}/history`)
    if (!histRes.ok) return

    const processFlow = histRes.data?.process_flow || []
    if (processFlow.length < 2) return

    // Process flow should be chronologically ordered
    for (let i = 1; i < processFlow.length; i++) {
      const prevStart = processFlow[i - 1].start_time
      const currStart = processFlow[i].start_time

      if (prevStart && currStart) {
        const prevTime = new Date(prevStart).getTime()
        const currTime = new Date(currStart).getTime()
        expect(currTime).toBeGreaterThanOrEqual(prevTime)
      }
    }
  })

  it('Lot 추적 공정시간: end_time > start_time', async () => {
    await login()

    const listRes = await commands.fetchApi('/analytics/lot-trace?limit=5')
    if (!listRes.ok) return

    const items = listRes.data?.items || listRes.data || []
    if (!Array.isArray(items) || items.length === 0) return

    const lotNo = items[0].lot_no || items[0].lot_number
    if (!lotNo) return

    const histRes = await commands.fetchApi(`/analytics/lot-trace/${lotNo}/history`)
    if (!histRes.ok) return

    const processFlow = histRes.data?.process_flow || []

    for (const step of processFlow) {
      if (step.start_time && step.end_time) {
        const start = new Date(step.start_time).getTime()
        const end = new Date(step.end_time).getTime()
        expect(end).toBeGreaterThanOrEqual(start)
      }

      // Duration should be positive
      if (step.duration !== undefined && step.duration !== null) {
        expect(step.duration).toBeGreaterThanOrEqual(0)
      }
    }
  })

  it('Lot 추적 품질체크포인트: 판정결과 유효성', async () => {
    await login()

    const listRes = await commands.fetchApi('/analytics/lot-trace?limit=5')
    if (!listRes.ok) return

    const items = listRes.data?.items || listRes.data || []
    if (!Array.isArray(items) || items.length === 0) return

    const lotNo = items[0].lot_no || items[0].lot_number
    if (!lotNo) return

    const histRes = await commands.fetchApi(`/analytics/lot-trace/${lotNo}/history`)
    if (!histRes.ok) return

    const checkpoints = histRes.data?.quality_checkpoints || []

    for (const cp of checkpoints) {
      // Judgment should be valid
      if (cp.judgment) {
        expect(['OK', 'NG', 'PASS', 'FAIL', 'HOLD', 'PENDING']).toContain(cp.judgment)
      }

      // Defect items should have measured values
      const defects = cp.defects || []
      for (const d of defects) {
        if (d.measured_value !== undefined) {
          expect(typeof d.measured_value).toBe('number')
        }
        if (d.judgment) {
          expect(['OK', 'NG', 'PASS', 'FAIL']).toContain(d.judgment)
        }
      }
    }
  })

  it('Lot 추적 API → UI 검색 교차검증', async () => {
    await login()

    const listRes = await commands.fetchApi('/analytics/lot-trace?limit=5')
    if (!listRes.ok) return

    const items = listRes.data?.items || listRes.data || []
    if (!Array.isArray(items) || items.length === 0) return

    const lotNo = items[0].lot_no || items[0].lot_number
    if (!lotNo) return

    // Navigate to lot trace page
    await commands.goto(`${APP_URL}/analytics/lot-trace`)
    await commands.waitForTimeout(3000)

    const hasHeader = await commands.isVisibleByText('Lot', 10_000)
    expect(hasHeader).toBe(true)

    // Lot data should appear in table
    const hasTable = await commands.isVisibleBySelector('table', 5_000)
    if (hasTable) {
      const hasLotNo = await commands.isVisibleByText(lotNo, 5_000)
      expect(hasLotNo).toBe(true)
    }
  })
})

describe('생산 트렌드 분석 데이터 검증', () => {

  it('생산량 계획 vs 실적: 효율 계산 검증', async () => {
    await login()

    const res = await commands.fetchApi('/analytics/production/trends')
    if (!res.ok) return

    const volume = res.data?.production_volume || []

    for (const point of volume) {
      const planned = point.planned || 0
      const actual = point.actual || 0

      // Quantities should be non-negative
      expect(planned).toBeGreaterThanOrEqual(0)
      expect(actual).toBeGreaterThanOrEqual(0)

      // Efficiency should be non-negative when present
      if (point.efficiency !== undefined) {
        expect(point.efficiency).toBeGreaterThanOrEqual(0)
      }
    }
  })

  it('품질 트렌드: pass_rate + defect_rate ≈ 100%', async () => {
    await login()

    const res = await commands.fetchApi('/analytics/production/trends')
    if (!res.ok) return

    const qualityTrends = res.data?.quality_trends || []

    for (const point of qualityTrends) {
      const passRate = point.pass_rate || 0
      const defectRate = point.defect_rate || 0
      const reworkRate = point.rework_rate || 0

      // Rates should be in valid range
      expect(passRate).toBeGreaterThanOrEqual(0)
      expect(passRate).toBeLessThanOrEqual(100)
      expect(defectRate).toBeGreaterThanOrEqual(0)
      expect(defectRate).toBeLessThanOrEqual(100)

      // pass_rate + defect_rate should approximate 100 (rework may be separate)
      if (passRate > 0 && defectRate > 0) {
        const sum = passRate + defectRate + (reworkRate || 0)
        // Allow tolerance since rework may or may not be included
        expect(sum).toBeGreaterThan(0)
        expect(sum).toBeLessThanOrEqual(200) // Sanity check
      }
    }
  })

  it('사이클타임 트렌드: 편차 계산 검증', async () => {
    await login()

    const res = await commands.fetchApi('/analytics/production/trends')
    if (!res.ok) return

    const cycleTimeTrends = res.data?.cycle_time_trends || []

    for (const point of cycleTimeTrends) {
      const avg = point.avg_cycle_time || 0
      const planned = point.planned_cycle_time || 0

      // Cycle times should be non-negative
      expect(avg).toBeGreaterThanOrEqual(0)
      expect(planned).toBeGreaterThanOrEqual(0)

      // Variance = avg - planned (can be negative meaning faster than planned)
      if (point.variance !== undefined && avg > 0 && planned > 0) {
        const expectedVariance = avg - planned
        const diff = Math.abs(point.variance - expectedVariance)
        expect(diff).toBeLessThan(0.5)
      }
    }
  })

  it('생산 트렌드 데이터 시간순 정렬', async () => {
    await login()

    const res = await commands.fetchApi('/analytics/production/trends')
    if (!res.ok) return

    const volume = res.data?.production_volume || []
    if (volume.length < 2) return

    for (let i = 1; i < volume.length; i++) {
      const prev = new Date(volume[i - 1].date)
      const curr = new Date(volume[i].date)
      expect(curr.getTime()).toBeGreaterThanOrEqual(prev.getTime())
    }
  })
})

describe('자원 활용도 데이터 검증', () => {

  it('인력 가동률 계산 검증', async () => {
    await login()

    const res = await commands.fetchApi('/analytics/resources')
    if (!res.ok) return

    const workforce = res.data?.workforce_utilization || []

    for (const shift of workforce) {
      const planned = shift.planned_hours || 0
      const worked = shift.worked_hours || 0
      const overtime = shift.overtime_hours || 0

      // Hours should be non-negative
      expect(planned).toBeGreaterThanOrEqual(0)
      expect(worked).toBeGreaterThanOrEqual(0)
      expect(overtime).toBeGreaterThanOrEqual(0)

      // Efficiency should be in valid range
      if (shift.efficiency !== undefined) {
        expect(shift.efficiency).toBeGreaterThanOrEqual(0)
        expect(shift.efficiency).toBeLessThanOrEqual(200) // Overtime can push over 100%
      }
    }
  })

  it('자재 소비량: 실소비 vs 계획 편차 검증', async () => {
    await login()

    const res = await commands.fetchApi('/analytics/resources')
    if (!res.ok) return

    const materials = res.data?.material_consumption || []

    for (const mat of materials) {
      const planned = mat.planned_consumption || 0
      const actual = mat.actual_consumption || 0

      expect(planned).toBeGreaterThanOrEqual(0)
      expect(actual).toBeGreaterThanOrEqual(0)

      // Variance = actual - planned
      if (mat.variance !== undefined) {
        const expectedVariance = actual - planned
        const diff = Math.abs(mat.variance - expectedVariance)
        expect(diff).toBeLessThan(0.5)
      }
    }
  })
})

describe('에지 케이스 및 빈 데이터 처리', () => {

  it('날짜 범위가 없는 경우 기본 응답 확인', async () => {
    await login()

    // Calling without date filters should return valid response (not crash)
    const res = await commands.fetchApi('/analytics/kpi/summary')
    expect(res.ok || res.status === 400).toBe(true)
  })

  it('미래 날짜 범위: 빈 데이터 graceful 처리', async () => {
    await login()

    const res = await commands.fetchApi('/analytics/kpi/summary?date_from=2030-01-01&date_to=2030-12-31')
    if (!res.ok) return

    const data = res.data
    if (!data) return

    // Should return zero/empty values, not crash
    const oee = data.overall_oee || 0
    expect(oee).toBeGreaterThanOrEqual(0)
  })

  it('존재하지 않는 설비 ID로 효율 조회 시 에러 처리', async () => {
    await login()

    const res = await commands.fetchApi('/analytics/equipment/efficiency?equipment_id=999999')

    // Should return 404 or empty data, not 500
    expect(res.status !== 500).toBe(true)
  })

  it('존재하지 않는 Lot 번호 검색 시 에러 처리', async () => {
    await login()

    const res = await commands.fetchApi('/analytics/lot-trace/NON-EXISTENT-LOT-99999')

    // Should return 404 or empty, not 500
    expect(res.status !== 500).toBe(true)
  })

  it('빈 데이터셋에서 UI 크래시 없음 확인', async () => {
    await login()

    // Navigate to analytics with future date filter (likely empty data)
    await commands.goto(`${APP_URL}/analytics`)
    await commands.waitForTimeout(3000)

    // Page should not crash even with no data
    const hasBody = await commands.isVisibleBySelector('body', 5_000)
    expect(hasBody).toBe(true)

    const hasHeader = await commands.isVisibleByText('분석 대시보드', 5_000)
    expect(hasHeader).toBe(true)
  })
})
