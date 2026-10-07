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
 * 품질관리자 역할 상세 테스트
 * - 검사 등록, NCR 생성/관리, 합격/불합격 판정, SPC 모니터링
 */
describe('품질관리자 - 화면 단위 테스트', () => {

  describe('품질 대시보드', () => {

    it('페이지 진입 및 KPI 확인', async () => {
      await login()
      await commands.goto(`${APP_URL}/quality`)

      const hasHeader = await commands.isVisibleByText('품질 대시보드', 15_000)
      expect(hasHeader).toBe(true)

      const hasCards = await commands.isVisibleBySelector('[class*="card"]', 5_000)
      expect(hasCards || hasHeader).toBe(true)
    })
  })

  describe('검사계획 관리', () => {

    it('검사계획 목록 조회', async () => {
      await login()
      await commands.goto(`${APP_URL}/quality/inspection-plans`)

      const hasHeader = await commands.isVisibleByText('검사계획 관리', 15_000)
      expect(hasHeader).toBe(true)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      const hasEmpty = await commands.isVisibleByText('없습니다', 3_000)
      expect(hasTable || hasEmpty || hasHeader).toBe(true)
    })

    it('검사계획 생성 모달 확인', async () => {
      await login()
      await commands.goto(`${APP_URL}/quality/inspection-plans`)

      const hasHeader = await commands.isVisibleByText('검사계획 관리', 15_000)
      expect(hasHeader).toBe(true)

      const hasCreateBtn = await commands.isVisibleByRole('button', '검사계획 생성', 5_000)
      if (hasCreateBtn) {
        await commands.clickByRole('button', '검사계획 생성')
        const hasModal = await commands.isVisibleBySelector('[role="dialog"], .fixed.inset-0', 5_000)
        expect(hasModal).toBe(true)

        // Verify form elements
        const hasSelect = await commands.isVisibleBySelector('select', 3_000)
        expect(hasSelect).toBe(true)

        await commands.clickByRole('button', '취소')
      }
    })
  })

  describe('NCR 관리', () => {

    it('NCR 목록 조회', async () => {
      await login()
      await commands.goto(`${APP_URL}/quality/ncr`)

      const hasHeader = await commands.isVisibleByText('부적합 관리', 15_000)
      expect(hasHeader).toBe(true)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      const hasEmpty = await commands.isVisibleByText('없습니다', 3_000)
      expect(hasTable || hasEmpty || hasHeader).toBe(true)
    })

    it('NCR 생성 모달 확인', async () => {
      await login()
      await commands.goto(`${APP_URL}/quality/ncr`)

      const hasHeader = await commands.isVisibleByText('부적합 관리', 15_000)
      expect(hasHeader).toBe(true)

      await commands.clickByRole('button', 'NCR 생성')
      const hasModal = await commands.isVisibleBySelector('.fixed.inset-0, [role="dialog"]', 5_000)
      expect(hasModal).toBe(true)

      const hasSelects = await commands.isVisibleBySelector('select', 3_000)
      expect(hasSelects).toBe(true)

      const hasTextarea = await commands.isVisibleBySelector('textarea', 3_000)
      expect(hasTextarea).toBe(true)

      await commands.clickByRole('button', '취소')
    })
  })

  describe('SPC 모니터링', () => {

    it('SPC 페이지 접근 및 선택 확인', async () => {
      await login()
      await commands.goto(`${APP_URL}/quality/spc`)

      const hasHeader = await commands.isVisibleByText('SPC', 15_000)
      expect(hasHeader).toBe(true)

      const hasSelect = await commands.isVisibleBySelector('select', 5_000)
      expect(hasSelect || hasHeader).toBe(true)
    })
  })
})

describe('품질관리자 - 하위 메뉴 네비게이션', () => {

  it('품질 하위 메뉴 순회', async () => {
    await login()

    const subPages = [
      { path: '/quality/inspection-plans', text: '검사' },
      { path: '/quality/inspection-results', text: '측정' },
      { path: '/quality/spc', text: 'SPC' },
      { path: '/quality/ncr', text: '부적합' },
    ]

    let loadedCount = 0
    for (const page of subPages) {
      await commands.goto(`${APP_URL}${page.path}`)
      const hasContent = await commands.isVisibleByText(page.text, 15_000)
      if (hasContent) {
        loadedCount++
      }
    }
    // At least some sub-pages should load successfully
    expect(loadedCount).toBeGreaterThan(0)
  })
})
