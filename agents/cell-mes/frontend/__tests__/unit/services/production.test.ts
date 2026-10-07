import { describe, it, expect, vi, beforeEach } from 'vitest'
import api from '@/lib/axios'

vi.mock('@/lib/axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}))

const mockApi = api as any

import { productionService } from '@/services/production'

beforeEach(() => {
  vi.clearAllMocks()
})

describe('productionService', () => {
  describe('getOrders', () => {
    it('should GET /api/v1/production/orders with default params', async () => {
      const expected = { items: [], total: 0, page: 1, limit: 30 }
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await productionService.getOrders()

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/production/orders', {
        params: {
          status: undefined,
          view: undefined,
          date_from: undefined,
          date_to: undefined,
          page: 1,
          limit: 30,
          sort_by: 'plan_start',
          sort_order: 'asc',
        },
      })
      expect(result).toEqual(expected)
    })

    it('should GET with all filters mapped correctly', async () => {
      const expected = { items: [{ id: 1 }], total: 1, page: 2, limit: 10 }
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await productionService.getOrders({
        status: 'RUNNING',
        page: 2,
        limit: 10,
        sortBy: 'due_date',
        sortOrder: 'desc',
        dateFrom: '2024-01-01',
        dateTo: '2024-01-31',
        view: 'today',
      })

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/production/orders', {
        params: {
          status: 'RUNNING',
          view: 'today',
          date_from: '2024-01-01',
          date_to: '2024-01-31',
          page: 2,
          limit: 10,
          sort_by: 'due_date',
          sort_order: 'desc',
        },
      })
      expect(result).toEqual(expected)
    })
  })

  describe('getOrderById', () => {
    it('should GET /api/v1/production/orders/1', async () => {
      const expected = { id: 1, lot_no: 'LOT-001', status: 'READY' }
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await productionService.getOrderById(1)

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/production/orders/1')
      expect(result).toEqual(expected)
    })
  })

  describe('createOrder', () => {
    it('should POST /api/v1/production/orders with data', async () => {
      const data = { lot_no: 'LOT-001', product_id: 1, target_qty: 100 }
      const expected = { id: 1, ...data, status: 'READY' }
      mockApi.post.mockResolvedValue({ data: expected })

      const result = await productionService.createOrder(data)

      expect(mockApi.post).toHaveBeenCalledWith('/api/v1/production/orders', data)
      expect(result).toEqual(expected)
    })
  })

  describe('updateOrderStatus', () => {
    it('should PATCH /api/v1/production/orders/1/status with status', async () => {
      const expected = { id: 1, lot_no: 'LOT-001', status: 'RUNNING' }
      mockApi.patch.mockResolvedValue({ data: expected })

      const result = await productionService.updateOrderStatus(1, 'RUNNING')

      expect(mockApi.patch).toHaveBeenCalledWith('/api/v1/production/orders/1/status', {
        status: 'RUNNING',
      })
      expect(result).toEqual(expected)
    })
  })

  describe('getResults', () => {
    it('should GET /api/v1/production/results with default params', async () => {
      const expected = { items: [], total: 0, page: 1, limit: 30 }
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await productionService.getResults()

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/production/results', {
        params: {
          work_order_id: undefined,
          page: 1,
          limit: 30,
        },
      })
      expect(result).toEqual(expected)
    })

    it('should GET with workOrderId and page filters', async () => {
      const expected = { items: [{ id: 1 }], total: 1, page: 2, limit: 30 }
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await productionService.getResults({ workOrderId: 5, page: 2 })

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/production/results', {
        params: {
          work_order_id: 5,
          page: 2,
          limit: 30,
        },
      })
      expect(result).toEqual(expected)
    })
  })

  describe('createResult', () => {
    it('should POST /api/v1/production/results with data', async () => {
      const data = { work_order_id: 1, ok_qty: 95, ng_qty: 5 }
      const expected = { id: 1, ...data }
      mockApi.post.mockResolvedValue({ data: expected })

      const result = await productionService.createResult(data)

      expect(mockApi.post).toHaveBeenCalledWith('/api/v1/production/results', data)
      expect(result).toEqual(expected)
    })
  })

  describe('getWorkInfo', () => {
    it('should GET /api/v1/production/middleware/work-info with lot_no param', async () => {
      const expected = { lot_no: 'LOT-001', product: 'Widget A', status: 'RUNNING' }
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await productionService.getWorkInfo('LOT-001')

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/production/middleware/work-info', {
        params: { lot_no: 'LOT-001' },
      })
      expect(result).toEqual(expected)
    })
  })

  describe('unit scenario changes', () => {
    it('should POST scenario-hold for a unit', async () => {
      const expected = { unit_id: 2, status: 'SCENARIO_HOLD' }
      mockApi.post.mockResolvedValue({ data: expected })

      const result = await productionService.holdUnitScenario(1, 2)

      expect(mockApi.post).toHaveBeenCalledWith('/api/v1/production/orders/1/units/2/scenario-hold')
      expect(result).toEqual(expected)
    })

    it('should PATCH scenario for a held unit', async () => {
      const expected = { unit_id: 2, status: 'READY', scenario_id: 9 }
      mockApi.patch.mockResolvedValue({ data: expected })

      const result = await productionService.updateUnitScenario(1, 2, 9)

      expect(mockApi.patch).toHaveBeenCalledWith('/api/v1/production/orders/1/units/2/scenario', {
        scenario_id: 9,
      })
      expect(result).toEqual(expected)
    })

    it('should POST scenario-release for a held unit', async () => {
      const expected = { unit_id: 2, status: 'READY' }
      mockApi.post.mockResolvedValue({ data: expected })

      const result = await productionService.releaseUnitScenarioHold(1, 2)

      expect(mockApi.post).toHaveBeenCalledWith('/api/v1/production/orders/1/units/2/scenario-release')
      expect(result).toEqual(expected)
    })
  })
})
