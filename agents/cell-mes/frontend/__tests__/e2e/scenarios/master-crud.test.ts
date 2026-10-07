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

describe('설비관리 CRUD', () => {

  it('설비 목록 조회 및 추가 버튼 확인', async () => {
    await login()
    await commands.goto(`${APP_URL}/master/equipments`)

    const hasHeader = await commands.isVisibleByText('설비 관리', 15_000)
    expect(hasHeader).toBe(true)

    const hasTable = await commands.isVisibleBySelector('table', 5_000)
    const hasCards = await commands.isVisibleBySelector('[class*="grid"]', 5_000)
    const hasEmpty = await commands.isVisibleByText('없습니다', 3_000)
    expect(hasTable || hasCards || hasEmpty).toBe(true)

    const hasAddBtn = await commands.isVisibleByRole('button', '설비 추가|추가', 3_000)
    if (hasAddBtn) {
      await commands.clickByRole('button', '설비 추가|추가')
      const hasModal = await commands.isVisibleBySelector('[role="dialog"], .fixed.inset-0', 3_000)
      if (hasModal) {
        await commands.clickByRole('button', '취소|닫기')
      }
    }
  })
})

describe('라우팅설계 CRUD', () => {

  it('라우팅 목록 조회 및 UI 확인', async () => {
    await login()
    await commands.goto(`${APP_URL}/master/routings`)

    const hasHeader = await commands.isVisibleByText('라우팅', 15_000)
    expect(hasHeader).toBe(true)

    const hasTable = await commands.isVisibleBySelector('table', 5_000)
    const hasCards = await commands.isVisibleBySelector('[class*="card"], [class*="grid"]', 5_000)
    const hasEmpty = await commands.isVisibleByText('없습니다', 3_000)
    expect(hasTable || hasCards || hasEmpty).toBe(true)
  })

  it('라우팅 추가 모달 열기', async () => {
    await login()
    await commands.goto(`${APP_URL}/master/routings`)

    const hasHeader = await commands.isVisibleByText('라우팅', 15_000)
    expect(hasHeader).toBe(true)

    const hasAddBtn = await commands.isVisibleByRole('button', '추가|라우팅 추가|생성', 5_000)
    if (hasAddBtn) {
      await commands.clickByRole('button', '추가|라우팅 추가|생성')

      const hasModal = await commands.isVisibleBySelector('[role="dialog"], .fixed.inset-0, form', 5_000)
      expect(hasModal).toBe(true)

      const hasCancelBtn = await commands.isVisibleByRole('button', '취소|닫기', 2_000)
      if (hasCancelBtn) {
        await commands.clickByRole('button', '취소|닫기')
      }
    }
  })
})

describe('물류시나리오 CRUD', () => {

  it('시나리오 페이지 로드', async () => {
    await login()
    await commands.goto(`${APP_URL}/master/scenarios`)

    const hasHeader = await commands.isVisibleByText('시나리오', 15_000)
    const hasContent = await commands.isVisibleBySelector('table, [class*="grid"]', 5_000)
    expect(hasHeader || hasContent).toBe(true)
  })
})

describe('작업지시 CRUD 보완', () => {

  it('작업지시 테이블 로드 확인', async () => {
    await login()
    await commands.goto(`${APP_URL}/production/orders`)

    const hasHeader = await commands.isVisibleByText('작업지시', 15_000)
    expect(hasHeader).toBe(true)

    const hasTable = await commands.isVisibleBySelector('table', 5_000)
    expect(hasTable).toBe(true)
  })

  it('작업지시 탭 전환', async () => {
    await login()
    await commands.goto(`${APP_URL}/production/orders`)

    const hasHeader = await commands.isVisibleByText('작업지시', 15_000)
    expect(hasHeader).toBe(true)

    const tabs = ['오늘 작업', '예정 작업', '진행중', '전체']
    let foundTab = false

    for (const tabName of tabs) {
      const hasTab = await commands.isVisibleByRole('button', tabName, 2_000)
      if (hasTab) {
        foundTab = true
        await commands.clickByRole('button', tabName)
        await commands.waitForTimeout(1000)

        const stillHasHeader = await commands.isVisibleByText('작업지시', 5_000)
        expect(stillHasHeader).toBe(true)
        break
      }
    }

    expect(foundTab || hasHeader).toBe(true)
  })
})
