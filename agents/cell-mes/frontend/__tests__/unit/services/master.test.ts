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

import {
  stdProcessService,
  productService,
  routingService,
  scenarioService,
} from '@/services/master'

beforeEach(() => {
  vi.clearAllMocks()
})

describe('stdProcessService', () => {
  describe('getAll', () => {
    it('should GET /api/v1/masters/std-processes', async () => {
      const expected = [{ id: 1, name: 'Turning' }]
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await stdProcessService.getAll()

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/masters/std-processes')
      expect(result).toEqual(expected)
    })
  })

  describe('getById', () => {
    it('should GET /api/v1/masters/std-processes/1', async () => {
      const expected = { id: 1, name: 'Turning' }
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await stdProcessService.getById(1)

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/masters/std-processes/1')
      expect(result).toEqual(expected)
    })
  })

  describe('create', () => {
    it('should POST /api/v1/masters/std-processes with data', async () => {
      const data = { name: 'Milling', code: 'MILL' }
      const expected = { id: 2, ...data }
      mockApi.post.mockResolvedValue({ data: expected })

      const result = await stdProcessService.create(data)

      expect(mockApi.post).toHaveBeenCalledWith('/api/v1/masters/std-processes', data)
      expect(result).toEqual(expected)
    })
  })

  describe('update', () => {
    it('should PATCH /api/v1/masters/std-processes/1 with data', async () => {
      const data = { name: 'Updated Turning' }
      const expected = { id: 1, ...data }
      mockApi.patch.mockResolvedValue({ data: expected })

      const result = await stdProcessService.update(1, data)

      expect(mockApi.patch).toHaveBeenCalledWith('/api/v1/masters/std-processes/1', data)
      expect(result).toEqual(expected)
    })
  })

  describe('delete', () => {
    it('should DELETE /api/v1/masters/std-processes/1', async () => {
      mockApi.delete.mockResolvedValue({ data: null })

      await stdProcessService.delete(1)

      expect(mockApi.delete).toHaveBeenCalledWith('/api/v1/masters/std-processes/1')
    })
  })
})

describe('productService', () => {
  describe('getAll', () => {
    it('should GET /api/v1/masters/products with include_deleted false by default', async () => {
      const expected = [{ id: 1, name: 'Widget A' }]
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await productService.getAll()

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/masters/products', {
        params: { include_deleted: false },
      })
      expect(result).toEqual(expected)
    })

    it('should GET with include_deleted true when passed true', async () => {
      const expected = [{ id: 1, name: 'Widget A' }, { id: 2, name: 'Deleted Widget' }]
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await productService.getAll(true)

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/masters/products', {
        params: { include_deleted: true },
      })
      expect(result).toEqual(expected)
    })
  })

  describe('getById', () => {
    it('should GET /api/v1/masters/products/1', async () => {
      const expected = { id: 1, name: 'Widget A' }
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await productService.getById(1)

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/masters/products/1')
      expect(result).toEqual(expected)
    })
  })

  describe('create', () => {
    it('should POST /api/v1/masters/products with data', async () => {
      const data = { name: 'Widget B', code: 'WB' }
      const expected = { id: 2, ...data }
      mockApi.post.mockResolvedValue({ data: expected })

      const result = await productService.create(data)

      expect(mockApi.post).toHaveBeenCalledWith('/api/v1/masters/products', data)
      expect(result).toEqual(expected)
    })
  })

  describe('update', () => {
    it('should PATCH /api/v1/masters/products/1 with data', async () => {
      const data = { name: 'Updated Widget' }
      const expected = { id: 1, ...data }
      mockApi.patch.mockResolvedValue({ data: expected })

      const result = await productService.update(1, data)

      expect(mockApi.patch).toHaveBeenCalledWith('/api/v1/masters/products/1', data)
      expect(result).toEqual(expected)
    })
  })

  describe('delete', () => {
    it('should DELETE /api/v1/masters/products/1', async () => {
      mockApi.delete.mockResolvedValue({ data: null })

      await productService.delete(1)

      expect(mockApi.delete).toHaveBeenCalledWith('/api/v1/masters/products/1')
    })
  })
})

