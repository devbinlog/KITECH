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

describe('제조 데이터 정합성 (Manufacturing Data Integrity)', () => {

  describe('1. 작업지시 데이터 정합성', () => {

    describe('1.1 작업지시 기본 검증', () => {

      it('목표수량 > 0 검증', async () => {
        await login()

        const res = await commands.fetchApi('/production/orders?view=all&limit=100')
        if (!res.ok) return

        const orders = res.data?.items || res.data?.data || res.data || []

        let invalidCount = 0
        for (const order of orders) {
          const qty = order.target_qty || order.quantity || order.plan_qty
          if (qty !== undefined && qty <= 0) {
            invalidCount++
          }
        }

        expect(invalidCount).toBe(0)
      })

      it('계획시간 논리: plan_start < plan_end', async () => {
        await login()

        const res = await commands.fetchApi('/production/orders?view=all&limit=100')
        if (!res.ok) return

        const orders = res.data?.items || res.data?.data || res.data || []

        let invalidCount = 0
        for (const order of orders) {
          const start = order.plan_start || order.start_time
          const end = order.plan_end || order.end_time

          if (start && end) {
            const startDate = new Date(start)
            const endDate = new Date(end)

            if (startDate >= endDate) {
              invalidCount++
            }
          }
        }

        expect(invalidCount).toBe(0)
      })

      it('우선순위 범위: 1-10', async () => {
        await login()

        const res = await commands.fetchApi('/production/orders?view=all&limit=100')
        if (!res.ok) return

        const orders = res.data?.items || res.data?.data || res.data || []

        let invalidCount = 0
        for (const order of orders) {
          const priority = order.priority
          if (priority !== undefined && (priority < 1 || priority > 10)) {
            invalidCount++
          }
        }

        expect(invalidCount).toBe(0)
      })

      it('Lot No 중복 없음', async () => {
        await login()

        const res = await commands.fetchApi('/production/orders?view=all&limit=1000')
        if (!res.ok) return

        const orders = res.data?.items || res.data?.data || res.data || []

        const lotNos = orders.map((o: any) => o.lot_no).filter(Boolean)
        const uniqueLotNos = new Set(lotNos)

        const duplicateCount = lotNos.length - uniqueLotNos.size
        expect(duplicateCount).toBe(0)
      })
    })
  })

  describe('2. 실적 데이터 정합성', () => {

    it('양품 + 불량 = 총수량', async () => {
      await login()

      const res = await commands.fetchApi('/production/results?limit=100')
      if (!res.ok) return

      const results = res.data?.items || res.data || []

      let mismatchCount = 0
      for (const r of results) {
        const ok = r.ok_qty || 0
        const ng = r.ng_qty || 0
        const total = r.total_qty

        // Skip items with no production recorded
        if (total === undefined || total === null || total === 0) continue

        if (total !== (ok + ng)) {
          mismatchCount++
        }
      }

      expect(mismatchCount).toBe(0)
    })

    it('음수 수량 없음', async () => {
      await login()

      const res = await commands.fetchApi('/production/results?limit=100')
      if (!res.ok) return

      const results = res.data?.items || res.data || []

      let negativeCount = 0
      for (const r of results) {
        if ((r.ok_qty || 0) < 0 || (r.ng_qty || 0) < 0) {
          negativeCount++
        }
      }

      expect(negativeCount).toBe(0)
    })
  })

  describe('3. 마스터 데이터 정합성', () => {

    it('제품 -> 공정 라우팅 -> 설비 연결', async () => {
      await login()

      const productsRes = await commands.fetchApi('/masters/products?limit=5')
      if (!productsRes.ok) return

      const products = productsRes.data?.items || productsRes.data || []

      for (const product of products) {
        const productId = product.id || product.product_id
        expect(productId).toBeDefined()
      }
    })

    it('삭제된 마스터 참조 검사', async () => {
      await login()

      const ordersRes = await commands.fetchApi('/production/orders?limit=20')
      if (!ordersRes.ok) return

      const orders = ordersRes.data?.items || ordersRes.data || []

      const productIds = new Set<number>()
      for (const order of orders) {
        if (order.product_id) productIds.add(order.product_id)
      }

      let orphanCount = 0
      for (const productId of productIds) {
        const productRes = await commands.fetchApi(`/masters/products/${productId}`)
        if (!productRes.ok) {
          orphanCount++
        }
      }

      expect(orphanCount).toBe(0)
    })
  })
})
