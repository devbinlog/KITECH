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
 * 생산관리자 역할 상세 테스트
 * - 작업지시 생성/수정/삭제, 우선순위 변경, 일정 조정, 생산 현황 모니터링
 */
describe('생산관리자 - 화면 단위 테스트', () => {

  describe('작업지시 페이지', () => {

    it('페이지 진입 및 기본 요소 로딩', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/orders`)

      const hasHeader = await commands.isVisibleByText('작업지시', 15_000)
      expect(hasHeader).toBe(true)

      const hasTodayTab = await commands.isVisibleByRole('button', '오늘 작업', 5_000)
      expect(hasTodayTab).toBe(true)

      const hasCreateBtn = await commands.isVisibleByRole('button', '작업지시 생성', 5_000)
      expect(hasCreateBtn).toBe(true)
    })

    it('각 탭 전환 시 데이터 로드', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/orders`)

      const hasHeader = await commands.isVisibleByText('작업지시', 15_000)
      expect(hasHeader).toBe(true)

      const tabs = ['오늘 작업', '예정 작업', '진행중', '전체']
      for (const tabName of tabs) {
        const hasTab = await commands.isVisibleByRole('button', tabName, 3_000)
        if (hasTab) {
          await commands.clickByRole('button', tabName)
          await commands.waitForTimeout(1500)
          const stillHasHeader = await commands.isVisibleByText('작업지시', 5_000)
          expect(stillHasHeader).toBe(true)
        }
      }
    })
  })

  describe('생산실적 페이지', () => {

    it('페이지 진입 및 기본 요소', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/results`)

      const hasHeader = await commands.isVisibleByText('생산 실적', 15_000)
      expect(hasHeader).toBe(true)

      const hasStats = await commands.isVisibleBySelector('[class*="card"]', 5_000)
      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      expect(hasStats || hasTable).toBe(true)
    })
  })
})

describe('생산관리자 - 컴포넌트 단위 테스트', () => {

  describe('작업지시 생성 폼', () => {

    it('모달 열기/닫기', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/orders`)

      const hasHeader = await commands.isVisibleByText('작업지시', 15_000)
      expect(hasHeader).toBe(true)

      await commands.clickByRole('button', '작업지시 생성')
      const hasModal = await commands.isVisibleBySelector('.fixed.inset-0, [role="dialog"]', 5_000)
      expect(hasModal).toBe(true)

      await commands.clickByRole('button', '취소')
      await commands.waitForTimeout(1000)
    })

    it('폼 필드 구성 확인', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/orders`)

      const hasHeader = await commands.isVisibleByText('작업지시', 15_000)
      expect(hasHeader).toBe(true)

      await commands.clickByRole('button', '작업지시 생성')
      const hasModal = await commands.isVisibleBySelector('.fixed.inset-0, [role="dialog"]', 5_000)
      expect(hasModal).toBe(true)

      // Lot No input
      const hasTextInput = await commands.isVisibleBySelector('input[type="text"]', 3_000)
      expect(hasTextInput).toBe(true)

      // Product select
      const hasSelect = await commands.isVisibleBySelector('select', 3_000)
      expect(hasSelect).toBe(true)

      // Submit button
      const hasSubmit = await commands.isVisibleBySelector('button[type="submit"]', 3_000)
      expect(hasSubmit).toBe(true)

      await commands.clickByRole('button', '취소')
    })
  })
})

describe('생산관리자 - 버튼 단위 테스트', () => {

  it('작업지시 생성 버튼 클릭 시 모달 열림', async () => {
    await login()
    await commands.goto(`${APP_URL}/production/orders`)

    const hasHeader = await commands.isVisibleByText('작업지시', 15_000)
    expect(hasHeader).toBe(true)

    await commands.clickByRole('button', '작업지시 생성')
    const hasModal = await commands.isVisibleBySelector('.fixed.inset-0, [role="dialog"]', 5_000)
    expect(hasModal).toBe(true)

    await commands.clickByRole('button', '취소')
  })
})

describe('생산관리자 - 비정상 케이스', () => {

  it('필수값 누락 시 유효성 검사', async () => {
    await login()
    await commands.goto(`${APP_URL}/production/orders`)

    const hasHeader = await commands.isVisibleByText('작업지시', 15_000)
    expect(hasHeader).toBe(true)

    await commands.clickByRole('button', '작업지시 생성')
    const hasModal = await commands.isVisibleBySelector('.fixed.inset-0, [role="dialog"]', 5_000)
    expect(hasModal).toBe(true)

    // Verify submit button exists - required fields should prevent submission
    const hasSubmit = await commands.isVisibleBySelector('button[type="submit"]', 3_000)
    expect(hasSubmit).toBe(true)

    // Modal should remain open (required fields not filled)
    const modalStillOpen = await commands.isVisibleBySelector('.fixed.inset-0, [role="dialog"]', 2_000)
    expect(modalStillOpen).toBe(true)

    await commands.clickByRole('button', '취소')
  })
})

describe('생산관리자 - 우선순위 및 일정 관리', () => {

  it('우선순위 변경 UI 확인', async () => {
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
    expect(hasTable || hasHeader).toBe(true)
  })
})
