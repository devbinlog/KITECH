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

import { equipmentService } from '@/services/equipment'

beforeEach(() => {
  vi.clearAllMocks()
})

describe('equipmentService', () => {
  describe('getAll', () => {
    it('should GET /api/v1/masters/equipments with include_deleted false by default', async () => {
      const expected = [{ id: 1, name: 'CNC-01' }]
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await equipmentService.getAll()

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/masters/equipments', {
        params: { include_deleted: false },
      })
      expect(result).toEqual(expected)
    })

    it('should GET with include_deleted true when passed true', async () => {
      const expected = [{ id: 1, name: 'CNC-01' }, { id: 2, name: 'CNC-02', deleted: true }]
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await equipmentService.getAll(true)

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/masters/equipments', {
        params: { include_deleted: true },
      })
      expect(result).toEqual(expected)
    })
  })

  describe('getById', () => {
    it('should GET /api/v1/masters/equipments/1', async () => {
      const expected = { id: 1, name: 'CNC-01' }
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await equipmentService.getById(1)

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/masters/equipments/1')
      expect(result).toEqual(expected)
    })
  })

  describe('getStatus', () => {
    it('should GET /api/v1/masters/equipments/1/status with refresh false by default', async () => {
      const expected = { equipment_id: 1, status: 'RUNNING' }
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await equipmentService.getStatus(1)

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/masters/equipments/1/status', {
        params: { refresh: false },
      })
      expect(result).toEqual(expected)
    })

    it('should GET with refresh true when passed true', async () => {
      const expected = { equipment_id: 1, status: 'IDLE' }
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await equipmentService.getStatus(1, true)

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/masters/equipments/1/status', {
        params: { refresh: true },
      })
      expect(result).toEqual(expected)
    })
  })

  describe('sync', () => {
    it('should POST /api/v1/masters/equipments/sync', async () => {
      const expected = { synced: 5 }
      mockApi.post.mockResolvedValue({ data: expected })

      const result = await equipmentService.sync()

      expect(mockApi.post).toHaveBeenCalledWith('/api/v1/masters/equipments/sync')
      expect(result).toEqual(expected)
    })
  })

  describe('create', () => {
    it('should POST /api/v1/masters/equipments with data', async () => {
      const data: import('@/types').Equipment = {
        id: 3,
        eq_code: 'CNC-03',
        aas_id: null,
        eq_name: 'CNC Machine 03',
        model_name: null,
        equipment_type: 'CNC',
        location: null,
        cell_id: null,
        connection_config: {},
        spec_data: {},
        last_data: {},
        current_status: 'STOP',
        updated_at: '2024-01-01T00:00:00Z',
        last_connected_at: null,
        is_deleted: false,
      }
      const expected = data
      mockApi.post.mockResolvedValue({ data: expected })

      const result = await equipmentService.create(data)

      expect(mockApi.post).toHaveBeenCalledWith('/api/v1/masters/equipments', data)
      expect(result).toEqual(expected)
    })
  })

  describe('delete', () => {
    it('should DELETE /api/v1/masters/equipments/1', async () => {
      mockApi.delete.mockResolvedValue({ data: null })

      await equipmentService.delete(1)

      expect(mockApi.delete).toHaveBeenCalledWith('/api/v1/masters/equipments/1')
    })
  })

  describe('checkMiddlewareHealth', () => {
    it('should GET /api/v1/masters/equipments/middleware-health', async () => {
      const expected = { status: 'healthy', connected: true }
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await equipmentService.checkMiddlewareHealth()

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/masters/equipments/middleware-health')
      expect(result).toEqual(expected)
    })
  })

  describe('getStatusHistory', () => {
    it('should GET /api/v1/masters/equipments/1/status-history with default limit 50', async () => {
      const expected = [{ timestamp: '2024-01-01', status: 'RUNNING' }]
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await equipmentService.getStatusHistory(1)

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/masters/equipments/1/status-history', {
        params: { limit: 50 },
      })
      expect(result).toEqual(expected)
    })

    it('should GET with custom limit when provided', async () => {
      const expected = [{ timestamp: '2024-01-01', status: 'RUNNING' }]
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await equipmentService.getStatusHistory(1, 10)

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/masters/equipments/1/status-history', {
        params: { limit: 10 },
      })
      expect(result).toEqual(expected)
    })
  })
})
