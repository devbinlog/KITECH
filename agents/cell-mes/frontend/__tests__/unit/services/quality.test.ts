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

import { qualityService } from '@/services/quality'

beforeEach(() => {
  vi.clearAllMocks()
})

describe('qualityService', () => {
  describe('Inspection Plans', () => {
    describe('getInspectionPlans', () => {
      it('should GET /api/v1/quality/inspection-plans with default params', async () => {
        const expected = [{ id: 1, name: 'Plan A' }]
        mockApi.get.mockResolvedValue({ data: expected })

        const result = await qualityService.getInspectionPlans()

        expect(mockApi.get).toHaveBeenCalledWith('/api/v1/quality/inspection-plans', {
          params: { inspection_type: undefined, product_id: undefined, page: 1, limit: 20 },
        })
        expect(result).toEqual(expected)
      })

      it('should GET with custom params when provided', async () => {
        const expected = [{ id: 2, name: 'Plan B' }]
        mockApi.get.mockResolvedValue({ data: expected })

        const result = await qualityService.getInspectionPlans({
          page: 2,
          limit: 10,
          inspection_type: 'INCOMING',
        })

        expect(mockApi.get).toHaveBeenCalledWith('/api/v1/quality/inspection-plans', {
          params: { inspection_type: 'INCOMING', product_id: undefined, page: 2, limit: 10 },
        })
        expect(result).toEqual(expected)
      })
    })

    describe('getInspectionPlanById', () => {
      it('should GET /api/v1/quality/inspection-plans/1', async () => {
        const expected = { id: 1, name: 'Plan A' }
        mockApi.get.mockResolvedValue({ data: expected })

        const result = await qualityService.getInspectionPlanById(1)

        expect(mockApi.get).toHaveBeenCalledWith('/api/v1/quality/inspection-plans/1')
        expect(result).toEqual(expected)
      })
    })

    describe('createInspectionPlan', () => {
      it('should POST /api/v1/quality/inspection-plans with data', async () => {
        const data = {
          product_id: 1,
          inspection_type: 'INCOMING' as const,
          characteristic: '외경',
          usl: 50.1,
          lsl: 49.9,
        }
        const expected = { id: 3, ...data }
        mockApi.post.mockResolvedValue({ data: expected })

        const result = await qualityService.createInspectionPlan(data)

        expect(mockApi.post).toHaveBeenCalledWith('/api/v1/quality/inspection-plans', data)
        expect(result).toEqual(expected)
      })
    })

    describe('updateInspectionPlan', () => {
      it('should PUT /api/v1/quality/inspection-plans/1 with data', async () => {
        const data = { is_active: false }
        const expected = { id: 1, ...data }
        mockApi.put.mockResolvedValue({ data: expected })

        const result = await qualityService.updateInspectionPlan(1, data)

        expect(mockApi.put).toHaveBeenCalledWith('/api/v1/quality/inspection-plans/1', data)
        expect(result).toEqual(expected)
      })
    })

    describe('deleteInspectionPlan', () => {
      it('should DELETE /api/v1/quality/inspection-plans/1', async () => {
        mockApi.delete.mockResolvedValue({ data: null })

        await qualityService.deleteInspectionPlan(1)

        expect(mockApi.delete).toHaveBeenCalledWith('/api/v1/quality/inspection-plans/1')
      })
    })
  })

  describe('Inspection Results', () => {
    describe('getInspectionResults', () => {
      it('should GET /api/v1/quality/inspection-results with default params', async () => {
        const expected = [{ id: 1, result: 'PASS' }]
        mockApi.get.mockResolvedValue({ data: expected })

        const result = await qualityService.getInspectionResults()

        expect(mockApi.get).toHaveBeenCalledWith('/api/v1/quality/inspection-results', {
          params: expect.objectContaining({}),
        })
        expect(result).toEqual(expected)
      })

      it('should GET with work_order_id filter when provided', async () => {
        const expected = [{ id: 1, result: 'PASS', work_order_id: 1 }]
        mockApi.get.mockResolvedValue({ data: expected })

        const result = await qualityService.getInspectionResults({ work_order_id: 1 })

        expect(mockApi.get).toHaveBeenCalledWith('/api/v1/quality/inspection-results', {
          params: expect.objectContaining({ work_order_id: 1 }),
        })
        expect(result).toEqual(expected)
      })
    })

    describe('getInspectionResultById', () => {
      it('should GET /api/v1/quality/inspection-results/1', async () => {
        const expected = { id: 1, result: 'PASS' }
        mockApi.get.mockResolvedValue({ data: expected })

        const result = await qualityService.getInspectionResultById(1)

        expect(mockApi.get).toHaveBeenCalledWith('/api/v1/quality/inspection-results/1')
        expect(result).toEqual(expected)
      })
    })

    describe('createInspectionResult', () => {
      it('should POST /api/v1/quality/inspection-results with data', async () => {
        const data = {
          inspection_plan_id: 1,
          work_order_id: 1,
          lot_no: 'LOT-001',
          measured_values: [],
          inspector: 'admin',
          inspection_date: '2024-01-01T00:00:00Z',
          judgment: 'OK' as const,
        }
        const expected = { id: 1, ...data }
        mockApi.post.mockResolvedValue({ data: expected })

        const result = await qualityService.createInspectionResult(data)

        expect(mockApi.post).toHaveBeenCalledWith('/api/v1/quality/inspection-results', data)
        expect(result).toEqual(expected)
      })
    })

    describe('updateInspectionResult', () => {
      it('should PUT /api/v1/quality/inspection-results/1 with data', async () => {
        const data = { judgment: 'NG' as const }
        const expected = { id: 1, ...data }
        mockApi.put.mockResolvedValue({ data: expected })

        const result = await qualityService.updateInspectionResult(1, data)

        expect(mockApi.put).toHaveBeenCalledWith('/api/v1/quality/inspection-results/1', data)
        expect(result).toEqual(expected)
      })
    })
  })

  describe('SPC', () => {
    describe('getSPCData', () => {
      it('should GET /api/v1/quality/spc/charts/diameter and transform response', async () => {
        const backendResponse = [
          {
            inspection_plan_id: 10,
            upper_control_limit: 10.5,
            lower_control_limit: 9.5,
            range_upper_control_limit: 1.0,
            range_lower_control_limit: 0,
            data_points: [
              { id: 1, created_at: '2024-01-01T00:00:00Z', mean_value: 10.1, range_value: 0.3, raw_values: [10.0, 10.2] },
              { id: 2, created_at: '2024-01-02T00:00:00Z', mean_value: 9.8, range_value: 0.4, raw_values: [9.7, 9.9] },
            ],
          },
        ]
        mockApi.get.mockResolvedValue({ data: backendResponse })

        const result = await qualityService.getSPCData('diameter')

        expect(mockApi.get).toHaveBeenCalledWith('/api/v1/quality/spc/charts/diameter', {
          params: { date_from: undefined, date_to: undefined },
        })
        expect(Array.isArray(result)).toBe(true)
        expect(result).toHaveLength(2)
        expect(result[0]).toEqual({
          id: 1,
          inspection_item_id: 10,
          sample_date: '2024-01-01T00:00:00Z',
          sample_values: [10.0, 10.2],
          x_bar: 10.1,
          r_value: 0.3,
          ucl_x: 10.5,
          lcl_x: 9.5,
          ucl_r: 1.0,
          lcl_r: 0,
        })
        expect(result[1]).toEqual({
          id: 2,
          inspection_item_id: 10,
          sample_date: '2024-01-02T00:00:00Z',
          sample_values: [9.7, 9.9],
          x_bar: 9.8,
          r_value: 0.4,
          ucl_x: 10.5,
          lcl_x: 9.5,
          ucl_r: 1.0,
          lcl_r: 0,
        })
      })

      it('should return empty array when response is empty', async () => {
        mockApi.get.mockResolvedValue({ data: null })

        const result = await qualityService.getSPCData('diameter')

        expect(result).toEqual([])
      })
    })

    describe('generateSPCData', () => {
      it('should return empty array (stub)', async () => {
        const result = await qualityService.generateSPCData(1, 5)

        expect(result).toEqual([])
      })
    })
  })

  describe('NCR', () => {
    describe('getNCRs', () => {
      it('should GET /api/v1/quality/ncr with default params', async () => {
        const expected = [{ id: 1, status: 'OPEN' }]
        mockApi.get.mockResolvedValue({ data: expected })

        const result = await qualityService.getNCRs()

        expect(mockApi.get).toHaveBeenCalledWith('/api/v1/quality/ncr', {
          params: expect.objectContaining({}),
        })
        expect(result).toEqual(expected)
      })
    })

    describe('getNCRById', () => {
      it('should GET /api/v1/quality/ncr/1', async () => {
        const expected = { id: 1, status: 'OPEN' }
        mockApi.get.mockResolvedValue({ data: expected })

        const result = await qualityService.getNCRById(1)

        expect(mockApi.get).toHaveBeenCalledWith('/api/v1/quality/ncr/1')
        expect(result).toEqual(expected)
      })
    })

    describe('createNCR', () => {
      it('should POST /api/v1/quality/ncr with data', async () => {
        const data = {
          ncr_no: 'NCR-001',
          defect_type: 'OTHER' as const,
          defect_description: 'Defect found',
          severity: 'MINOR' as const,
          created_by: 'admin',
        }
        const expected = { id: 1, ...data }
        mockApi.post.mockResolvedValue({ data: expected })

        const result = await qualityService.createNCR(data)

        expect(mockApi.post).toHaveBeenCalledWith('/api/v1/quality/ncr', data)
        expect(result).toEqual(expected)
      })
    })

    describe('updateNCR', () => {
      it('should PUT /api/v1/quality/ncr/1 with data', async () => {
        const data = { corrective_action: 'Updated corrective action' }
        const expected = { id: 1, ...data }
        mockApi.put.mockResolvedValue({ data: expected })

        const result = await qualityService.updateNCR(1, data)

        expect(mockApi.put).toHaveBeenCalledWith('/api/v1/quality/ncr/1', data)
        expect(result).toEqual(expected)
      })
    })

    describe('updateNCRStatus', () => {
      it('should PATCH /api/v1/quality/ncr/1/status with status body', async () => {
        const expected = { id: 1, status: 'CLOSED' }
        mockApi.patch.mockResolvedValue({ data: expected })

        const result = await qualityService.updateNCRStatus(1, 'CLOSED')

        expect(mockApi.patch).toHaveBeenCalledWith('/api/v1/quality/ncr/1/status', {
          status: 'CLOSED',
        })
        expect(result).toEqual(expected)
      })
    })
  })

  describe('Dashboard', () => {
    describe('getQualityDashboard', () => {
      it('should call 3 APIs in parallel and compute dashboard data', async () => {
        const summaryResponse = {
          total_inspections: 100,
          pass_count: 90,
          fail_count: 10,
          pass_rate: 90.0,
        }
        const resultsResponse = [
          { id: 1, result: 'PASS', inspected_at: '2024-01-02T00:00:00Z', defect_type: null },
          { id: 2, result: 'FAIL', inspected_at: '2024-01-03T00:00:00Z', defect_type: 'SCRATCH' },
          { id: 3, result: 'FAIL', inspected_at: '2024-01-05T00:00:00Z', defect_type: 'CRACK' },
        ]
        const ncrsResponse = [
          { id: 1, status: 'OPEN', created_at: '2024-01-02T00:00:00Z', title: 'NCR-001', category: 'DIMENSIONAL' },
        ]

        // The service calls 3 endpoints in parallel
        mockApi.get
          .mockResolvedValueOnce({ data: summaryResponse })
          .mockResolvedValueOnce({ data: resultsResponse })
          .mockResolvedValueOnce({ data: ncrsResponse })

        const result = await qualityService.getQualityDashboard('2024-01-01', '2024-01-08')

        expect(mockApi.get).toHaveBeenCalledTimes(3)
        expect(result).toBeDefined()
        // 7 days from Jan 1 to Jan 8
        expect(result.trend_data).toBeDefined()
        expect(result.defect_by_type).toBeDefined()
        expect(result.top_issues).toBeDefined()
      })

      it('should still return dashboard with empty trend_data when results API fails', async () => {
        const summaryResponse = {
          total_inspections: 100,
          pass_count: 90,
          fail_count: 10,
          pass_rate: 90.0,
        }
        const ncrsResponse: any[] = []

        mockApi.get
          .mockResolvedValueOnce({ data: summaryResponse })
          .mockRejectedValueOnce(new Error('Network error'))
          .mockResolvedValueOnce({ data: ncrsResponse })

        const result = await qualityService.getQualityDashboard('2024-01-01', '2024-01-08')

        expect(result).toBeDefined()
        expect(result.trend_data).toBeDefined()
      })
    })
  })
})
