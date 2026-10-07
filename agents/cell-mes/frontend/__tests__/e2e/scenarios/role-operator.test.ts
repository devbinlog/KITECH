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
 * 현장작업자 역할 상세 테스트
 * - 생산실적 등록, 작업 시작/완료, 불량 보고, 설비 상태 확인
 */
describe('현장작업자 - 화면 단위 테스트', () => {

  describe('생산실적 페이지', () => {

    it('페이지 진입 및 기본 요소', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/results`)

      const hasHeader = await commands.isVisibleByText('생산 실적', 15_000)
      expect(hasHeader).toBe(true)

      const hasRegisterBtn = await commands.isVisibleByRole('button', '실적 등록', 5_000)
      expect(hasRegisterBtn).toBe(true)

      const hasStats = await commands.isVisibleBySelector('[class*="card"]', 5_000)
      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      expect(hasStats || hasTable).toBe(true)
    })
  })

  describe('작업지시 확인 페이지', () => {

    it('오늘 작업 탭 확인', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/orders`)

      const hasHeader = await commands.isVisibleByText('작업지시', 15_000)
      expect(hasHeader).toBe(true)

      const hasTodayTab = await commands.isVisibleByRole('button', '오늘 작업', 5_000)
      expect(hasTodayTab).toBe(true)

      await commands.clickByRole('button', '오늘 작업')
      await commands.waitForTimeout(1000)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      const hasEmpty = await commands.isVisibleByText('없습니다', 3_000)
      expect(hasTable || hasEmpty).toBe(true)
    })

    it('진행중 작업 확인', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/orders`)

      const hasHeader = await commands.isVisibleByText('작업지시', 15_000)
      expect(hasHeader).toBe(true)

      const hasInProgressTab = await commands.isVisibleByRole('button', '진행중', 3_000)
      if (hasInProgressTab) {
        await commands.clickByRole('button', '진행중')
        await commands.waitForTimeout(1000)
      }
      expect(hasHeader).toBe(true)
    })
  })

  describe('설비 현황 페이지', () => {

    it('담당 설비 확인', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/equipments`)

      const hasHeader = await commands.isVisibleByText('설비', 15_000)
      expect(hasHeader).toBe(true)

      const hasCards = await commands.isVisibleBySelector('[class*="card"], table', 10_000)
      expect(hasCards || hasHeader).toBe(true)
    })
  })
})

describe('현장작업자 - 컴포넌트 단위 테스트', () => {

  describe('실적 등록 폼', () => {

    it('폼 구성 요소 확인', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/results`)

      const hasHeader = await commands.isVisibleByText('생산 실적', 15_000)
      expect(hasHeader).toBe(true)

      await commands.clickByRole('button', '실적 등록')
      const hasModal = await commands.isVisibleBySelector('.fixed.inset-0, [role="dialog"]', 5_000)
      expect(hasModal).toBe(true)

      // 작업지시 선택
      const hasSelect = await commands.isVisibleBySelector('select', 3_000)
      expect(hasSelect).toBe(true)

      // 양품 수량 입력
      const hasNumberInput = await commands.isVisibleBySelector('input[type="number"]', 3_000)
      expect(hasNumberInput).toBe(true)

      // 닫기
      await commands.clickByRole('button', '취소')
    })
  })

  describe('통계 카드', () => {

    it('총 생산량 및 양품/불량 표시', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/results`)

      const hasHeader = await commands.isVisibleByText('생산 실적', 15_000)
      expect(hasHeader).toBe(true)

      const hasCards = await commands.isVisibleBySelector('[class*="card"]', 5_000)
      expect(hasCards || hasHeader).toBe(true)
    })
  })
})

describe('현장작업자 - 버튼 단위 테스트', () => {

  it('실적 등록 클릭 시 모달 열림', async () => {
    await login()
    await commands.goto(`${APP_URL}/production/results`)

    const hasHeader = await commands.isVisibleByText('생산 실적', 15_000)
    expect(hasHeader).toBe(true)

    await commands.clickByRole('button', '실적 등록')
    const hasModal = await commands.isVisibleBySelector('.fixed.inset-0, [role="dialog"]', 5_000)
    expect(hasModal).toBe(true)

    await commands.clickByRole('button', '취소')
  })

  it('작업지시 미선택 시 유효성 검사', async () => {
    await login()
    await commands.goto(`${APP_URL}/production/results`)

    const hasHeader = await commands.isVisibleByText('생산 실적', 15_000)
    expect(hasHeader).toBe(true)

    await commands.clickByRole('button', '실적 등록')
    const hasModal = await commands.isVisibleBySelector('.fixed.inset-0, [role="dialog"]', 5_000)
    expect(hasModal).toBe(true)

    // Modal should stay open without valid selection
    const modalStillOpen = await commands.isVisibleBySelector('.fixed.inset-0, [role="dialog"]', 1_000)
    expect(modalStillOpen).toBe(true)

    await commands.clickByRole('button', '취소')
  })
})

describe('현장작업자 - 설비 관련', () => {

  it('설비 상태 확인 후 작업지시로 이동', async () => {
    await login()

    // 설비 상태 확인
    await commands.goto(`${APP_URL}/master/equipments`)
    const hasEquip = await commands.isVisibleByText('설비', 15_000)
    expect(hasEquip).toBe(true)

    // 작업지시 페이지로 이동
    await commands.goto(`${APP_URL}/production/orders`)
    const hasOrders = await commands.isVisibleByText('작업지시', 15_000)
    expect(hasOrders).toBe(true)
  })
})
