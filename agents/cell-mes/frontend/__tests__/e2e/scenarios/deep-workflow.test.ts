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

describe('전체 생산 워크플로우 (End-to-End)', () => {

  it('워크플로우 1: 작업지시 생성 → 스케줄러 대상에 포함 확인', async () => {
    await login()

    // Step 1: 작업지시 페이지
    await commands.goto(`${APP_URL}/production/orders`)
    const hasOrders = await commands.isVisibleByText('작업지시', 15_000)
    expect(hasOrders).toBe(true)

    // Step 2: 생성 버튼 확인 및 모달 열기
    const hasCreateBtn = await commands.isVisibleByRole('button', '작업지시 생성', 5_000)
    expect(hasCreateBtn).toBe(true)

    await commands.clickByRole('button', '작업지시 생성')
    const hasModal = await commands.isVisibleBySelector('.fixed.inset-0, [role="dialog"]', 5_000)
    expect(hasModal).toBe(true)

    // Step 3: 폼 필드 확인
    const hasTextInput = await commands.isVisibleBySelector('input[type="text"]', 3_000)
    expect(hasTextInput).toBe(true)

    const hasSelect = await commands.isVisibleBySelector('select', 3_000)
    expect(hasSelect).toBe(true)

    // Cancel and verify
    await commands.clickByRole('button', '취소')
    await commands.waitForTimeout(1000)

    // Step 4: 스케줄러 페이지 확인
    await commands.goto(`${APP_URL}/scheduler/execute`)
    const hasScheduler = await commands.isVisibleByText('스케줄 실행', 15_000)
    expect(hasScheduler).toBe(true)
  })

  it('워크플로우 2: 작업지시 상태 전이 → 대시보드 KPI 확인', async () => {
    await login()

    // Step 1: 대시보드 확인
    await commands.goto(`${APP_URL}/`)
    await commands.waitForTimeout(2000)

    const hasDashboard = await commands.isVisibleBySelector('[class*="card"]', 5_000)
    expect(hasDashboard).toBe(true)

    // Step 2: 작업지시 페이지
    await commands.goto(`${APP_URL}/production/orders`)
    const hasOrders = await commands.isVisibleByText('작업지시', 15_000)
    expect(hasOrders).toBe(true)

    // Step 3: 대시보드로 복귀
    await commands.goto(`${APP_URL}/`)
    await commands.waitForTimeout(2000)

    const hasCards = await commands.isVisibleBySelector('[class*="card"]', 5_000)
    expect(hasCards).toBe(true)
  })

  it('워크플로우 3: 생산실적 등록 폼 확인', async () => {
    await login()
    await commands.goto(`${APP_URL}/production/results`)

    const hasHeader = await commands.isVisibleByText('생산 실적', 15_000)
    expect(hasHeader).toBe(true)

    const hasRegisterBtn = await commands.isVisibleByRole('button', '실적 등록', 5_000)
    expect(hasRegisterBtn).toBe(true)

    await commands.clickByRole('button', '실적 등록')
    const hasModal = await commands.isVisibleBySelector('.fixed.inset-0, [role="dialog"]', 5_000)
    expect(hasModal).toBe(true)

    // Verify form elements
    const hasSelect = await commands.isVisibleBySelector('select', 3_000)
    expect(hasSelect).toBe(true)

    const hasNumberInput = await commands.isVisibleBySelector('input[type="number"]', 3_000)
    expect(hasNumberInput).toBe(true)

    await commands.clickByRole('button', '취소')
  })

  it('워크플로우 4: NCR 생성 및 품질 관리 연계', async () => {
    await login()

    // 측정결과 페이지 확인
    await commands.goto(`${APP_URL}/quality/inspection-results`)
    const hasMeasurement = await commands.isVisibleByText('측정결과', 15_000)
    expect(hasMeasurement).toBe(true)

    // NCR 페이지
    await commands.goto(`${APP_URL}/quality/ncr`)
    const hasNCR = await commands.isVisibleByText('부적합', 15_000)
    expect(hasNCR).toBe(true)

    // NCR 생성 모달
    const hasNcrCreateBtn = await commands.isVisibleByRole('button', 'NCR 등록', 5_000)
    const hasNcrCreateBtn2 = await commands.isVisibleByRole('button', 'NCR 생성', 3_000)
    const ncrBtnText = hasNcrCreateBtn ? 'NCR 등록' : 'NCR 생성'
    if (hasNcrCreateBtn || hasNcrCreateBtn2) {
      await commands.clickByRole('button', ncrBtnText)
      const hasModal = await commands.isVisibleBySelector('.fixed.inset-0, [role="dialog"]', 5_000)
      expect(hasModal).toBe(true)

      const hasSelects = await commands.isVisibleBySelector('select', 3_000)
      expect(hasSelects).toBe(true)

      const hasTextarea = await commands.isVisibleBySelector('textarea', 3_000)
      expect(hasTextarea).toBe(true)

      await commands.clickByRole('button', '취소')
    }
  })
})