describe('routingService', () => {
  describe('getByProduct', () => {
    it('should GET /api/v1/masters/products/1/routings', async () => {
      const expected = [{ id: 1, product_id: 1, sequence: 1 }]
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await routingService.getByProduct(1)

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/masters/products/1/routings')
      expect(result).toEqual(expected)
    })
  })

  describe('save', () => {
    it('should PUT /api/v1/masters/products/1/routings with routings array', async () => {
      const routings = [
        { sequence: 1, std_process_id: 1, equipment_id: 1 },
        { sequence: 2, std_process_id: 2, equipment_id: 2 },
      ]
      const expected = routings
      mockApi.put.mockResolvedValue({ data: expected })

      const result = await routingService.save(1, routings)

      expect(mockApi.put).toHaveBeenCalledWith('/api/v1/masters/products/1/routings', routings)
      expect(result).toEqual(expected)
    })
  })
})

describe('scenarioService', () => {
  describe('getAll', () => {
    it('should GET /api/v1/masters/scenarios with default params', async () => {
      const expected = [{ id: 1, name: 'Scenario A' }]
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await scenarioService.getAll()

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/masters/scenarios', {
        params: { product_id: undefined, active_only: true },
      })
      expect(result).toEqual(expected)
    })

    it('should GET with custom params when provided', async () => {
      const expected = [{ id: 1, name: 'Scenario A' }, { id: 2, name: 'Inactive Scenario' }]
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await scenarioService.getAll(1, false)

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/masters/scenarios', {
        params: { product_id: 1, active_only: false },
      })
      expect(result).toEqual(expected)
    })
  })

  describe('getById', () => {
    it('should GET /api/v1/masters/scenarios/1', async () => {
      const expected = { id: 1, name: 'Scenario A' }
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await scenarioService.getById(1)

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/masters/scenarios/1')
      expect(result).toEqual(expected)
    })
  })

  describe('create', () => {
    it('should POST /api/v1/masters/scenarios with data', async () => {
      const data = { name: 'Scenario B', file_path: '/scenarios/b.json', product_id: 1 }
      const expected = { id: 2, ...data }
      mockApi.post.mockResolvedValue({ data: expected })

      const result = await scenarioService.create(data)

      expect(mockApi.post).toHaveBeenCalledWith('/api/v1/masters/scenarios', data)
      expect(result).toEqual(expected)
    })
  })

  describe('update', () => {
    it('should PATCH /api/v1/masters/scenarios/1 with data', async () => {
      const data = { name: 'Updated Scenario' }
      const expected = { id: 1, ...data }
      mockApi.patch.mockResolvedValue({ data: expected })

      const result = await scenarioService.update(1, data)

      expect(mockApi.patch).toHaveBeenCalledWith('/api/v1/masters/scenarios/1', data)
      expect(result).toEqual(expected)
    })
  })

  describe('toggleActive', () => {
    it('should PATCH /api/v1/masters/scenarios/1/active with null body and is_active param', async () => {
      const expected = { id: 1, is_active: true }
      mockApi.patch.mockResolvedValue({ data: expected })

      const result = await scenarioService.toggleActive(1, true)

      expect(mockApi.patch).toHaveBeenCalledWith('/api/v1/masters/scenarios/1/active', null, {
        params: { is_active: true },
      })
      expect(result).toEqual(expected)
    })
  })

  describe('delete', () => {
    it('should DELETE /api/v1/masters/scenarios/1', async () => {
      mockApi.delete.mockResolvedValue({ data: null })

      await scenarioService.delete(1)

      expect(mockApi.delete).toHaveBeenCalledWith('/api/v1/masters/scenarios/1')
    })
  })

  describe('getContent', () => {
    it('should GET /api/v1/masters/scenarios/1/content', async () => {
      const expected = { id: 1, content: { work_orders: [] } }
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await scenarioService.getContent(1)

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/masters/scenarios/1/content')
      expect(result).toEqual(expected)
    })
  })
})
