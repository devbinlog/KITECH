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

import { downtimeReasonService, downtimeService } from '@/services/downtime'

beforeEach(() => {
  vi.clearAllMocks()
})

describe('downtimeReasonService', () => {
  describe('getAll', () => {
    it('should GET /api/v1/downtime/reasons with active_only true by default', async () => {
      const expected = [{ id: 1, code: 'DT001', category: 'MECHANICAL' }]
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await downtimeReasonService.getAll()

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/downtime/reasons', {
        params: { active_only: true },
      })
      expect(result).toEqual(expected)
    })

    it('should GET with active_only false when passed false', async () => {
      const expected = [{ id: 1, code: 'DT001' }, { id: 2, code: 'DT002' }]
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await downtimeReasonService.getAll(false)

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/downtime/reasons', {
        params: { active_only: false },
      })
      expect(result).toEqual(expected)
    })
  })

  describe('getById', () => {
    it('should GET /api/v1/downtime/reasons/1', async () => {
      const expected = { id: 1, code: 'DT001', category: 'MECHANICAL' }
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await downtimeReasonService.getById(1)

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/downtime/reasons/1')
      expect(result).toEqual(expected)
    })
  })

  describe('create', () => {
    it('should POST /api/v1/downtime/reasons with data', async () => {
      const data = { category: 'MECHANICAL', code: 'DT003', name: 'Belt Failure' }
      const expected = { id: 3, ...data }
      mockApi.post.mockResolvedValue({ data: expected })

      const result = await downtimeReasonService.create(data)

      expect(mockApi.post).toHaveBeenCalledWith('/api/v1/downtime/reasons', data)
      expect(result).toEqual(expected)
    })
  })

  describe('update', () => {
    it('should PATCH /api/v1/downtime/reasons/1 with data', async () => {
      const data = { name: 'Updated Belt Failure' }
      const expected = { id: 1, code: 'DT001', name: 'Updated Belt Failure' }
      mockApi.patch.mockResolvedValue({ data: expected })

      const result = await downtimeReasonService.update(1, data)

      expect(mockApi.patch).toHaveBeenCalledWith('/api/v1/downtime/reasons/1', data)
      expect(result).toEqual(expected)
    })
  })

  describe('delete', () => {
    it('should DELETE /api/v1/downtime/reasons/1', async () => {
      mockApi.delete.mockResolvedValue({ data: null })

      await downtimeReasonService.delete(1)

      expect(mockApi.delete).toHaveBeenCalledWith('/api/v1/downtime/reasons/1')
    })
  })
})

describe('downtimeService', () => {
  describe('getAll', () => {
    it('should GET /api/v1/downtime with params undefined when no filters', async () => {
      const expected = [{ id: 1, equipment_id: 1 }]
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await downtimeService.getAll()

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/downtime', {
        params: undefined,
      })
      expect(result).toEqual(expected)
    })

    it('should GET /api/v1/downtime with params when filters provided', async () => {
      const filters = { status: 'ACTIVE' as const, equipment_id: 1 }
      const expected = [{ id: 1, equipment_id: 1 }]
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await downtimeService.getAll(filters)

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/downtime', {
        params: filters,
      })
      expect(result).toEqual(expected)
    })
  })

  describe('getActive', () => {
    it('should GET /api/v1/downtime with ACTIVE status and return array', async () => {
      const expected = [{ id: 1, status: 'ACTIVE' }]
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await downtimeService.getActive()

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/downtime', {
        params: { status: 'ACTIVE', limit: 100 },
      })
      expect(result).toEqual(expected)
    })

    it('should return empty array when response data is not an array', async () => {
      mockApi.get.mockResolvedValue({ data: { some: 'object' } })

      const result = await downtimeService.getActive()

      expect(result).toEqual([])
    })
  })

  describe('getById', () => {
    it('should GET /api/v1/downtime/1', async () => {
      const expected = { id: 1, equipment_id: 1, status: 'ACTIVE' }
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await downtimeService.getById(1)

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/downtime/1')
      expect(result).toEqual(expected)
    })
  })

  describe('start', () => {
    it('should POST /api/v1/downtime with data', async () => {
      const data = { equipment_id: 1, reason_id: 2, remarks: 'Belt snapped' }
      const expected = { id: 1, ...data, status: 'ACTIVE' }
      mockApi.post.mockResolvedValue({ data: expected })

      const result = await downtimeService.start(data)

      expect(mockApi.post).toHaveBeenCalledWith('/api/v1/downtime', data)
      expect(result).toEqual(expected)
    })
  })

  describe('end', () => {
    it('should POST /api/v1/downtime/1/end with data', async () => {
      const data = { end_time: '2024-01-01T12:00:00Z', remarks: 'Repaired' }
      const expected = { id: 1, status: 'ENDED' }
      mockApi.post.mockResolvedValue({ data: expected })

      const result = await downtimeService.end(1, data)

      expect(mockApi.post).toHaveBeenCalledWith('/api/v1/downtime/1/end', data)
      expect(result).toEqual(expected)
    })
  })

  describe('update', () => {
    it('should PATCH /api/v1/downtime/1 with data', async () => {
      const data = { reason_id: 3, remarks: 'Updated reason' }
      const expected = { id: 1, ...data }
      mockApi.patch.mockResolvedValue({ data: expected })

      const result = await downtimeService.update(1, data)

      expect(mockApi.patch).toHaveBeenCalledWith('/api/v1/downtime/1', data)
      expect(result).toEqual(expected)
    })
  })

  describe('delete', () => {
    it('should DELETE /api/v1/downtime/1', async () => {
      mockApi.delete.mockResolvedValue({ data: null })

      await downtimeService.delete(1)

      expect(mockApi.delete).toHaveBeenCalledWith('/api/v1/downtime/1')
    })
  })

  describe('getSummary', () => {
    it('should transform backend by_category object to array format', async () => {
      const backendResponse = {
        by_category: {
          MECHANICAL: { count: 3, total_minutes: 120 },
          ELECTRICAL: { count: 1, total_minutes: 30 },
        },
        total_count: 4,
      }
      mockApi.get.mockResolvedValue({ data: backendResponse })

      const result = await downtimeService.getSummary()

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/downtime/summary', {
        params: undefined,
      })
      expect(result).toEqual([
        { category: 'MECHANICAL', count: 3, total_duration_sec: 7200 },
        { category: 'ELECTRICAL', count: 1, total_duration_sec: 1800 },
      ])
    })

    it('should return array as-is when backend returns plain array', async () => {
      const backendResponse = [
        { category: 'MECHANICAL', count: 3, total_duration_sec: 7200 },
      ]
      mockApi.get.mockResolvedValue({ data: backendResponse })

      const result = await downtimeService.getSummary()

      expect(result).toEqual(backendResponse)
    })

    it('should return empty array when backend returns object without by_category', async () => {
      mockApi.get.mockResolvedValue({ data: {} })

      const result = await downtimeService.getSummary()

      expect(result).toEqual([])
    })
  })
})
