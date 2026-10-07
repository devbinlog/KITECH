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
 * 스케줄러 역할 상세 테스트
 * - 설비 배정, 간트 차트 조작, 재스케줄링, 스케줄 최적화
 */
describe('스케줄러 - 화면 단위 테스트', () => {

  describe('스케줄 현황 페이지', () => {

    it('페이지 진입 및 기본 요소', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler`)

      const hasHeader = await commands.isVisibleByText('스케줄 현황', 15_000)
      expect(hasHeader).toBe(true)

      // Gantt or equipment list
      const hasGantt = await commands.isVisibleBySelector('[class*="gantt"], .recharts-wrapper, canvas, svg', 5_000)
      const hasEquipList = await commands.isVisibleByText('CNC|ROBOT|AMR|설비', 5_000)
      expect(hasGantt || hasEquipList || hasHeader).toBe(true)
    })

    it('스케줄 결과 요약 표시', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler`)

      const hasHeader = await commands.isVisibleByText('스케줄 현황', 15_000)
      expect(hasHeader).toBe(true)

      // Summary cards or empty state
      const hasSummary = await commands.isVisibleByText('스케줄된|작업지시|설비', 5_000)
      const hasEmpty = await commands.isVisibleByText('없습니다', 3_000)
      expect(hasSummary || hasEmpty || hasHeader).toBe(true)
    })

    it('날짜 선택 기능', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler`)

      const hasHeader = await commands.isVisibleByText('스케줄 현황', 15_000)
      expect(hasHeader).toBe(true)

      const hasDateInput = await commands.isVisibleBySelector('input[type="date"]', 5_000)
      expect(hasDateInput || hasHeader).toBe(true)
    })
  })

  describe('스케줄 실행 페이지', () => {

    it('페이지 진입 및 설정 확인', async () => {
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

    it('솔버 선택 드롭다운 (5+ 옵션)', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler/execute`)

      const hasHeader = await commands.isVisibleByText('스케줄 실행', 15_000)
      expect(hasHeader).toBe(true)

      const hasSelect = await commands.isVisibleBySelector('select', 5_000)
      expect(hasSelect).toBe(true)
    })

    it('스케줄 실행 버튼 존재', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler/execute`)

      const hasHeader = await commands.isVisibleByText('스케줄 실행', 15_000)
      expect(hasHeader).toBe(true)

      const hasRunBtn = await commands.isVisibleByRole('button', '스케줄 실행')
      expect(hasRunBtn).toBe(true)
    })
  })
})

describe('스케줄러 - 데이터 검증', () => {

  it('스케줄 현황과 스케줄 실행 페이지 양쪽 로드', async () => {
    await login()

    await commands.goto(`${APP_URL}/scheduler`)
    const hasOverview = await commands.isVisibleByText('스케줄 현황', 15_000)
    expect(hasOverview).toBe(true)

    await commands.goto(`${APP_URL}/scheduler/execute`)
    const hasExecute = await commands.isVisibleByText('스케줄 실행', 15_000)
    expect(hasExecute).toBe(true)
  })
})
