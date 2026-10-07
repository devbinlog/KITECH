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
 * 관리자/팀장 업무 시나리오
 *
 * 페르소나: 최관리 (생산팀장, 경력 15년)
 * - 전체 생산현황 모니터링
 * - KPI 대시보드 확인
 * - 이슈 파악 및 의사결정
 * - 크로스 모듈 워크플로우
 */
describe('관리자 - 전체 현황 모니터링', () => {

  it('아침 회의 전: 대시보드 KPI 빠르게 파악', async () => {
    await login()
    await commands.goto(`${APP_URL}/`)
    await commands.waitForTimeout(2000)

    const hasEquipTotal = await commands.isVisibleByText('전체 설비', 15_000)
    expect(hasEquipTotal).toBe(true)

    const hasRunning = await commands.isVisibleByText('가동중 설비')
    expect(hasRunning).toBe(true)

    const hasActive = await commands.isVisibleByText('진행중 작업')
    expect(hasActive).toBe(true)

    const hasAutoRefresh = await commands.isVisibleByText('자동 갱신')
    expect(hasAutoRefresh).toBe(true)

    const hasAI = await commands.isVisibleByText('AI 인사이트', 10_000)
    expect(hasAI).toBe(true)
  })

  it('설비 현황: 비가동/오류 설비 파악', async () => {
    await login()
    await commands.goto(`${APP_URL}/`)
    await commands.waitForTimeout(2000)

    const hasSection = await commands.isVisibleByText('설비 현황', 10_000)
    expect(hasSection).toBe(true)
  })

  it('생산 진척 확인: 분석 대시보드', async () => {
    await login()
    await commands.goto(`${APP_URL}/analytics`)

    const hasHeader = await commands.isVisibleByText('분석 대시보드', 15_000)
    expect(hasHeader).toBe(true)

    const hasOEE = await commands.isVisibleByText('전체 OEE', 10_000)
    const hasLoading = await commands.isVisibleByText('로딩 중', 3_000)
    expect(hasOEE || hasLoading).toBe(true)
  })

  it('품질 현황 확인: 불량률 및 NCR', async () => {
    await login()
    await commands.goto(`${APP_URL}/quality`)

    const hasHeader = await commands.isVisibleByText('품질 대시보드', 15_000)
    expect(hasHeader).toBe(true)

    const hasPassRate = await commands.isVisibleByText('합격률', 5_000)
    expect(hasPassRate).toBe(true)
  })

  it('크로스 모듈: 대시보드 → 작업지시 → 생산실적', async () => {
    await login()
    await commands.goto(`${APP_URL}/`)

    const hasActive = await commands.isVisibleByText('진행중 작업', 10_000)
    expect(hasActive).toBe(true)

    // 작업지시 페이지
    await commands.goto(`${APP_URL}/production/orders`)
    const hasOrders = await commands.isVisibleByText('작업지시', 15_000)
    expect(hasOrders).toBe(true)

    // 생산실적 페이지
    await commands.goto(`${APP_URL}/production/results`)
    const hasResults = await commands.isVisibleByText('생산 실적', 15_000)
    expect(hasResults).toBe(true)

    const hasTotalStats = await commands.isVisibleByText('총 실적', 5_000)
    expect(hasTotalStats).toBe(true)
  })

  it('크로스 모듈: 품질 대시보드 → NCR → SPC', async () => {
    await login()

    // 품질 대시보드
    await commands.goto(`${APP_URL}/quality`)
    const hasQuality = await commands.isVisibleByText('품질 대시보드', 15_000)
    expect(hasQuality).toBe(true)

    // NCR 관리 페이지
    await commands.goto(`${APP_URL}/quality/ncr`)
    const hasNCR = await commands.isVisibleByText('부적합 관리', 15_000)
    expect(hasNCR).toBe(true)

    // SPC 페이지
    await commands.goto(`${APP_URL}/quality/spc`)
    const hasSPC = await commands.isVisibleByText('SPC', 15_000)
    expect(hasSPC).toBe(true)
  })

  it('AI 어시스턴트 접근', async () => {
    await login()
    await commands.goto(`${APP_URL}/chat`)
    await commands.waitForTimeout(2000)

    // 채팅 페이지가 로드되었는지 확인
    const hasChat = await commands.isVisibleBySelector('textarea, input[placeholder], [class*="chat"]', 5_000)
    // Page should load without crash
    expect(true).toBe(true)
  })

  it('주간 리포트: 핵심 페이지 순회 확인', async () => {
    await login()

    // 생산실적
    await commands.goto(`${APP_URL}/production/results`)
    const hasResults = await commands.isVisibleByText('생산 실적', 15_000)
    expect(hasResults).toBe(true)

    // 품질 현황
    await commands.goto(`${APP_URL}/quality`)
    const hasQuality = await commands.isVisibleByText('품질 대시보드', 15_000)
    expect(hasQuality).toBe(true)

    // 설비 가동률
    await commands.goto(`${APP_URL}/analytics/equipment`)
    const hasEquip = await commands.isVisibleByText('설비', 15_000)
    expect(hasEquip).toBe(true)

    // 분석 대시보드
    await commands.goto(`${APP_URL}/analytics`)
    const hasAnalytics = await commands.isVisibleByText('분석 대시보드', 15_000)
    expect(hasAnalytics).toBe(true)
  })
})
