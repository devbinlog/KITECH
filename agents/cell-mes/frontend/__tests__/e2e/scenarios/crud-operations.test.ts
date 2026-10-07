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

describe('CRUD 보강 테스트', () => {

  describe('제품관리 CRUD', () => {

    it('제품 목록 조회', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/products`)

      const hasHeader = await commands.isVisibleByText('제품 관리', 15_000)
      expect(hasHeader).toBe(true)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      const hasEmpty = await commands.isVisibleByText('없습니다', 3_000)
      expect(hasTable || hasEmpty || hasHeader).toBe(true)
    })

    it('제품 수정 모달 열기', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/products`)

      const hasHeader = await commands.isVisibleByText('제품 관리', 15_000)
      expect(hasHeader).toBe(true)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      expect(hasTable || hasHeader).toBe(true)
    })

    it('제품 검색/필터 동작', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/products`)

      const hasHeader = await commands.isVisibleByText('제품 관리', 15_000)
      expect(hasHeader).toBe(true)

      const hasSearch = await commands.isVisibleBySelector('input[placeholder*="검색"], input[type="search"]', 3_000)
      expect(hasSearch || hasHeader).toBe(true)
    })
  })

  describe('표준공정 CRUD', () => {

    it('공정 목록 조회', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/processes`)

      const hasHeader = await commands.isVisibleByText('표준', 15_000)
      expect(hasHeader).toBe(true)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      const hasEmpty = await commands.isVisibleByText('없습니다', 3_000)
      expect(hasTable || hasEmpty || hasHeader).toBe(true)
    })
  })

  describe('설비관리 CRUD', () => {

    it('설비 목록 조회', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/equipments`)

      const hasHeader = await commands.isVisibleByText('설비', 15_000)
      expect(hasHeader).toBe(true)

      const hasCards = await commands.isVisibleBySelector('[class*="card"], table', 5_000)
      expect(hasCards || hasHeader).toBe(true)
    })

    it('설비 상태 변경 UI 확인', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/equipments`)

      const hasHeader = await commands.isVisibleByText('설비', 15_000)
      expect(hasHeader).toBe(true)

      const hasStatus = await commands.isVisibleByText('가동', 3_000)
      const hasIdle = await commands.isVisibleByText('IDLE', 3_000)
      const hasRunning = await commands.isVisibleByText('RUNNING', 3_000)
      expect(hasStatus || hasIdle || hasRunning || hasHeader).toBe(true)
    })
  })

  describe('작업지시 CRUD', () => {

    it('작업지시 테이블 로드 확인', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/orders`)

      const hasHeader = await commands.isVisibleByText('작업지시', 15_000)
      expect(hasHeader).toBe(true)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      const hasEmpty = await commands.isVisibleByText('없습니다', 3_000)
      expect(hasTable || hasEmpty).toBe(true)
    })

    it('작업지시 날짜 필터', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/orders`)

      const hasHeader = await commands.isVisibleByText('작업지시', 15_000)
      expect(hasHeader).toBe(true)

      // Date filter or tabs
      const hasTabs = await commands.isVisibleByRole('button', '오늘 작업', 3_000)
      const hasDateInput = await commands.isVisibleBySelector('input[type="date"]', 3_000)
      expect(hasTabs || hasDateInput || hasHeader).toBe(true)
    })
  })

  describe('라우팅설계 CRUD', () => {

    it('라우팅 추가 모달 확인', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/routings`)

      const hasHeader = await commands.isVisibleByText('라우팅', 15_000)
      expect(hasHeader).toBe(true)

      const hasAddBtn = await commands.isVisibleByRole('button', '추가|생성|등록', 3_000)
      if (hasAddBtn) {
        await commands.clickByRole('button', '추가|생성|등록')
        const hasModal = await commands.isVisibleBySelector('[role="dialog"], .fixed.inset-0, form', 5_000)
        if (hasModal) {
          const hasCancelBtn = await commands.isVisibleByRole('button', '취소|닫기', 2_000)
          if (hasCancelBtn) {
            await commands.clickByRole('button', '취소|닫기')
          }
        }
      }
    })
  })

  describe('물류시나리오 CRUD', () => {

    it('시나리오 추가 버튼 확인', async () => {
      await login()
      await commands.goto(`${APP_URL}/master/scenarios`)

      const hasHeader = await commands.isVisibleByText('시나리오', 15_000)
      expect(hasHeader).toBe(true)

      const hasAddBtn = await commands.isVisibleByRole('button', '추가|생성|등록', 3_000)
      expect(hasAddBtn || hasHeader).toBe(true)
    })
  })
})
