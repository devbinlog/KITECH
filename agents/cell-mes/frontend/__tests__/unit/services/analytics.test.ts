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

import { analyticsService } from '@/services/analytics'

beforeEach(() => {
  vi.clearAllMocks()
})

describe('analyticsService', () => {
  describe('getKPIData', () => {
    it('should GET /api/v1/analytics/kpi with default params', async () => {
      const expected = [{ date: '2024-01-01', oee: 85 }]
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await analyticsService.getKPIData()

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/analytics/kpi', {
        params: {
          date_from: undefined,
          date_to: undefined,
          period: 'daily',
          equipment_id: undefined,
        },
      })
      expect(result).toEqual(expected)
    })

    it('should GET with custom filter params', async () => {
      const expected = [{ date: '2024-01-01', oee: 90 }]
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await analyticsService.getKPIData({
        date_from: '2024-01-01',
        period: 'weekly',
      })

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/analytics/kpi', {
        params: {
          date_from: '2024-01-01',
          date_to: undefined,
          period: 'weekly',
          equipment_id: undefined,
        },
      })
      expect(result).toEqual(expected)
    })
  })

  describe('getKPISummary', () => {
    it('should GET /api/v1/analytics/kpi/summary with undefined params by default', async () => {
      const expected = { overall_oee: 85, availability: 90, performance: 92, quality: 98 }
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await analyticsService.getKPISummary()

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/analytics/kpi/summary', {
        params: { date_from: undefined, date_to: undefined },
      })
      expect(result).toEqual(expected)
    })

    it('should GET with date_from and date_to params', async () => {
      const expected = { overall_oee: 88 }
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await analyticsService.getKPISummary('2024-01-01', '2024-01-31')

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/analytics/kpi/summary', {
        params: { date_from: '2024-01-01', date_to: '2024-01-31' },
      })
      expect(result).toEqual(expected)
    })
  })

  describe('getEquipmentUtilization', () => {
    it('should GET /api/v1/analytics/equipment/utilization with default params', async () => {
      const expected = [{ equipment_name: 'CNC-01', utilization: 85 }]
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await analyticsService.getEquipmentUtilization()

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/analytics/equipment/utilization', {
        params: {
          equipment_id: undefined,
          date_from: undefined,
          date_to: undefined,
          period: 'daily',
        },
      })
      expect(result).toEqual(expected)
    })
  })

  describe('getEquipmentEfficiency', () => {
    it('should GET /api/v1/analytics/equipment/efficiency with all undefined params', async () => {
      const expected = { equipment_name: 'All', planned_time: 100, actual_time: 85 }
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await analyticsService.getEquipmentEfficiency()

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/analytics/equipment/efficiency', {
        params: {
          equipment_id: undefined,
          date_from: undefined,
          date_to: undefined,
        },
      })
      expect(result).toEqual(expected)
    })

    it('should GET with equipment_id and date range', async () => {
      const expected = { equipment_name: 'CNC-01', planned_time: 100, actual_time: 90 }
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await analyticsService.getEquipmentEfficiency(1, '2024-01-01', '2024-01-31')

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/analytics/equipment/efficiency', {
        params: {
          equipment_id: 1,
          date_from: '2024-01-01',
          date_to: '2024-01-31',
        },
      })
      expect(result).toEqual(expected)
    })
  })

  describe('getLotTraces', () => {
    it('should GET /api/v1/analytics/lot-trace with default params', async () => {
      const expected = { items: [], total: 0, page: 1, limit: 20 }
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await analyticsService.getLotTraces()

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/analytics/lot-trace', {
        params: {
          date_from: undefined,
          date_to: undefined,
          page: 1,
          limit: 20,
        },
      })
      expect(result).toEqual(expected)
    })
  })

  describe('getLotTraceByLotNo', () => {
    it('should GET /api/v1/analytics/lot-trace/LOT-001', async () => {
      const expected = { lot_no: 'LOT-001', product: 'Widget A' }
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await analyticsService.getLotTraceByLotNo('LOT-001')

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/analytics/lot-trace/LOT-001')
      expect(result).toEqual(expected)
    })
  })

  describe('getLotTraceHistory', () => {
    it('should GET /api/v1/analytics/lot-trace/LOT-001/history', async () => {
      const expected = { lot_info: {}, process_flow: [], quality_checkpoints: [] }
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await analyticsService.getLotTraceHistory('LOT-001')

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/analytics/lot-trace/LOT-001/history')
      expect(result).toEqual(expected)
    })
  })

  describe('getProductionTrends', () => {
    it('should GET /api/v1/analytics/production/trends with default period daily', async () => {
      const expected = { production_volume: [], quality_trends: [], cycle_time_trends: [] }
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await analyticsService.getProductionTrends()

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/analytics/production/trends', {
        params: { date_from: undefined, date_to: undefined, period: 'daily' },
      })
      expect(result).toEqual(expected)
    })
  })

  describe('getResourceUtilization', () => {
    it('should GET /api/v1/analytics/resources with undefined date params', async () => {
      const expected = { equipment_utilization: [], workforce_utilization: [], material_consumption: [] }
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await analyticsService.getResourceUtilization()

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/analytics/resources', {
        params: { date_from: undefined, date_to: undefined },
      })
      expect(result).toEqual(expected)
    })
  })

  describe('getEnergyConsumption', () => {
    it('should GET /api/v1/analytics/energy with undefined params', async () => {
      const expected = { total_consumption: 0, cost: 0, consumption_by_equipment: [] }
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await analyticsService.getEnergyConsumption()

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/analytics/energy', {
        params: {
          equipment_id: undefined,
          date_from: undefined,
          date_to: undefined,
        },
      })
      expect(result).toEqual(expected)
    })
  })

  describe('getPredictiveInsights', () => {
    it('should GET /api/v1/analytics/predictions with undefined equipment_id', async () => {
      const expected = { maintenance_predictions: [], quality_predictions: [], capacity_forecasts: [] }
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await analyticsService.getPredictiveInsights()

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/analytics/predictions', {
        params: { equipment_id: undefined },
      })
      expect(result).toEqual(expected)
    })
  })
})
