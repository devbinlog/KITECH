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

import { schedulerService } from '@/services/scheduler'

beforeEach(() => {
  vi.clearAllMocks()
})

describe('schedulerService', () => {
  describe('getCurrentSchedule', () => {
    it('should GET /api/v1/scheduler/current-schedule with default includeRunning true', async () => {
      const expected = { date: '2024-06-15', availability: [], summary: {} }
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await schedulerService.getCurrentSchedule({ date: '2024-06-15' })

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/scheduler/current-schedule', {
        params: { date: '2024-06-15', include_running: true },
      })
      expect(result).toEqual(expected)
    })

    it('should GET with include_running false when explicitly set', async () => {
      const expected = { date: '2024-06-15', availability: [], summary: {} }
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await schedulerService.getCurrentSchedule({
        date: '2024-06-15',
        includeRunning: false,
      })

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/scheduler/current-schedule', {
        params: { date: '2024-06-15', include_running: false },
      })
      expect(result).toEqual(expected)
    })
  })

  describe('getEquipmentAvailability', () => {
    it('should GET /api/v1/scheduler/equipment-availability with empty params when no ids', async () => {
      const expected = { machines: [], count: 0 }
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await schedulerService.getEquipmentAvailability()

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/scheduler/equipment-availability', {
        params: {},
      })
      expect(result).toEqual(expected)
    })

    it('should GET with equipment_ids as comma-separated string', async () => {
      const expected = { machines: [{ machine_id: '1' }], count: 2 }
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await schedulerService.getEquipmentAvailability([1, 2])

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/scheduler/equipment-availability', {
        params: { equipment_ids: '1,2' },
      })
      expect(result).toEqual(expected)
    })
  })

  describe('getWorkOrdersForScheduling', () => {
    it('should GET /api/v1/scheduler/work-orders with default READY status and limit 100', async () => {
      const expected = { work_orders: [], count: 0 }
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await schedulerService.getWorkOrdersForScheduling()

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/scheduler/work-orders', {
        params: { status: 'READY', limit: 100 },
      })
      expect(result).toEqual(expected)
    })

    it('should GET with custom status and limit', async () => {
      const expected = { work_orders: [{ id: 1 }], count: 1 }
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await schedulerService.getWorkOrdersForScheduling('RUNNING', 50)

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/scheduler/work-orders', {
        params: { status: 'RUNNING', limit: 50 },
      })
      expect(result).toEqual(expected)
    })
  })

  describe('createSchedulingRequest', () => {
    it('should POST /api/v1/scheduler/create-request with params', async () => {
      const params = { horizon_hours: 24, include_running: true }
      const expected = { request: {}, work_orders: [], machines: [], machine_type_params: {} }
      mockApi.post.mockResolvedValue({ data: expected })

      const result = await schedulerService.createSchedulingRequest(params)

      expect(mockApi.post).toHaveBeenCalledWith('/api/v1/scheduler/create-request', params)
      expect(result).toEqual(expected)
    })
  })

  describe('processSchedulingResult', () => {
    it('should POST /api/v1/scheduler/process-result with result', async () => {
      const schedulingResult = {
        status: 'OPTIMAL',
        scheduled_tasks: [],
        statistics: { total_tasks: 5, makespan_seconds: 3600, makespan_hours: 1, machine_utilization: {}, bottleneck_machines: [], solve_time_sec: 2.5, objective_value: 100 },
      }
      const expected = { success: true, message: 'Applied', updated_orders: [] }
      mockApi.post.mockResolvedValue({ data: expected })

      const result = await schedulerService.processSchedulingResult(schedulingResult)

      expect(mockApi.post).toHaveBeenCalledWith('/api/v1/scheduler/process-result', schedulingResult)
      expect(result).toEqual(expected)
    })
  })

  describe('getMachineTypeParams', () => {
    it('should GET /api/v1/scheduler/machine-type-params', async () => {
      const expected = { machine_types: { CNC: { setup_time: 10 } } }
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await schedulerService.getMachineTypeParams()

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/scheduler/machine-type-params')
      expect(result).toEqual(expected)
    })
  })

  describe('solveSchedule', () => {
    it('should POST /api/v1/scheduler/solve with default params', async () => {
      const expected = { scheduling_result: { status: 'OPTIMAL' }, processing_result: null }
      mockApi.post.mockResolvedValue({ data: expected })

      const result = await schedulerService.solveSchedule({})

      expect(mockApi.post).toHaveBeenCalledWith('/api/v1/scheduler/solve', {
        horizon_hours: 24,
        include_running: false,
        include_scheduled: false,
        solver_type: 'OR_TOOLS',
        time_limit_sec: undefined,
        auto_apply: false,
      }, { signal: undefined })
      expect(result).toEqual(expected)
    })

    it('should POST /api/v1/scheduler/solve with merged custom params', async () => {
      const expected = { scheduling_result: { status: 'OPTIMAL' }, processing_result: null }
      mockApi.post.mockResolvedValue({ data: expected })

      const result = await schedulerService.solveSchedule({
        horizon_hours: 48,
        solver_type: 'GA',
      })

      expect(mockApi.post).toHaveBeenCalledWith('/api/v1/scheduler/solve', {
        horizon_hours: 48,
        include_running: false,
        include_scheduled: false,
        solver_type: 'GA',
        time_limit_sec: undefined,
        auto_apply: false,
      }, { signal: undefined })
      expect(result).toEqual(expected)
    })
  })

  describe('approveSchedule', () => {
    it('should POST /api/v1/scheduler/process-result with result', async () => {
      const schedulingResult = {
        status: 'OPTIMAL',
        scheduled_tasks: [{ wo_id: '1', op_id: '1', machine_id: 'M1', start_time: 0, end_time: 100, quantity: 10 }],
        statistics: { total_tasks: 1, makespan_seconds: 100, makespan_hours: 0.03, machine_utilization: {}, bottleneck_machines: [], solve_time_sec: 1, objective_value: 50 },
      }
      const expected = { success: true, message: 'Schedule applied', updated_orders: [{ id: 1 }] }
      mockApi.post.mockResolvedValue({ data: expected })

      const result = await schedulerService.approveSchedule(schedulingResult)

      expect(mockApi.post).toHaveBeenCalledWith('/api/v1/scheduler/process-result', schedulingResult)
      expect(result).toEqual(expected)
    })
  })
})