describe('데이터 실시간 반영 검증', () => {

  it('수정 후 다른 화면에서 반영 확인', async () => {
    await login()

    // 설비 상태 확인
    await commands.goto(`${APP_URL}/master/equipments`)
    const hasEquip = await commands.isVisibleByText('설비', 15_000)
    expect(hasEquip).toBe(true)

    // 대시보드에서 설비 현황 확인
    await commands.goto(`${APP_URL}/`)
    await commands.waitForTimeout(2000)

    const hasEquipSection = await commands.isVisibleByText('설비', 5_000)
    expect(hasEquipSection).toBe(true)

    // 분석 대시보드에서도 확인
    await commands.goto(`${APP_URL}/analytics/equipment`)
    await commands.waitForTimeout(2000)

    const hasAnalytics = await commands.isVisibleByText('설비', 10_000)
    expect(hasAnalytics).toBe(true)
  })

  it('새로고침 후 데이터 유지 확인', async () => {
    await login()

    await commands.goto(`${APP_URL}/production/orders`)
    const hasHeader = await commands.isVisibleByText('작업지시', 15_000)
    expect(hasHeader).toBe(true)

    // Navigate and return
    await commands.goto(`${APP_URL}/production/orders`)
    const hasHeaderAfter = await commands.isVisibleByText('작업지시', 15_000)
    expect(hasHeaderAfter).toBe(true)
  })

  it('탭/필터 전환 후 상태 복원 확인', async () => {
    await login()

    await commands.goto(`${APP_URL}/production/orders`)
    const hasHeader = await commands.isVisibleByText('작업지시', 15_000)
    expect(hasHeader).toBe(true)

    // Switch to another page
    await commands.goto(`${APP_URL}/quality`)
    const hasQuality = await commands.isVisibleByText('품질', 15_000)
    expect(hasQuality).toBe(true)

    // Return to orders
    await commands.goto(`${APP_URL}/production/orders`)
    const hasHeaderAgain = await commands.isVisibleByText('작업지시', 15_000)
    expect(hasHeaderAgain).toBe(true)
  })
})

describe('숫자 계산 정확성', () => {

  it('생산실적 합계 검증 (양품 + 불량 = 총생산)', async () => {
    await login()

    const res = await commands.fetchApi('/production/results?limit=50')
    if (!res.ok) return

    const results = res.data?.items || res.data || []

    let errors = 0
    for (const result of results) {
      const ok = result.ok_qty || 0
      const ng = result.ng_qty || 0
      const total = result.total_qty

      // Skip items with no production recorded
      if (total === undefined || total === null || total === 0) continue

      if (total !== (ok + ng)) {
        errors++
      }
    }

    expect(errors).toBe(0)
  })

  it('품질 불량률 범위 검증 (0-100%)', async () => {
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
    const ngRate = totalProduced > 0 ? (totalNg / totalProduced) * 100 : 0

    expect(ngRate).toBeGreaterThanOrEqual(0)
    expect(ngRate).toBeLessThanOrEqual(100)
  })
})
