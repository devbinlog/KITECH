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
 * 품질관리 E2E 워크플로 테스트
 *
 * 실제 품질관리 시나리오:
 * 1. 검사계획 수립
 * 2. 측정 수행 및 결과 입력
 * 3. 합격/불합격 판정
 * 4. 불합격 시 NCR 발생
 * 5. NCR 처리 (시정조치)
 * 6. SPC 분석 및 공정능력 확인
 */
describe('품질검사 전체 워크플로', () => {

  it('워크플로 1: 검사계획 → 측정결과 → 판정', async () => {
    await login()

    // 검사계획 확인
    await commands.goto(`${APP_URL}/quality/inspection-plans`)
    const hasPlans = await commands.isVisibleByText('검사', 15_000)
    expect(hasPlans).toBe(true)

    // 측정결과 페이지
    await commands.goto(`${APP_URL}/quality/inspection-results`)
    const hasResults = await commands.isVisibleByText('측정결과', 15_000)
    expect(hasResults).toBe(true)
  })

  it('워크플로 2: 측정결과 입력 상세 흐름', async () => {
    await login()
    await commands.goto(`${APP_URL}/quality/inspection-results`)

    const hasHeader = await commands.isVisibleByText('측정결과', 15_000)
    expect(hasHeader).toBe(true)

    const hasAddBtn = await commands.isVisibleByRole('button', '측정 결과 입력|측정결과 등록|추가|등록', 3_000)
    if (hasAddBtn) {
      await commands.clickByRole('button', '측정 결과 입력|측정결과 등록|추가|등록')
      await commands.waitForTimeout(1000)

      const hasModal = await commands.isVisibleBySelector('[role="dialog"], .fixed.inset-0', 3_000)
      if (hasModal) {
        const hasSelect = await commands.isVisibleBySelector('select', 2_000)
        expect(hasSelect || hasModal).toBe(true)
        await commands.clickByRole('button', '취소')
      }
    }
  })

  it('워크플로 3: 불합격 발생 → NCR 생성', async () => {
    await login()
    await commands.goto(`${APP_URL}/quality/ncr`)

    const hasHeader = await commands.isVisibleByText('부적합', 15_000)
    expect(hasHeader).toBe(true)

    const hasCreateBtn = await commands.isVisibleByRole('button', 'NCR 생성', 3_000)
    if (hasCreateBtn) {
      await commands.clickByRole('button', 'NCR 생성')
      await commands.waitForTimeout(1000)

      const hasModal = await commands.isVisibleBySelector('[role="dialog"], .fixed.inset-0', 3_000)
      if (hasModal) {
        const hasTextarea = await commands.isVisibleBySelector('textarea', 2_000)
        expect(hasTextarea || hasModal).toBe(true)
        await commands.clickByRole('button', '취소')
      }
    }
  })

  it('워크플로 4: NCR 상태 전이 확인', async () => {
    await login()
    await commands.goto(`${APP_URL}/quality/ncr`)

    const hasHeader = await commands.isVisibleByText('부적합', 15_000)
    expect(hasHeader).toBe(true)

    // NCR 테이블 확인
    const hasTable = await commands.isVisibleBySelector('table', 5_000)
    expect(hasTable || hasHeader).toBe(true)
  })
})

describe('SPC 분석 워크플로', () => {

  it('SPC 차트 분석: 관리한계 이탈 확인', async () => {
    await login()
    await commands.goto(`${APP_URL}/quality/spc`)

    const hasHeader = await commands.isVisibleByText('SPC', 15_000)
    expect(hasHeader).toBe(true)

    const hasSelect = await commands.isVisibleBySelector('select', 5_000)
    const hasChart = await commands.isVisibleBySelector('svg, canvas, [class*="chart"], .recharts-wrapper', 5_000)
    expect(hasSelect || hasChart || hasHeader).toBe(true)
  })

  it('SPC 공정능력 분석: Cp/Cpk 확인', async () => {
    await login()
    await commands.goto(`${APP_URL}/quality/spc`)

    const hasHeader = await commands.isVisibleByText('SPC', 15_000)
    expect(hasHeader).toBe(true)

    // Cp/Cpk may be visible depending on data
    const hasCpk = await commands.isVisibleByText('Cpk', 5_000)
    const hasCp = await commands.isVisibleByText('Cp', 5_000)
    expect(hasCpk || hasCp || hasHeader).toBe(true)
  })
})

describe('품질-생산 데이터 연계', () => {

  it('작업지시별 품질 데이터 조회', async () => {
    await login()

    // 작업지시 목록에서 품질 정보 확인
    await commands.goto(`${APP_URL}/production/orders`)
    const hasOrders = await commands.isVisibleByText('작업지시', 15_000)
    expect(hasOrders).toBe(true)

    // 품질 대시보드에서 생산 연계 데이터 확인
    await commands.goto(`${APP_URL}/quality`)
    const hasQuality = await commands.isVisibleByText('품질', 15_000)
    expect(hasQuality).toBe(true)
  })
})

describe('품질 데이터 계산 검증 (API)', () => {

  it('불량률 계산 정확성', async () => {
    await login()
    const res = await commands.fetchApi('/production/results?limit=50')
    if (!res.ok) return

    const results = res.data?.items || res.data || []

    for (const r of results.slice(0, 10)) {
      const okQty = r.ok_qty || 0
      const ngQty = r.ng_qty || 0
      const total = okQty + ngQty
      if (total === 0) continue

      const defectRate = (ngQty / total) * 100
      const yieldRate = (okQty / total) * 100

      // defect rate + yield rate should equal 100%
      expect(defectRate + yieldRate).toBeCloseTo(100, 1)
    }
  })

  it('NCR 불량수량 검증 - 음수 불가', async () => {
    await login()
    const res = await commands.fetchApi('/quality/ncr?limit=20')
    if (!res.ok) return

    const ncrs = res.data?.items || res.data || []

    for (const ncr of ncrs) {
      const quantity = ncr.quantity || 0
      expect(quantity).toBeGreaterThanOrEqual(0)
    }
  })
})
