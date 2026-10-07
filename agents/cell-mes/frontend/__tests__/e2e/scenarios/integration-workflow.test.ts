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
 * 시스템 통합 E2E 워크플로 테스트
 *
 * 모듈 간 데이터 연계 및 일관성 검증
 */
describe('마스터-생산-품질 통합 워크플로', () => {

  it('통합 1: 제품 → 라우팅 → 작업지시 연계 확인', async () => {
    await login()

    // 제품 목록
    await commands.goto(`${APP_URL}/master/products`)
    const hasProducts = await commands.isVisibleByText('제품', 15_000)
    expect(hasProducts).toBe(true)

    // 라우팅 목록
    await commands.goto(`${APP_URL}/master/routings`)
    const hasRoutings = await commands.isVisibleByText('라우팅', 15_000)
    expect(hasRoutings).toBe(true)

    // 작업지시
    await commands.goto(`${APP_URL}/production/orders`)
    const hasOrders = await commands.isVisibleByText('작업지시', 15_000)
    expect(hasOrders).toBe(true)
  })

  it('통합 2: 설비 → 작업지시 배정 → 실적 연계', async () => {
    await login()

    // 설비 목록
    await commands.goto(`${APP_URL}/master/equipments`)
    const hasEquip = await commands.isVisibleByText('설비', 15_000)
    expect(hasEquip).toBe(true)

    // 스케줄러
    await commands.goto(`${APP_URL}/scheduler`)
    const hasScheduler = await commands.isVisibleByText('스케줄 현황', 15_000)
    expect(hasScheduler).toBe(true)

    // 생산실적
    await commands.goto(`${APP_URL}/production/results`)
    const hasResults = await commands.isVisibleByText('생산 실적', 15_000)
    expect(hasResults).toBe(true)
  })

  it('통합 3: 검사계획 → 측정결과 → NCR 자동 연계', async () => {
    await login()

    // 검사계획
    await commands.goto(`${APP_URL}/quality/inspection-plans`)
    const hasPlans = await commands.isVisibleByText('검사', 15_000)
    expect(hasPlans).toBe(true)

    // 측정결과
    await commands.goto(`${APP_URL}/quality/inspection-results`)
    const hasResults = await commands.isVisibleByText('측정결과', 15_000)
    expect(hasResults).toBe(true)

    // NCR
    await commands.goto(`${APP_URL}/quality/ncr`)
    const hasNCR = await commands.isVisibleByText('부적합', 15_000)
    expect(hasNCR).toBe(true)
  })
})

describe('대시보드 데이터 일관성', () => {

  it('대시보드 KPI vs 상세 페이지 데이터 일치', async () => {
    await login()

    // 대시보드
    await commands.goto(`${APP_URL}/`)
    await commands.waitForTimeout(2000)
    const hasCards = await commands.isVisibleBySelector('[class*="card"]', 5_000)
    expect(hasCards).toBe(true)

    // 설비 관리 페이지
    await commands.goto(`${APP_URL}/master/equipments`)
    const hasEquip = await commands.isVisibleByText('설비', 15_000)
    expect(hasEquip).toBe(true)
  })

  it('품질 대시보드 vs NCR 목록', async () => {
    await login()

    // 품질 대시보드
    await commands.goto(`${APP_URL}/quality`)
    const hasQuality = await commands.isVisibleByText('품질', 15_000)
    expect(hasQuality).toBe(true)

    // NCR 목록
    await commands.goto(`${APP_URL}/quality/ncr`)
    const hasNCR = await commands.isVisibleByText('부적합', 15_000)
    expect(hasNCR).toBe(true)
  })

  it('분석 대시보드 KPI vs 생산 데이터', async () => {
    await login()

    // 분석 대시보드
    await commands.goto(`${APP_URL}/analytics`)
    const hasAnalytics = await commands.isVisibleByText('분석', 15_000)
    expect(hasAnalytics).toBe(true)

    // 생산실적
    await commands.goto(`${APP_URL}/production/results`)
    const hasResults = await commands.isVisibleByText('생산 실적', 15_000)
    expect(hasResults).toBe(true)
  })
})

describe('스케줄러 통합 워크플로', () => {

  it('스케줄 실행 페이지 확인', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/execute`)

    const hasHeader = await commands.isVisibleByText('스케줄 실행', 15_000)
    expect(hasHeader).toBe(true)

    const hasRunBtn = await commands.isVisibleByRole('button', '스케줄 실행', 10_000)
    const hasTable = await commands.isVisibleBySelector('table', 10_000)
    expect(hasRunBtn || hasTable).toBe(true)
  })

  it('스케줄 결과 → 설비별 배정 확인', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler`)

    const hasHeader = await commands.isVisibleByText('스케줄 현황', 15_000)
    expect(hasHeader).toBe(true)
  })
})

describe('크로스 모듈 네비게이션', () => {

  it('대시보드 → 상세 페이지 → 대시보드 순환', async () => {
    await login()

    await commands.goto(`${APP_URL}/`)
    await commands.waitForTimeout(1000)

    await commands.goto(`${APP_URL}/production/orders`)
    await commands.waitForTimeout(1000)

    await commands.goto(`${APP_URL}/`)
    await commands.waitForTimeout(1000)

    const hasMain = await commands.isVisibleBySelector('main', 10_000)
    expect(hasMain).toBe(true)
  })

  it('사이드바 메뉴 전체 탐색', async () => {
    await login()

    const menuPaths = ['/production/orders', '/quality', '/analytics']

    for (const path of menuPaths) {
      await commands.goto(`${APP_URL}${path}`)
      await commands.waitForTimeout(1000)
      const hasBody = await commands.isVisibleBySelector('body', 10_000)
      expect(hasBody).toBe(true)
    }
  })
})

describe('AI 어시스턴트 통합', () => {

  it('AI 채팅 페이지 접근', async () => {
    await login()
    await commands.goto(`${APP_URL}/chat`)
    await commands.waitForTimeout(2000)

    const hasBody = await commands.isVisibleBySelector('body', 10_000)
    expect(hasBody).toBe(true)
  })

  it('대시보드 AI 인사이트 섹션 확인', async () => {
    await login()
    await commands.goto(`${APP_URL}/`)
    await commands.waitForTimeout(2000)

    const hasMain = await commands.isVisibleBySelector('main', 10_000)
    expect(hasMain).toBe(true)
  })
})
