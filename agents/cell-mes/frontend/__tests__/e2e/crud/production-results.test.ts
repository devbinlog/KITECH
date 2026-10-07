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

describe('생산실적 CRUD 테스트', () => {
  describe('Read: 목록 조회', () => {
    it('페이지 로드 및 제목 확인', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/results`)

      const hasHeading = await commands.isVisibleByRole('heading', '생산 실적')
      expect(hasHeading).toBe(true)
    })

    it('통계 카드 4개 모두 표시', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/results`)
      await commands.waitForTimeout(2000)

      const cards = ['총 실적 건수', '양품 수량', '불량 수량', '수율']
      for (const card of cards) {
        const hasCard = await commands.isVisibleByText(card, 5_000)
        expect(hasCard).toBe(true)
      }
    })

    it('수율 카드에 % 기호 표시', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/results`)
      await commands.waitForTimeout(2000)

      const hasPercent = await commands.isVisibleByText('%', 5_000)
      expect(hasPercent).toBe(true)
    })

    it('테이블 또는 빈 상태 표시', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/results`)
      await commands.waitForTimeout(2000)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      const hasEmpty = await commands.isVisibleByText('생산 실적이 없습니다', 3_000)
      expect(hasTable || hasEmpty).toBe(true)
    })

    it('테이블 헤더 확인 (데이터 있는 경우)', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/results`)
      await commands.waitForTimeout(2000)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      if (hasTable) {
        const headers = ['Lot No', '양품', '불량', '수율', '시작', '종료', '소요시간']
        for (const header of headers) {
          const hasHeader = await commands.isVisibleByText(header, 3_000)
          expect(hasHeader).toBe(true)
        }
      }
    })
  })

  describe('Read: API 검증', () => {
    it('GET /results 유효한 응답 반환', async () => {
      const result = await commands.fetchApi('/production/results?limit=5')
      expect(result.ok).toBe(true)
      expect(result.status).toBe(200)
      expect(result.data).toHaveProperty('items')
      expect(result.data).toHaveProperty('total')
      expect(result.data).toHaveProperty('pages')
      expect(Array.isArray(result.data.items)).toBe(true)
    })

    it('결과 항목에 필수 필드 포함', async () => {
      const result = await commands.fetchApi('/production/results?limit=5')
      expect(result.ok).toBe(true)

      if (result.data.items.length > 0) {
        const item = result.data.items[0]
        expect(item).toHaveProperty('id')
        expect(item).toHaveProperty('work_order_id')
        expect(item).toHaveProperty('ok_qty')
        expect(item).toHaveProperty('ng_qty')
      }
    })
  })

  describe('Create: 실적 등록 모달', () => {
    it('실적 등록 버튼 표시', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/results`)

      const hasBtn = await commands.isVisibleByRole('button', '실적 등록')
      expect(hasBtn).toBe(true)
    })

    it('실적 등록 모달 열기 및 폼 필드 확인', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/results`)
      await commands.waitForTimeout(1000)

      await commands.clickByRole('button', '실적 등록')
      await commands.waitForTimeout(500)

      // 모달 제목
      const hasTitle = await commands.isVisibleByText('생산 실적 등록', 5_000)
      expect(hasTitle).toBe(true)

      // 작업지시 선택
      const hasSelect = await commands.isVisibleBySelector('select', 3_000)
      expect(hasSelect).toBe(true)

      // 양품/불량 수량 입력
      const hasNumberInput = await commands.isVisibleBySelector('input[type="number"]', 3_000)
      expect(hasNumberInput).toBe(true)

      // 라벨 텍스트
      const hasWoLabel = await commands.isVisibleByText('작업지시 선택', 3_000)
      expect(hasWoLabel).toBe(true)

      const hasOkLabel = await commands.isVisibleByText('양품 수량', 3_000)
      expect(hasOkLabel).toBe(true)

      const hasNgLabel = await commands.isVisibleByText('불량 수량', 3_000)
      expect(hasNgLabel).toBe(true)

      // 설명 텍스트 (optional - may not be visible if no running orders)
      const hasHelp = await commands.isVisibleByText('RUNNING', 3_000)

      // 등록/취소 버튼
      const hasSubmitBtn = await commands.isVisibleBySelector('button[type="submit"]', 3_000)
      const hasCancelBtn = await commands.isVisibleByRole('button', '취소')
      expect(hasSubmitBtn || hasCancelBtn).toBe(true)

      // 취소
      await commands.clickByRole('button', '취소')
      await commands.waitForTimeout(500)
    })

    it('모달 취소 시 닫힘', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/results`)
      await commands.waitForTimeout(1000)

      await commands.clickByRole('button', '실적 등록')
      await commands.waitForTimeout(500)

      const hasModal = await commands.isVisibleBySelector('.fixed.inset-0', 3_000)
      expect(hasModal).toBe(true)

      await commands.clickByRole('button', '취소')
      await commands.waitForTimeout(500)

      // 페이지 제목이 다시 보여야 함
      const hasHeading = await commands.isVisibleByRole('heading', '생산 실적')
      expect(hasHeading).toBe(true)
    })
  })

  describe('Create & Verify: API를 통한 실적 등록 흐름', () => {
    it('작업지시 생성 -> 실적 등록 -> 확인 -> 정리', async () => {
      // 1. 제품 확인
      const productsResult = await commands.fetchApi('/masters/products')
      expect(productsResult.ok).toBe(true)
      if (productsResult.data.length === 0) return

      const productId = productsResult.data[0].id
      const lotNo = `VT-RES-${Date.now()}`

      // 2. 작업지시 생성
      const woResult = await commands.fetchApi(
        '/production/orders',
        'POST',
        JSON.stringify({
          lot_no: lotNo,
          product_id: productId,
          target_qty: 100,
          qty: 1,
          priority: 5,
        })
      )
      expect(woResult.ok).toBe(true)
      const woId = woResult.data.id

      // 3. 작업지시를 RUNNING 상태로 변경
      const startResult = await commands.fetchApi(
        `/production/orders/${woId}/status`,
        'PATCH',
        JSON.stringify({ status: 'RUNNING' })
      )
      expect(startResult.ok).toBe(true)

      // 4. 실적 등록
      const resultCreate = await commands.fetchApi(
        '/production/results',
        'POST',
        JSON.stringify({
          work_order_id: woId,
          ok_qty: 90,
          ng_qty: 10,
        })
      )
      expect(resultCreate.ok).toBe(true)
      expect(resultCreate.data).toHaveProperty('id')

      // 5. 실적 목록에서 확인
      const listResult = await commands.fetchApi('/production/results?limit=100')
      expect(listResult.ok).toBe(true)
      const found = listResult.data.items.find((r: any) => r.work_order_id === woId)
      expect(found).toBeDefined()
      expect(found.ok_qty).toBe(90)
      expect(found.ng_qty).toBe(10)

      // 6. 정리: 작업지시 완료 후 삭제
      await commands.fetchApi(`/production/orders/${woId}/status`, 'PATCH', JSON.stringify({ status: 'DONE' }))
      await commands.fetchApi(`/production/orders/${woId}`, 'DELETE')
    })
  })

  describe('Pagination', () => {
    it('페이지네이션 텍스트 표시 (데이터 있는 경우)', async () => {
      await login()
      await commands.goto(`${APP_URL}/production/results`)
      await commands.waitForTimeout(2000)

      const hasTable = await commands.isVisibleBySelector('table', 5_000)
      if (hasTable) {
        const hasPagination = await commands.isVisibleByText('총.*건 중', 5_000)
        expect(hasPagination).toBe(true)
      }
    })
  })
})
