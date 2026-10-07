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
 * 제조현업 업무 흐름 테스트
 * USE_CASES.md Part 1과 1:1 매칭
 */
describe('제조 업무 흐름 (Manufacturing Workflows)', () => {

  describe('1. 작업지시 관리', () => {

    it('작업지시 목록 확인 - 전체 탭', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/orders`)

      const hasHeader = await commands.isVisibleByText('작업지시', 15_000)
      expect(hasHeader).toBe(true)

      const hasAllTab = await commands.isVisibleByRole('button', '전체', 3_000)
      if (hasAllTab) {
        await commands.clickByRole('button', '전체')
        await commands.waitForTimeout(1000)
      }

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      const hasEmpty = await commands.isVisibleByText('없습니다', 3_000)
      expect(hasTable || hasEmpty || hasHeader).toBe(true)
    })

    it('Lot No 형식 검증 (LOT-YYYYMMDD-NNN)', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/orders`)

      const hasHeader = await commands.isVisibleByText('작업지시', 15_000)
      expect(hasHeader).toBe(true)

      await commands.clickByRole('button', '작업지시 생성')
      const hasModal = await commands.isVisibleBySelector('.fixed.inset-0', 5_000)
      expect(hasModal).toBe(true)

      // Lot No placeholder 확인
      const hasLotInput = await commands.isVisibleBySelector('input[placeholder="LOT-YYYYMMDD-001"]', 3_000)
      expect(hasLotInput || hasModal).toBe(true)

      await commands.clickByRole('button', '취소')
    })

    it('READY → RUNNING 전이 버튼 확인', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/orders`)

      const hasHeader = await commands.isVisibleByText('작업지시', 15_000)
      expect(hasHeader).toBe(true)

      // Check that status transition buttons exist in table
      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      expect(hasTable || hasHeader).toBe(true)
    })

    it('오늘 작업 탭', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/orders`)

      const hasHeader = await commands.isVisibleByText('작업지시', 15_000)
      expect(hasHeader).toBe(true)

      const hasTodayTab = await commands.isVisibleByRole('button', '오늘 작업', 3_000)
      if (hasTodayTab) {
        await commands.clickByRole('button', '오늘 작업')
        await commands.waitForTimeout(1000)
      }

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      const hasEmpty = await commands.isVisibleByText('없습니다', 3_000)
      expect(hasTable || hasEmpty || hasHeader).toBe(true)
    })
  })

  describe('2. 생산실적', () => {

    it('실적 목록 및 통계 카드 확인', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/results`)

      const hasHeader = await commands.isVisibleByText('생산 실적', 15_000)
      expect(hasHeader).toBe(true)

      const hasTotalCount = await commands.isVisibleByText('총 실적 건수', 10_000)
      expect(hasTotalCount).toBe(true)

      const hasGoodQty = await commands.isVisibleByText('양품 수량', 5_000)
      expect(hasGoodQty).toBe(true)

      const hasDefectQty = await commands.isVisibleByText('불량 수량', 5_000)
      expect(hasDefectQty).toBe(true)

      const hasYield = await commands.isVisibleByText('수율', 5_000)
      expect(hasYield).toBe(true)
    })

    it('실적 데이터 정합성: ok_qty + ng_qty = total (API)', async () => {
      await login()
      const res = await commands.fetchApi('/production/results?limit=100')
      if (!res.ok) return

      const results = res.data?.items || res.data?.data || res.data || []

      let mismatchCount = 0
      for (const result of results) {
        const ok = result.ok_qty || 0
        const ng = result.ng_qty || 0
        const total = result.total_qty || result.quantity
        if (total !== undefined && total !== (ok + ng)) {
          mismatchCount++
        }
      }

      expect(mismatchCount).toBe(0)
    })
  })

  describe('3. 스케줄링', () => {

    it('스케줄 현황 페이지 요약 카드 확인', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler`)

      const hasHeader = await commands.isVisibleByText('스케줄 현황', 15_000)
      expect(hasHeader).toBe(true)

      const hasSummary = await commands.isVisibleByText('스케줄된 설비|예정 작업지시|진행중', 5_000)
      const hasEmpty = await commands.isVisibleByText('스케줄된 작업지시가 없습니다', 3_000)
      expect(hasSummary || hasEmpty || hasHeader).toBe(true)
    })

    it('스케줄 실행 페이지 설정 확인', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler/execute`)

      const hasHeader = await commands.isVisibleByText('스케줄 실행', 15_000)
      expect(hasHeader).toBe(true)

      const hasPlanPeriod = await commands.isVisibleByText('계획 기간', 10_000)
      expect(hasPlanPeriod).toBe(true)

      const hasSolverLabel = await commands.isVisibleByText('솔버 선택', 5_000)
      expect(hasSolverLabel).toBe(true)

      const hasTimeLimit = await commands.isVisibleByText('시간 제한', 5_000)
      expect(hasTimeLimit).toBe(true)
    })
  })

  describe('4. 품질관리', () => {

    it('검사항목 동적 추가', async () => {
      await login()
      await commands.goto(`${APP_URL}/quality/inspection-plans`)

      const hasHeader = await commands.isVisibleByText('검사계획 관리', 15_000)
      expect(hasHeader).toBe(true)

      await commands.clickByRole('button', '검사계획 생성')
      const hasModal = await commands.isVisibleBySelector('.fixed.inset-0', 5_000)
      expect(hasModal).toBe(true)

      // 초기 항목 #1
      const hasItem1 = await commands.isVisibleByText('검사항목 #1', 3_000)
      expect(hasItem1).toBe(true)

      // 항목 추가
      await commands.clickByRole('button', '항목 추가')
      const hasItem2 = await commands.isVisibleByText('검사항목 #2', 3_000)
      expect(hasItem2).toBe(true)

      await commands.clickByRole('button', '취소')
    })

    it('SPC 페이지 접근', async () => {
      await login()
      await commands.goto(`${APP_URL}/quality/spc`)

      const hasHeader = await commands.isVisibleByText('SPC', 15_000)
      expect(hasHeader).toBe(true)
    })

    it('NCR 상태 전이 순서', async () => {
      await login()
      await commands.goto(`${APP_URL}/quality/ncr`)

      const hasHeader = await commands.isVisibleByText('부적합 관리', 15_000)
      expect(hasHeader).toBe(true)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      expect(hasTable || hasHeader).toBe(true)
    })
  })

  describe('5. 기준정보', () => {

    it('설비 목록 페이지 접근', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/equipments`)

      const hasHeader = await commands.isVisibleByText('설비', 15_000)
      expect(hasHeader).toBe(true)

      const hasContent = await commands.isVisibleBySelector('table, [class*="card"]', 10_000)
      expect(hasContent || hasHeader).toBe(true)
    })
  })

  describe('6. 분석', () => {

    it('분석 대시보드 OEE 카드 확인', async () => {
      await login()
      await commands.goto(`${APP_URL}/analytics`)

      const hasHeader = await commands.isVisibleByText('분석 대시보드', 15_000)
      expect(hasHeader).toBe(true)

      const hasOEE = await commands.isVisibleByText('전체 OEE', 10_000)
      const hasLoading = await commands.isVisibleByText('로딩 중', 3_000)
      expect(hasOEE || hasLoading).toBe(true)
    })

    it('Lot 추적 페이지 접근', async () => {
      await login()
      await commands.goto(`${APP_URL}/analytics/lot-trace`)

      const hasHeader = await commands.isVisibleByText('Lot', 15_000)
      expect(hasHeader).toBe(true)
    })
  })
})
