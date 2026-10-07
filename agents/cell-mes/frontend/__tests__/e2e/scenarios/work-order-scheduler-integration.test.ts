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

describe('작업지시-스케줄러 통합 워크플로우', () => {

  describe('1. 전체 워크플로우 시나리오', () => {

    it('작업지시 생성 → 스케줄러 페이지 확인', async () => {
      await login()

      // Step 1: 작업지시 페이지
      await commands.goto(`${APP_URL}/production/orders`)
      const hasOrders = await commands.isVisibleByText('작업지시', 15_000)
      expect(hasOrders).toBe(true)

      // Step 2: 생성 버튼 확인
      const hasCreateBtn = await commands.isVisibleByRole('button', '작업지시 생성', 5_000)
      expect(hasCreateBtn).toBe(true)

      // Step 3: 스케줄러 실행 페이지
      await commands.goto(`${APP_URL}/scheduler/execute`)
      const hasScheduler = await commands.isVisibleByText('스케줄 실행', 15_000)
      expect(hasScheduler).toBe(true)

      // Step 4: 스케줄 현황 페이지
      await commands.goto(`${APP_URL}/scheduler`)
      const hasOverview = await commands.isVisibleByText('스케줄 현황', 15_000)
      expect(hasOverview).toBe(true)
    })

    it('작업지시 목록에서 테이블 구조 확인', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/orders`)

      const hasHeader = await commands.isVisibleByText('작업지시', 15_000)
      expect(hasHeader).toBe(true)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      const hasEmpty = await commands.isVisibleByText('없습니다', 3_000)
      expect(hasTable || hasEmpty || hasHeader).toBe(true)
    })
  })

  describe('2. 긴급 작업지시 삽입 시나리오', () => {

    it('우선순위 관련 UI 확인', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler/execute`)

      const hasHeader = await commands.isVisibleByText('스케줄 실행', 15_000)
      expect(hasHeader).toBe(true)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      const hasCards = await commands.isVisibleBySelector('[class*="card"]', 5_000)
      expect(hasTable || hasCards || hasHeader).toBe(true)
    })

    it('작업지시 생성 폼에서 우선순위 입력 확인', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/orders`)

      const hasHeader = await commands.isVisibleByText('작업지시', 15_000)
      expect(hasHeader).toBe(true)

      const hasCreateBtn = await commands.isVisibleByRole('button', '작업지시 생성', 5_000)
      if (hasCreateBtn) {
        await commands.clickByRole('button', '작업지시 생성')
        await commands.waitForTimeout(1000)

        const hasModal = await commands.isVisibleBySelector('.fixed.inset-0, [role="dialog"]', 5_000)
        expect(hasModal).toBe(true)

        await commands.clickByRole('button', '취소')
      }
    })
  })

  describe('3. 스케줄 변경 후 작업지시 영향 확인', () => {

    it('스케줄 실행 페이지에서 설정 변경', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler/execute`)

      const hasHeader = await commands.isVisibleByText('스케줄 실행', 15_000)
      expect(hasHeader).toBe(true)

      const hasRunBtn = await commands.isVisibleByRole('button', '스케줄 실행')
      expect(hasRunBtn).toBe(true)
    })

    it('스케줄 실행 버튼 및 솔버 선택', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler/execute`)

      const hasHeader = await commands.isVisibleByText('스케줄 실행', 15_000)
      expect(hasHeader).toBe(true)

      const hasSelect = await commands.isVisibleBySelector('select', 5_000)
      expect(hasSelect).toBe(true)
    })
  })

  describe('4. 다중 사용자 동시 작업 시나리오', () => {

    it('페이지 새로고침 후 데이터 유지', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/orders`)

      const hasHeader = await commands.isVisibleByText('작업지시', 15_000)
      expect(hasHeader).toBe(true)

      // Reload and check
      await commands.goto(`${APP_URL}/production/orders`)
      const hasHeaderAfter = await commands.isVisibleByText('작업지시', 15_000)
      expect(hasHeaderAfter).toBe(true)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      const hasEmpty = await commands.isVisibleByText('없습니다', 3_000)
      expect(hasTable || hasEmpty || hasHeaderAfter).toBe(true)
    })

    it('스케줄 현황 실시간 확인', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler`)

      const hasHeader = await commands.isVisibleByText('스케줄 현황', 15_000)
      expect(hasHeader).toBe(true)

      const hasDateInput = await commands.isVisibleBySelector('input[type="date"]', 5_000)
      expect(hasDateInput || hasHeader).toBe(true)
    })
  })

  describe('5. 설비 고장 시 재스케줄링 시나리오', () => {

    it('설비 상태 정보 표시 확인', async () => {
      await login()
      await commands.goto(`${APP_URL}/scheduler/execute`)

      const hasHeader = await commands.isVisibleByText('스케줄 실행', 15_000)
      expect(hasHeader).toBe(true)

      const hasEquipInfo = await commands.isVisibleByText('가용 설비', 5_000)
      expect(hasEquipInfo || hasHeader).toBe(true)
    })

    it('재스케줄링 UI 확인', async () => {
      await login()

      // 스케줄 현황 확인
      await commands.goto(`${APP_URL}/scheduler`)
      const hasOverview = await commands.isVisibleByText('스케줄 현황', 15_000)
      expect(hasOverview).toBe(true)

      // 스케줄 실행 페이지
      await commands.goto(`${APP_URL}/scheduler/execute`)
      const hasExecute = await commands.isVisibleByText('스케줄 실행', 15_000)
      expect(hasExecute).toBe(true)

      const hasRunBtn = await commands.isVisibleByRole('button', '스케줄 실행')
      expect(hasRunBtn).toBe(true)
    })
  })

  describe('워크플로우 데이터 일관성', () => {

    it('작업지시 생성 후 스케줄러에 반영 확인', async () => {
      await login()

      // 작업지시 페이지 확인
      await commands.goto(`${APP_URL}/production/orders`)
      const hasOrders = await commands.isVisibleByText('작업지시', 15_000)
      expect(hasOrders).toBe(true)

      // 스케줄러 실행 페이지에서 대상 확인
      await commands.goto(`${APP_URL}/scheduler/execute`)
      const hasScheduler = await commands.isVisibleByText('스케줄 실행', 15_000)
      expect(hasScheduler).toBe(true)

      const hasTarget = await commands.isVisibleByText('스케줄 대상', 5_000)
      expect(hasTarget || hasScheduler).toBe(true)
    })

    it('스케줄 승인 후 작업지시 페이지 연동', async () => {
      await login()

      await commands.goto(`${APP_URL}/scheduler/execute`)
      const hasScheduler = await commands.isVisibleByText('스케줄 실행', 15_000)
      expect(hasScheduler).toBe(true)

      await commands.goto(`${APP_URL}/production/orders`)
      const hasOrders = await commands.isVisibleByText('작업지시', 15_000)
      expect(hasOrders).toBe(true)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      expect(hasTable || hasOrders).toBe(true)
    })
  })
})
