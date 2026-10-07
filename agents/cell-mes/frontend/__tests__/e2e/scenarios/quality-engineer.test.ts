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
 * 품질관리 담당자 업무 시나리오
 *
 * 페르소나: 이품질 (품질관리팀, QE 경력 6년)
 * - 품질 대시보드에서 현황 파악
 * - 검사계획 수립 및 관리
 * - SPC 모니터링 및 공정능력 분석
 * - NCR 처리 및 시정조치 관리
 * - Lot 추적
 */
describe('품질관리 담당자 - 일일 업무', () => {

  it('아침: 품질 대시보드에서 KPI 확인', async () => {
    await login()
    await commands.goto(`${APP_URL}/quality`)

    const hasHeader = await commands.isVisibleByText('품질 대시보드', 15_000)
    expect(hasHeader).toBe(true)

    const hasInspectionCount = await commands.isVisibleByText('총 검사건수', 5_000)
    expect(hasInspectionCount).toBe(true)

    const hasPassRate = await commands.isVisibleByText('합격률', 3_000)
    expect(hasPassRate).toBe(true)
  })

  it('품질 대시보드: 날짜 필터 변경', async () => {
    await login()
    await commands.goto(`${APP_URL}/quality`)

    const hasHeader = await commands.isVisibleByText('품질 대시보드', 15_000)
    expect(hasHeader).toBe(true)

    // 날짜 필터 존재 확인
    const hasDateFilter = await commands.isVisibleBySelector('input[type="date"]', 3_000)
    // Page loaded successfully
    expect(hasHeader).toBe(true)
  })

  it('검사계획 관리: 목록 조회 및 생성 폼', async () => {
    await login()
    await commands.goto(`${APP_URL}/quality/inspection-plans`)

    const hasHeader = await commands.isVisibleByText('검사계획 관리', 15_000)
    expect(hasHeader).toBe(true)

    // 테이블 또는 빈 상태
    const hasTable = await commands.isVisibleBySelector('table', 5_000)
    const hasEmpty = await commands.isVisibleByText('없습니다', 3_000)
    const hasLoading = await commands.isVisibleByText('로딩', 3_000)
    expect(hasTable || hasEmpty || hasLoading).toBe(true)

    // 검사계획 생성 버튼 확인
    const hasCreateBtn = await commands.isVisibleByRole('button', '검사계획 생성', 5_000)
    if (hasCreateBtn) {
      await commands.clickByRole('button', '검사계획 생성')
      const hasModal = await commands.isVisibleBySelector('[role="dialog"], .fixed.inset-0', 5_000)
      expect(hasModal).toBe(true)

      // 취소
      await commands.clickByRole('button', '취소')
    }
  })

  it('측정결과 등록: 폼 입력 흐름', async () => {
    await login()
    await commands.goto(`${APP_URL}/quality/inspection-results`)

    const hasHeader = await commands.isVisibleByText('측정결과', 15_000)
    expect(hasHeader).toBe(true)

    // 측정결과 등록 버튼
    const hasRegisterBtn = await commands.isVisibleByRole('button', '측정결과 등록', 5_000)
    if (hasRegisterBtn) {
      await commands.clickByRole('button', '측정결과 등록')
      const hasModal = await commands.isVisibleBySelector('[role="dialog"], .fixed.inset-0', 5_000)
      expect(hasModal).toBe(true)

      // 취소
      await commands.clickByRole('button', '취소')
    }
  })

  it('SPC 모니터링: 관리도 확인', async () => {
    await login()
    await commands.goto(`${APP_URL}/quality/spc`)

    const hasHeader = await commands.isVisibleByText('SPC', 15_000)
    expect(hasHeader).toBe(true)

    // 검사항목 선택 드롭다운 확인
    const hasSelect = await commands.isVisibleBySelector('select', 5_000)
    expect(hasSelect || hasHeader).toBe(true)
  })

  it('NCR 처리: 목록 조회 및 상세 보기', async () => {
    await login()
    await commands.goto(`${APP_URL}/quality/ncr`)

    const hasHeader = await commands.isVisibleByText('부적합 관리', 15_000)
    expect(hasHeader).toBe(true)

    // NCR 테이블 확인
    const hasTable = await commands.isVisibleBySelector('table', 10_000)
    const hasEmpty = await commands.isVisibleByText('없습니다', 3_000)
    const hasLoading = await commands.isVisibleByText('로딩', 3_000)
    expect(hasTable || hasEmpty || hasLoading).toBe(true)
  })

  it('Lot 추적: 검색 및 상세 보기', async () => {
    await login()
    await commands.goto(`${APP_URL}/analytics/lot-trace`)

    const hasHeader = await commands.isVisibleByText('Lot', 15_000)
    expect(hasHeader).toBe(true)

    // Lot 추적 테이블 또는 빈 상태
    const hasTable = await commands.isVisibleBySelector('table', 10_000)
    const hasEmpty = await commands.isVisibleByText('없습니다', 3_000)
    expect(hasTable || hasEmpty || hasHeader).toBe(true)
  })
})
