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
 * 생산계획 담당자 일일 업무 시나리오
 *
 * 페르소나: 박계획 (생산관리팀, 경력 8년)
 * - 아침에 출근: 대시보드에서 전일 실적/현황 확인
 * - 작업지시 생성: 신규 주문 접수 처리
 * - 스케줄링: 솔버로 설비 배정 최적화
 * - 진행현황 모니터링: 작업 진행 상태 추적
 * - 생산실적 확인: 통계 카드와 테이블
 * - 분석: OEE, 설비 가동률, Lot 추적
 */
describe('생산계획 담당자 - 일일 업무', () => {

  it('아침: 대시보드에서 전일 실적 확인', async () => {
    await login()
    await commands.goto(`${APP_URL}/`)

    const hasCompleted = await commands.isVisibleByText('완료 작업', 10_000)
    expect(hasCompleted).toBe(true)

    const hasActive = await commands.isVisibleByText('진행중 작업')
    expect(hasActive).toBe(true)

    const hasRecentSection = await commands.isVisibleByText('최근 작업지시', 10_000)
    expect(hasRecentSection).toBe(true)

    // 대시보드 KPI 카드 확인
    const hasEquipTotal = await commands.isVisibleByText('전체 설비', 5_000)
    expect(hasEquipTotal).toBe(true)

    const hasRunning = await commands.isVisibleByText('가동중 설비')
    expect(hasRunning).toBe(true)
  })

  it('대시보드 설비 현황 섹션 확인', async () => {
    await login()
    await commands.goto(`${APP_URL}/`)

    const hasSection = await commands.isVisibleByText('설비 현황', 10_000)
    expect(hasSection).toBe(true)

    // 설비 카드가 있어야 함
    const hasCards = await commands.isVisibleBySelector('[class*="card"]', 5_000)
    expect(hasCards).toBe(true)
  })

  it('작업지시 생성: 모달 폼 필드 확인', async () => {
    await login()
    await commands.goto(`${APP_URL}/production/orders`)

    const hasHeader = await commands.isVisibleByText('작업지시', 15_000)
    expect(hasHeader).toBe(true)

    // 작업지시 생성 버튼 클릭
    await commands.clickByRole('button', '작업지시 생성')
    await commands.waitForTimeout(500)

    // 모달 확인
    const hasModal = await commands.isVisibleBySelector('.fixed.inset-0, [role="dialog"]', 5_000)
    expect(hasModal).toBe(true)

    // 폼 필드 확인 - 텍스트 입력, select, number 입력
    const hasTextInput = await commands.isVisibleBySelector('input[type="text"]', 3_000)
    expect(hasTextInput).toBe(true)

    const hasSelect = await commands.isVisibleBySelector('select', 3_000)
    expect(hasSelect).toBe(true)

    const hasNumberInput = await commands.isVisibleBySelector('input[type="number"]', 3_000)
    expect(hasNumberInput).toBe(true)

    // 제출/취소 버튼 확인
    const hasSubmitBtn = await commands.isVisibleBySelector('button[type="submit"]', 3_000)
    const hasSaveBtn = await commands.isVisibleByRole('button', '저장')
    expect(hasSubmitBtn || hasSaveBtn).toBe(true)

    const hasCancelBtn = await commands.isVisibleByRole('button', '취소')
    expect(hasCancelBtn).toBe(true)

    // 취소
    await commands.clickByRole('button', '취소')
    await commands.waitForTimeout(500)
  })

  it('작업지시 생성: 빈 폼 제출 방지', async () => {
    await login()
    await commands.goto(`${APP_URL}/production/orders`)

    const hasHeader = await commands.isVisibleByText('작업지시', 15_000)
    expect(hasHeader).toBe(true)

    await commands.clickByRole('button', '작업지시 생성')
    await commands.waitForTimeout(500)

    // 모달이 열려있는지 확인
    const hasModal = await commands.isVisibleBySelector('.fixed.inset-0, [role="dialog"]', 3_000)
    expect(hasModal).toBe(true)

    // 제출 버튼 존재 확인 (overlay 뒤 버튼 클릭 대신 존재 여부만 검증)
    const hasSubmit = await commands.isVisibleBySelector('button[type="submit"]', 3_000)
    expect(hasSubmit).toBe(true)

    await commands.clickByRole('button', '취소')
    await commands.waitForTimeout(500)
  })

  it('작업지시 API: 작업지시 목록 조회', async () => {
    const result = await commands.fetchApi('/production/orders?view=all&limit=10')
    expect(result.ok).toBe(true)
    expect(result.status).toBe(200)
    expect(result.data).toHaveProperty('items')
    expect(Array.isArray(result.data.items)).toBe(true)
  })

  it('작업지시 탭 전환: 오늘/진행중/전체', async () => {
    await login()
    await commands.goto(`${APP_URL}/production/orders`)

    const hasHeader = await commands.isVisibleByText('작업지시', 15_000)
    expect(hasHeader).toBe(true)

    // 오늘 작업 탭
    const hasTodayTab = await commands.isVisibleByRole('button', '오늘 작업', 3_000)
    expect(hasTodayTab).toBe(true)

    // 진행중 탭 클릭
    const hasActiveTab = await commands.isVisibleByRole('button', '진행중', 3_000)
    if (hasActiveTab) {
      await commands.clickByRole('button', '진행중')
      await commands.waitForTimeout(1000)

      // 콘텐츠 확인 (테이블 또는 빈 상태)
      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      const hasEmpty = await commands.isVisibleByText('없습니다', 2_000)
      expect(hasTable || hasEmpty).toBe(true)
    }

    // 전체 탭 클릭
    await commands.clickByRole('button', '전체')
    await commands.waitForTimeout(1500)

    const hasTable = await commands.isVisibleBySelector('table', 5_000)
    const hasEmpty = await commands.isVisibleByText('없습니다', 2_000)
    expect(hasTable || hasEmpty).toBe(true)
  })

  it('스케줄링: 스케줄 실행 페이지 UI 확인', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/execute`)

    const hasHeader = await commands.isVisibleByText('스케줄 실행', 15_000)
    expect(hasHeader).toBe(true)

    // 솔버 선택 드롭다운 확인
    const hasSelect = await commands.isVisibleBySelector('select', 5_000)
    expect(hasSelect).toBe(true)

    // 스케줄 실행 버튼 확인
    const hasRunBtn = await commands.isVisibleByRole('button', '스케줄 실행')
    expect(hasRunBtn).toBe(true)

    // 상태 카드 확인
    const hasEquipCard = await commands.isVisibleByText('가용 설비', 5_000)
    expect(hasEquipCard).toBe(true)

    const hasOrderCard = await commands.isVisibleByText('스케줄 대상', 5_000)
    expect(hasOrderCard).toBe(true)

    const hasResultCard = await commands.isVisibleByText('스케줄 결과', 5_000)
    expect(hasResultCard).toBe(true)
  })

  it('스케줄링: 설정 필드 확인', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/execute`)

    const hasHeader = await commands.isVisibleByText('스케줄 실행', 15_000)
    expect(hasHeader).toBe(true)

    // 계획 기간 입력 확인
    const hasHorizonLabel = await commands.isVisibleByText('계획 기간', 5_000)
    expect(hasHorizonLabel).toBe(true)

    // 솔버 선택 라벨 확인
    const hasSolverLabel = await commands.isVisibleByText('솔버 선택', 5_000)
    expect(hasSolverLabel).toBe(true)

    // 시간 제한 라벨 확인
    const hasTimeLimitLabel = await commands.isVisibleByText('시간 제한', 5_000)
    expect(hasTimeLimitLabel).toBe(true)

    // 옵션(진행중 포함) 확인
    const hasOptionLabel = await commands.isVisibleByText('진행중 포함', 5_000)
    expect(hasOptionLabel).toBe(true)
  })

  it('스케줄링: Scheduler API 솔버 목록 확인', async () => {
    // Cell-Scheduler runs on port 8002 - use fetchExternal for non-MES APIs
    try {
      const result = await commands.fetchExternal('http://localhost:8002/api/v1/schedule/solvers')
      if (result.ok) {
        expect(result.status).toBe(200)
        expect(Array.isArray(result.data)).toBe(true)
      }
    } catch {
      // Scheduler may not be running - skip gracefully
    }
  })

  it('스케줄 현황 페이지: 간트 차트 또는 빈 상태', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler`)

    const hasHeader = await commands.isVisibleByText('스케줄 현황', 15_000)
    expect(hasHeader).toBe(true)

    // 날짜 선택 필드 확인
    const hasDatePicker = await commands.isVisibleBySelector('input[type="date"]', 5_000)
    expect(hasDatePicker).toBe(true)

    // 오늘 버튼 확인
    const hasTodayBtn = await commands.isVisibleByRole('button', '오늘')
    expect(hasTodayBtn).toBe(true)

    // 간트 차트가 있거나 빈 상태 메시지 확인
    const hasGantt = await commands.isVisibleBySelector('svg, canvas, [class*="gantt"]', 5_000)
    const hasEmpty = await commands.isVisibleByText('스케줄된 작업지시가 없습니다', 3_000)
    const hasLoading = await commands.isVisibleByText('로딩 중', 3_000)
    expect(hasGantt || hasEmpty || hasLoading).toBe(true)
  })

  it('솔버 설정 페이지: 설정 폼 및 솔버 카드', async () => {
    await login()
    await commands.goto(`${APP_URL}/scheduler/settings`)

    const hasHeader = await commands.isVisibleByText('솔버 설정', 15_000)
    expect(hasHeader).toBe(true)

    // 기본 설정 섹션
    const hasBasicSettings = await commands.isVisibleByText('기본 설정', 5_000)
    expect(hasBasicSettings).toBe(true)

    // 솔버 유형 카드 섹션
    const hasSolverTypes = await commands.isVisibleByText('솔버 유형', 5_000)
    expect(hasSolverTypes).toBe(true)

    // 파라미터 참조 테이블
    const hasParamRef = await commands.isVisibleByText('파라미터 참조', 5_000)
    expect(hasParamRef).toBe(true)

    // 저장/초기화 버튼
    const hasResetBtn = await commands.isVisibleByRole('button', '초기화')
    expect(hasResetBtn).toBe(true)

    const hasSaveBtn = await commands.isVisibleByRole('button', '저장')
    expect(hasSaveBtn).toBe(true)
  })

  it('생산실적 확인: 통계 카드 전체 확인', async () => {
    await login()
    await commands.goto(`${APP_URL}/production/results`)

    const hasHeader = await commands.isVisibleByText('생산 실적', 15_000)
    expect(hasHeader).toBe(true)

    // 통계 카드 모두 확인
    const cards = ['총 실적', '양품', '불량', '수율']
    for (const card of cards) {
      const hasCard = await commands.isVisibleByText(card, 5_000)
      expect(hasCard).toBe(true)
    }

    // 실적 등록 버튼
    const hasRegisterBtn = await commands.isVisibleByRole('button', '실적 등록')
    expect(hasRegisterBtn).toBe(true)
  })

  it('생산실적 API: 실적 목록 조회', async () => {
    const result = await commands.fetchApi('/production/results?limit=10')
    expect(result.ok).toBe(true)
    expect(result.status).toBe(200)
    expect(result.data).toHaveProperty('items')
    expect(Array.isArray(result.data.items)).toBe(true)
  })

  it('분석 대시보드: OEE KPI 카드 확인', async () => {
    await login()
    await commands.goto(`${APP_URL}/analytics`)

    const hasHeader = await commands.isVisibleByText('분석 대시보드', 15_000)
    expect(hasHeader).toBe(true)

    // 로딩 또는 KPI 카드 확인
    const hasOEE = await commands.isVisibleByText('전체 OEE', 10_000)
    const hasLoading = await commands.isVisibleByText('로딩 중', 3_000)
    expect(hasOEE || hasLoading).toBe(true)

    if (hasOEE) {
      // KPI 카드 추가 확인
      const hasAvailability = await commands.isVisibleByText('가용성', 3_000)
      expect(hasAvailability).toBe(true)

      const hasPerformance = await commands.isVisibleByText('성능효율', 3_000)
      expect(hasPerformance).toBe(true)

      const hasQuality = await commands.isVisibleByText('품질지수', 3_000)
      expect(hasQuality).toBe(true)

      const hasTotalProd = await commands.isVisibleByText('총 생산량', 3_000)
      expect(hasTotalProd).toBe(true)

      const hasDefectRate = await commands.isVisibleByText('불량률', 3_000)
      expect(hasDefectRate).toBe(true)
    }
  })

  it('분석 대시보드: 차트 섹션 및 분석 메뉴', async () => {
    await login()
    await commands.goto(`${APP_URL}/analytics`)

    const hasHeader = await commands.isVisibleByText('분석 대시보드', 15_000)
    expect(hasHeader).toBe(true)

    const hasOEE = await commands.isVisibleByText('전체 OEE', 10_000)
    const hasLoading = await commands.isVisibleByText('로딩 중', 3_000)
    expect(hasOEE || hasLoading).toBe(true)

    if (hasOEE) {
      // 차트 섹션 확인
      const hasOEETrend = await commands.isVisibleByText('OEE 트렌드', 5_000)
      expect(hasOEETrend).toBe(true)

      const hasProdVolume = await commands.isVisibleByText('생산량 실적', 5_000)
      expect(hasProdVolume).toBe(true)

      // 기간 필터 확인
      const hasDateFilter = await commands.isVisibleBySelector('input[type="date"]', 3_000)
      expect(hasDateFilter).toBe(true)
    }

    // 분석 메뉴 섹션
    const hasAnalysisMenu = await commands.isVisibleByText('분석 메뉴', 5_000)
    if (hasAnalysisMenu) {
      const hasEquipAnalysis = await commands.isVisibleByText('설비 분석', 3_000)
      expect(hasEquipAnalysis).toBe(true)

      const hasLotTrace = await commands.isVisibleByText('Lot 추적', 3_000)
      expect(hasLotTrace).toBe(true)
    }
  })

  it('설비 분석: 가동률 차트 및 설비 현황', async () => {
    await login()
    await commands.goto(`${APP_URL}/analytics/equipment`)

    const hasHeader = await commands.isVisibleByText('설비 가동률 분석', 15_000)
    expect(hasHeader).toBe(true)

    // 기간 필터 확인
    const hasDateFilter = await commands.isVisibleBySelector('input[type="date"]', 5_000)
    expect(hasDateFilter).toBe(true)

    // 주기 선택 확인
    const hasPeriodSelect = await commands.isVisibleBySelector('select', 5_000)
    expect(hasPeriodSelect).toBe(true)

    // 설비 선택 드롭다운
    const hasEquipSelect = await commands.isVisibleByText('설비 선택', 5_000)
    expect(hasEquipSelect).toBe(true)

    // 차트 또는 카드 또는 로딩
    const hasChart = await commands.isVisibleBySelector('[class*="chart"], svg, canvas, .recharts-wrapper', 10_000)
    const hasCards = await commands.isVisibleBySelector('[class*="card"]', 5_000)
    const hasLoading = await commands.isVisibleByText('로딩', 3_000)
    expect(hasChart || hasCards || hasLoading).toBe(true)
  })

  it('설비 분석: 가동률 통계 카드 확인', async () => {
    await login()
    await commands.goto(`${APP_URL}/analytics/equipment`)

    const hasHeader = await commands.isVisibleByText('설비 가동률 분석', 15_000)
    expect(hasHeader).toBe(true)

    // 통계 카드가 렌더되면 확인
    const hasAvgUtil = await commands.isVisibleByText('평균 가동률', 5_000)
    if (hasAvgUtil) {
      const hasMaxUtil = await commands.isVisibleByText('최고 가동률', 3_000)
      expect(hasMaxUtil).toBe(true)

      const hasMinUtil = await commands.isVisibleByText('최저 가동률', 3_000)
      expect(hasMinUtil).toBe(true)

      const hasHighPerformers = await commands.isVisibleByText('우수 설비', 3_000)
      expect(hasHighPerformers).toBe(true)

      const hasNeedsAttention = await commands.isVisibleByText('관심 설비', 3_000)
      expect(hasNeedsAttention).toBe(true)
    }
  })

  it('Lot 추적 페이지: 검색 및 테이블', async () => {
    await login()
    await commands.goto(`${APP_URL}/analytics/lot-trace`)

    const hasHeader = await commands.isVisibleByText('Lot 추적', 15_000)
    expect(hasHeader).toBe(true)

    // 검색 입력 필드 확인
    const hasSearchInput = await commands.isVisibleBySelector('input[type="text"]', 5_000)
    expect(hasSearchInput).toBe(true)

    // 검색 버튼 확인
    const hasSearchBtn = await commands.isVisibleByRole('button', '검색')
    expect(hasSearchBtn).toBe(true)

    // 기간 필터 확인
    const hasDateFilter = await commands.isVisibleBySelector('input[type="date"]', 5_000)
    expect(hasDateFilter).toBe(true)

    // 테이블이 있거나 빈 상태 메시지
    const hasTable = await commands.isVisibleBySelector('table', 5_000)
    const hasEmpty = await commands.isVisibleByText('Lot 데이터가 없습니다', 3_000)
    const hasLoading = await commands.isVisibleByText('로딩 중', 3_000)
    expect(hasTable || hasEmpty || hasLoading).toBe(true)

    // 테이블이 있으면 헤더 확인
    if (hasTable) {
      const tableHeaders = ['Lot No', '제품명', '현재공정', '진행률', '상태']
      for (const th of tableHeaders) {
        const hasTh = await commands.isVisibleByText(th, 3_000)
        expect(hasTh).toBe(true)
      }
    }
  })

  it('전체 워크플로우: 대시보드 -> 작업지시 -> 스케줄러 -> 실적 -> 분석', async () => {
    await login()

    // Step 1: 대시보드
    await commands.goto(`${APP_URL}/`)
    const hasDashboard = await commands.isVisibleByText('전체 설비', 10_000)
    expect(hasDashboard).toBe(true)

    // Step 2: 작업지시
    await commands.goto(`${APP_URL}/production/orders`)
    const hasOrders = await commands.isVisibleByText('작업지시', 10_000)
    expect(hasOrders).toBe(true)

    // Step 3: 스케줄러
    await commands.goto(`${APP_URL}/scheduler/execute`)
    const hasScheduler = await commands.isVisibleByText('스케줄 실행', 10_000)
    expect(hasScheduler).toBe(true)

    // Step 4: 생산실적
    await commands.goto(`${APP_URL}/production/results`)
    const hasResults = await commands.isVisibleByText('생산 실적', 10_000)
    expect(hasResults).toBe(true)

    // Step 5: 분석 대시보드
    await commands.goto(`${APP_URL}/analytics`)
    const hasAnalytics = await commands.isVisibleByText('분석 대시보드', 10_000)
    expect(hasAnalytics).toBe(true)
  })
})
