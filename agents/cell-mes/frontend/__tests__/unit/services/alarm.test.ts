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

import { alarmDefinitionService, alarmService } from '@/services/alarm'

beforeEach(() => {
  vi.clearAllMocks()
})

describe('alarmDefinitionService', () => {
  describe('getAll', () => {
    it('should GET /api/v1/alarms/definitions with active_only true by default', async () => {
      const expected = [{ id: 1, code: 'ALM001' }]
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await alarmDefinitionService.getAll()

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/alarms/definitions', {
        params: { active_only: true },
      })
      expect(result).toEqual(expected)
    })

    it('should GET with active_only false when passed false', async () => {
      const expected = [{ id: 1, code: 'ALM001' }, { id: 2, code: 'ALM002' }]
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await alarmDefinitionService.getAll(false)

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/alarms/definitions', {
        params: { active_only: false },
      })
      expect(result).toEqual(expected)
    })
  })

  describe('getById', () => {
    it('should GET /api/v1/alarms/definitions/1', async () => {
      const expected = { id: 1, code: 'ALM001' }
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await alarmDefinitionService.getById(1)

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/alarms/definitions/1')
      expect(result).toEqual(expected)
    })
  })

  describe('create', () => {
    it('should POST /api/v1/alarms/definitions with data', async () => {
      const data = { alarm_code: 'ALM003', name: 'Test Alarm', severity: 'WARNING' }
      const expected = { id: 3, ...data }
      mockApi.post.mockResolvedValue({ data: expected })

      const result = await alarmDefinitionService.create(data)

      expect(mockApi.post).toHaveBeenCalledWith('/api/v1/alarms/definitions', data)
      expect(result).toEqual(expected)
    })
  })

  describe('update', () => {
    it('should PATCH /api/v1/alarms/definitions/1 with data', async () => {
      const data = { severity: 'CRITICAL' }
      const expected = { id: 1, code: 'ALM001', severity: 'CRITICAL' }
      mockApi.patch.mockResolvedValue({ data: expected })

      const result = await alarmDefinitionService.update(1, data)

      expect(mockApi.patch).toHaveBeenCalledWith('/api/v1/alarms/definitions/1', data)
      expect(result).toEqual(expected)
    })
  })

  describe('delete', () => {
    it('should DELETE /api/v1/alarms/definitions/1', async () => {
      mockApi.delete.mockResolvedValue({ data: null })

      await alarmDefinitionService.delete(1)

      expect(mockApi.delete).toHaveBeenCalledWith('/api/v1/alarms/definitions/1')
    })
  })
})

