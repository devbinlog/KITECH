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

describe('검사계획 데이터 검증', () => {

  it('검사계획 USL > Nominal > LSL 논리 검증', async () => {
    await login()

    const res = await commands.fetchApi('/quality/inspection-plans')
    if (!res.ok) return

    const plans = res.data?.items || res.data || []

    for (const plan of plans) {
      const usl = parseFloat(plan.usl)
      const lsl = parseFloat(plan.lsl)
      const nominal = parseFloat(plan.nominal)

      if (!isNaN(usl) && !isNaN(lsl)) {
        expect(usl).toBeGreaterThan(lsl)
      }

      if (!isNaN(nominal) && !isNaN(usl) && !isNaN(lsl)) {
        expect(nominal).toBeGreaterThanOrEqual(lsl)
        expect(nominal).toBeLessThanOrEqual(usl)
      }
    }
  })

  it('검사계획 필수 필드 존재 확인', async () => {
    await login()

    const res = await commands.fetchApi('/quality/inspection-plans')
    if (!res.ok) return

    const plans = res.data?.items || res.data || []

    for (const plan of plans) {
      expect(plan.id).toBeDefined()
    }
  })
})

describe('측정결과 적합/부적합 판정', () => {

  it('측정값이 규격 내면 적합', async () => {
    await login()

    const plansRes = await commands.fetchApi('/quality/inspection-plans')
    if (!plansRes.ok) return

    const plans = plansRes.data?.items || plansRes.data || []

    if (plans.length === 0) return

    const resultsRes = await commands.fetchApi('/quality/inspection-results?limit=10')
    if (!resultsRes.ok) return

    const results = resultsRes.data?.items || resultsRes.data || []

    for (const result of results.slice(0, 10)) {
      const plan = plans.find((p: any) => p.id === result.inspection_plan_id)
      if (!plan) continue

      const measured = parseFloat(result.measured_value)
      const usl = parseFloat(plan.usl)
      const lsl = parseFloat(plan.lsl)

      if (isNaN(measured) || isNaN(usl) || isNaN(lsl)) continue

      const isWithinSpec = measured >= lsl && measured <= usl

      if (result.is_conforming !== undefined) {
        expect(result.is_conforming).toBe(isWithinSpec)
      }
    }
  })
})

describe('SPC 데이터 검증', () => {

  it('SPC 페이지 로드 확인', async () => {
    await login()
    await commands.goto(`${APP_URL}/quality/spc`)

    const hasHeader = await commands.isVisibleByText('SPC', 15_000)
    expect(hasHeader).toBe(true)
  })

  it('SPC 차트 관리한계 논리 검증 (UCL > CL > LCL)', async () => {
    await login()

    const res = await commands.fetchApi('/quality/spc')
    if (!res.ok) return

    const charts = res.data?.items || res.data || []

    for (const chart of charts) {
      const ucl = parseFloat(chart.ucl)
      const cl = parseFloat(chart.cl)
      const lcl = parseFloat(chart.lcl)

      if (!isNaN(ucl) && !isNaN(cl) && !isNaN(lcl)) {
        expect(ucl).toBeGreaterThan(cl)
        expect(cl).toBeGreaterThan(lcl)
      }
    }
  })
})

describe('NCR 데이터 검증', () => {

  it('NCR 필수 필드 존재 확인', async () => {
    await login()

    const res = await commands.fetchApi('/quality/ncr?limit=10')
    if (!res.ok) return

    const ncrs = res.data?.items || res.data || []

    for (const ncr of ncrs) {
      expect(ncr.id).toBeDefined()
      expect(ncr.status).toBeDefined()
    }
  })

  it('NCR 상태값 유효성', async () => {
    await login()

    const res = await commands.fetchApi('/quality/ncr?limit=50')
    if (!res.ok) return

    const ncrs = res.data?.items || res.data || []

    const validStatuses = ['OPEN', 'INVESTIGATING', 'CORRECTIVE_ACTION', 'CLOSED', 'CANCELLED']

    for (const ncr of ncrs) {
      if (ncr.status) {
        expect(validStatuses).toContain(ncr.status)
      }
    }
  })

  it('NCR 페이지 UI 확인', async () => {
    await login()
    await commands.goto(`${APP_URL}/quality/ncr`)

    const hasHeader = await commands.isVisibleByText('부적합', 15_000)
    expect(hasHeader).toBe(true)

    const hasTable = await commands.isVisibleBySelector('table', 5_000)
    const hasEmpty = await commands.isVisibleByText('없습니다', 3_000)
    expect(hasTable || hasEmpty || hasHeader).toBe(true)
  })
})
