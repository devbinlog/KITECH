import { describe, it, expect, afterAll } from 'vitest'
import { commands } from 'vitest/browser'

const APP_URL = 'http://localhost:3000'

async function login() {
  await commands.goto(`${APP_URL}/login`)
  await commands.fillByRole('textbox', '사용자 ID', 'admin')
  await commands.fillByLabel('비밀번호', 'admin123')
  await commands.clickByRole('button', '로그인')
  await commands.waitForUrl('^(?!.*\\/login)', 10_000)
}

afterAll(async () => {
  await commands.closeAppPage()
})

/**
 * 현장 작업자 일일 업무 시나리오
 *
 * 페르소나: 김현장 (CNC 오퍼레이터, 경력 5년)
 * - 아침에 출근해서 오늘 할 작업 확인
 * - 작업 시작/완료 보고
 * - 불량 발생 시 NCR 등록
 * - 설비 상태 모니터링
 */
describe('현장 작업자 - 일일 업무', () => {

  it('아침 출근: 대시보드에서 오늘 현황 확인', async () => {
    await login()
    await commands.goto(`${APP_URL}/`)

    const hasEquipTotal = await commands.isVisibleByText('전체 설비', 10_000)
    expect(hasEquipTotal).toBe(true)

    const hasRunning = await commands.isVisibleByText('가동중 설비')
    expect(hasRunning).toBe(true)

    const hasActiveWork = await commands.isVisibleByText('진행중 작업')
    expect(hasActiveWork).toBe(true)

    const hasCompleted = await commands.isVisibleByText('완료 작업')
    expect(hasCompleted).toBe(true)
  })

  it('작업지시 확인: 오늘 작업 탭 조회', async () => {
    await login()
    await commands.goto(`${APP_URL}/production/orders`)

    const hasHeader = await commands.isVisibleByText('작업지시', 15_000)
    expect(hasHeader).toBe(true)

    // 오늘 작업 탭이 기본으로 선택됨
    const hasTodayTab = await commands.isVisibleByRole('button', '오늘 작업', 3_000)
    expect(hasTodayTab).toBe(true)

    // 테이블 또는 빈 상태 확인
    const hasTable = await commands.isVisibleBySelector('table', 5_000)
    const hasEmpty = await commands.isVisibleByText('없습니다', 3_000)
    expect(hasTable || hasEmpty).toBe(true)
  })

  it('전체 작업 조회: 전체 탭으로 이동하여 모든 작업 확인', async () => {
    await login()
    await commands.goto(`${APP_URL}/production/orders`)

    const hasHeader = await commands.isVisibleByText('작업지시', 15_000)
    expect(hasHeader).toBe(true)

    await commands.clickByRole('button', '전체')
    await commands.waitForTimeout(1500)

    // 테이블 또는 빈 상태
    const hasTable = await commands.isVisibleBySelector('table', 5_000)
    const hasEmpty = await commands.isVisibleByText('작업지시가 없습니다', 3_000)
    expect(hasTable || hasEmpty).toBe(true)

    // 테이블이 있으면 상태 배지 확인
    if (hasTable) {
      const hasAnyStatus = await commands.isVisibleByText('대기|진행중|완료', 3_000)
      expect(hasAnyStatus).toBe(true)
    }
  })

  it('작업 시작: READY 상태 작업지시 확인', async () => {
    await login()
    await commands.goto(`${APP_URL}/production/orders?view=all`)
    await commands.waitForTimeout(2000)

    const hasHeader = await commands.isVisibleByText('작업지시', 15_000)
    expect(hasHeader).toBe(true)

    // API로 READY 상태 작업 확인
    const result = await commands.fetchApi('/production/orders?view=all&limit=10')
    expect(result.ok).toBe(true)

    const readyOrders = result.data.items.filter((wo: any) => wo.status === 'READY')
    // If READY orders exist, verify the status UI shows "대기"
    if (readyOrders.length > 0) {
      const hasReady = await commands.isVisibleByText('대기', 5_000)
      expect(hasReady).toBe(true)
    }
  })

  it('설비 현황 확인: 대시보드 설비 섹션', async () => {
    await login()
    await commands.goto(`${APP_URL}/`)

    const hasSection = await commands.isVisibleByText('설비 현황', 10_000)
    expect(hasSection).toBe(true)

    // 설비 카드 또는 설비 목록 확인
    const hasCards = await commands.isVisibleBySelector('[class*="card"]', 5_000)
    expect(hasCards).toBe(true)
  })

  it('설비 관리 페이지: 설비 카드 및 상태 확인', async () => {
    await login()
    await commands.goto(`${APP_URL}/master/equipments`)

    const hasHeader = await commands.isVisibleByText('설비 관리', 15_000)
    expect(hasHeader).toBe(true)

    // 설비 카드나 빈 상태 확인
    const hasGrid = await commands.isVisibleBySelector('.grid', 5_000)
    const hasEmpty = await commands.isVisibleByText('등록된 설비가 없습니다', 3_000)
    expect(hasGrid || hasEmpty).toBe(true)

    // 미들웨어 상태 표시
    const hasMiddleware = await commands.isVisibleByText('미들웨어', 5_000)
    expect(hasMiddleware).toBe(true)
  })

  it('불량 발생: NCR 페이지 접근 및 생성 모달 확인', async () => {
    await login()
    await commands.goto(`${APP_URL}/quality/ncr`)

    const hasHeader = await commands.isVisibleByText('부적합 관리', 15_000)
    expect(hasHeader).toBe(true)

    // NCR 생성 버튼
    const hasCreateBtn = await commands.isVisibleByRole('button', 'NCR 생성')
    expect(hasCreateBtn).toBe(true)

    // 모달 열기
    await commands.clickByRole('button', 'NCR 생성')
    await commands.waitForTimeout(500)

    const hasModal = await commands.isVisibleBySelector('[role="dialog"], .fixed.inset-0', 5_000)
    expect(hasModal).toBe(true)

    // 취소
    await commands.clickByRole('button', '취소')
    await commands.waitForTimeout(500)
  })

  it('생산실적 조회: 통계 카드와 테이블 확인', async () => {
    await login()
    await commands.goto(`${APP_URL}/production/results`)

    const hasHeader = await commands.isVisibleByText('생산 실적', 15_000)
    expect(hasHeader).toBe(true)

    // 통계 카드 확인
    const cards = ['총 실적', '양품', '불량', '수율']
    for (const card of cards) {
      const hasCard = await commands.isVisibleByText(card, 5_000)
      expect(hasCard).toBe(true)
    }

    // 실적 등록 버튼
    const hasRegisterBtn = await commands.isVisibleByRole('button', '실적 등록')
    expect(hasRegisterBtn).toBe(true)
  })

  it('전체 워크플로우: 대시보드 -> 작업지시 -> 실적', async () => {
    await login()

    // Step 1: 대시보드
    await commands.goto(`${APP_URL}/`)
    const hasDashboard = await commands.isVisibleByText('전체 설비', 10_000)
    expect(hasDashboard).toBe(true)

    // Step 2: 작업지시
    await commands.goto(`${APP_URL}/production/orders`)
    const hasOrders = await commands.isVisibleByText('작업지시', 10_000)
    expect(hasOrders).toBe(true)

    // Step 3: 생산실적
    await commands.goto(`${APP_URL}/production/results`)
    const hasResults = await commands.isVisibleByText('생산 실적', 10_000)
    expect(hasResults).toBe(true)
  })
})