describe('alarmService', () => {
  describe('getAll', () => {
    it('should GET /api/v1/alarms with params undefined when no filters', async () => {
      const expected = [{ id: 1, definition_id: 1 }]
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await alarmService.getAll()

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/alarms', {
        params: undefined,
      })
      expect(result).toEqual(expected)
    })

    it('should GET /api/v1/alarms with params when filters provided', async () => {
      const filters = { severity: 'CRITICAL', equipment_id: 1 }
      const expected = [{ id: 1, definition_id: 1 }]
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await alarmService.getAll(filters)

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/alarms', {
        params: filters,
      })
      expect(result).toEqual(expected)
    })
  })

  describe('getActive', () => {
    it('should GET /api/v1/alarms/active', async () => {
      const expected = [{ id: 1, active: true }]
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await alarmService.getActive()

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/alarms/active')
      expect(result).toEqual(expected)
    })
  })

  describe('getById', () => {
    it('should GET /api/v1/alarms/1', async () => {
      const expected = { id: 1, definition_id: 1 }
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await alarmService.getById(1)

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/alarms/1')
      expect(result).toEqual(expected)
    })
  })

  describe('create', () => {
    it('should POST /api/v1/alarms with data', async () => {
      const data = { equipment_id: 1, alarm_code: 'ALM001', severity: 'WARNING', message: 'Test alarm' }
      const expected = { id: 1, ...data }
      mockApi.post.mockResolvedValue({ data: expected })

      const result = await alarmService.create(data)

      expect(mockApi.post).toHaveBeenCalledWith('/api/v1/alarms', data)
      expect(result).toEqual(expected)
    })
  })

  describe('acknowledge', () => {
    it('should POST /api/v1/alarms/1/acknowledge with default admin user', async () => {
      const expected = { id: 1, acknowledged: true }
      mockApi.post.mockResolvedValue({ data: expected })

      const result = await alarmService.acknowledge(1)

      expect(mockApi.post).toHaveBeenCalledWith('/api/v1/alarms/1/acknowledge', {
        acknowledged_by: 'admin',
      })
      expect(result).toEqual(expected)
    })

    it('should POST /api/v1/alarms/1/acknowledge with specified user', async () => {
      const expected = { id: 1, acknowledged: true }
      mockApi.post.mockResolvedValue({ data: expected })

      const result = await alarmService.acknowledge(1, 'user1')

      expect(mockApi.post).toHaveBeenCalledWith('/api/v1/alarms/1/acknowledge', {
        acknowledged_by: 'user1',
      })
      expect(result).toEqual(expected)
    })
  })

  describe('clear', () => {
    it('should POST /api/v1/alarms/1/resolve with default admin and null note', async () => {
      const expected = { id: 1, resolved: true }
      mockApi.post.mockResolvedValue({ data: expected })

      const result = await alarmService.clear(1)

      expect(mockApi.post).toHaveBeenCalledWith('/api/v1/alarms/1/resolve', {
        resolved_by: 'admin',
        resolution_note: null,
      })
      expect(result).toEqual(expected)
    })

    it('should POST /api/v1/alarms/1/resolve with specified user and note', async () => {
      const expected = { id: 1, resolved: true }
      mockApi.post.mockResolvedValue({ data: expected })

      const result = await alarmService.clear(1, 'user1', 'fixed')

      expect(mockApi.post).toHaveBeenCalledWith('/api/v1/alarms/1/resolve', {
        resolved_by: 'user1',
        resolution_note: 'fixed',
      })
      expect(result).toEqual(expected)
    })
  })

  describe('delete', () => {
    it('should DELETE /api/v1/alarms/1', async () => {
      mockApi.delete.mockResolvedValue({ data: null })

      await alarmService.delete(1)

      expect(mockApi.delete).toHaveBeenCalledWith('/api/v1/alarms/1')
    })
  })

  describe('getSummary', () => {
    it('should transform backend object response to array format', async () => {
      const backendResponse = {
        total: 5,
        by_severity: { CRITICAL: 2, WARNING: 3 },
        by_equipment: { EQ1: 1 },
      }
      mockApi.get.mockResolvedValue({ data: backendResponse })

      const result = await alarmService.getSummary()

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/alarms/active/summary', { params: undefined })
      expect(result).toEqual([
        { severity: 'CRITICAL', count: 2, equipment_counts: { EQ1: 1 } },
        { severity: 'WARNING', count: 3, equipment_counts: { EQ1: 1 } },
      ])
    })

    it('should return array as-is when backend returns array', async () => {
      const backendResponse = [
        { severity: 'CRITICAL', count: 2, equipment_counts: {} },
      ]
      mockApi.get.mockResolvedValue({ data: backendResponse })

      const result = await alarmService.getSummary()

      expect(result).toEqual(backendResponse)
    })

    it('should return empty array when backend returns object without by_severity', async () => {
      mockApi.get.mockResolvedValue({ data: {} })

      const result = await alarmService.getSummary()

      expect(result).toEqual([])
    })

    it('should return empty array when backend returns null/undefined data', async () => {
      mockApi.get.mockResolvedValue({ data: null })

      const result = await alarmService.getSummary()

      expect(result).toEqual([])
    })
  })
})
