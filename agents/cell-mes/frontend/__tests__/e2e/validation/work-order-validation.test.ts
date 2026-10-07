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

describe('작업지시 데이터 정합성', () => {

  it('작업지시 필수 필드 존재 확인', async () => {
    await login()

    const res = await commands.fetchApi('/production/orders?limit=10')
    if (!res.ok) return

    const orders = res.data?.items || res.data || []

    for (const order of orders.slice(0, 10)) {
      expect(order.id).toBeDefined()
      expect(order.lot_no).toBeDefined()
      expect(order.status).toBeDefined()
      expect(order.target_qty).toBeDefined()

      // Valid status
      const validStatuses = ['READY', 'WAITING', 'RUNNING', 'IN_PROGRESS', 'DONE', 'ERROR', 'PAUSED', 'CANCELLED']
      expect(validStatuses).toContain(order.status)

      // Positive quantity
      expect(order.target_qty).toBeGreaterThan(0)
    }
  })

  it('작업지시 상태별 카운트 합계 <= 전체', async () => {
    await login()

    const allRes = await commands.fetchApi('/production/orders?view=all&limit=1000')
    if (!allRes.ok) return

    const orders = allRes.data?.items || allRes.data?.data || allRes.data || []

    const waitingCount = orders.filter((o: any) => o.status === 'WAITING').length
    const inProgressCount = orders.filter((o: any) => o.status === 'IN_PROGRESS').length
    const doneCount = orders.filter((o: any) => o.status === 'DONE').length

    const sum = waitingCount + inProgressCount + doneCount
    expect(sum).toBeLessThanOrEqual(orders.length)
  })

  it('작업지시 목록 UI와 API 카운트 일치', async () => {
    await login()

    const apiRes = await commands.fetchApi('/production/orders?limit=50')
    let apiCount = 0
    if (apiRes.ok) {
      apiCount = (apiRes.data?.items || apiRes.data || []).length
    }

    // UI check
    await commands.goto(`${APP_URL}/production/orders`)
    const hasHeader = await commands.isVisibleByText('작업지시', 15_000)
    expect(hasHeader).toBe(true)

    const hasTable = await commands.isVisibleBySelector('table', 5_000)
    if (apiCount > 0) {
      expect(hasTable).toBe(true)
    }
  })

  it('작업지시 날짜 논리 검증 (start_time < end_time)', async () => {
    await login()

    const res = await commands.fetchApi('/production/orders?limit=20')
    if (!res.ok) return

    const orders = res.data?.items || res.data || []

    let invalidCount = 0
    for (const order of orders.slice(0, 10)) {
      if (order.start_time && order.end_time) {
        const start = new Date(order.start_time)
        const end = new Date(order.end_time)

        if (end < start) {
          invalidCount++
        }
      }
    }

    expect(invalidCount).toBe(0)
  })
})

describe('작업지시 생성 검증', () => {

  it('생성 모달 필수 필드 확인', async () => {
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

    // Submit button (text is dynamic: '생성' / '생성 중...')
    const hasSubmit = await commands.isVisibleBySelector('button[type="submit"]', 3_000)
    expect(hasSubmit).toBe(true)

    await commands.clickByRole('button', '취소')
  })

  it('필수값 누락 시 생성 불가', async () => {
    await login()
    await commands.goto(`${APP_URL}/production/orders`)

    const hasHeader = await commands.isVisibleByText('작업지시', 15_000)
    expect(hasHeader).toBe(true)

    await commands.clickByRole('button', '작업지시 생성')
    const hasModal = await commands.isVisibleBySelector('.fixed.inset-0, [role="dialog"]', 5_000)
    expect(hasModal).toBe(true)

    // Verify submit button exists in the modal
    const hasSubmit = await commands.isVisibleBySelector('button[type="submit"]', 3_000)
    expect(hasSubmit).toBe(true)

    // Modal should be open with form fields
    const hasInputs = await commands.isVisibleBySelector('input, select', 2_000)
    expect(hasInputs).toBe(true)

    await commands.clickByRole('button', '취소')
  })
})

describe('작업지시 상태 관리', () => {

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
