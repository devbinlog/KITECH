import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockInstance } = vi.hoisted(() => {
  const mockInstance = {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  }
  return { mockInstance }
})

vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => mockInstance),
  },
}))

import { NlmService } from '@/services/nlm'

beforeEach(() => {
  vi.clearAllMocks()
})

describe('NlmService', () => {
  describe('query', () => {
    it('should POST /nlm/query with query string', async () => {
      const expected = { answer: 'Production is good', sql: 'SELECT ...', data: [] }
      mockInstance.post.mockResolvedValue({ data: expected })

      const result = await NlmService.query('hello')

      expect(mockInstance.post).toHaveBeenCalledWith('/nlm/query', { query: 'hello' })
      expect(result).toEqual(expected)
    })
  })

  describe('getHistory', () => {
    it('should GET /nlm/history with default limit 50 and return messages', async () => {
      const messages = [{ role: 'user', content: 'hello' }]
      mockInstance.get.mockResolvedValue({ data: { messages } })

      const result = await NlmService.getHistory()

      expect(mockInstance.get).toHaveBeenCalledWith('/nlm/history', {
        params: { limit: 50 },
      })
      expect(result).toEqual(messages)
    })

    it('should GET /nlm/history with custom limit', async () => {
      const messages = [{ role: 'user', content: 'test' }]
      mockInstance.get.mockResolvedValue({ data: { messages } })

      const result = await NlmService.getHistory(10)

      expect(mockInstance.get).toHaveBeenCalledWith('/nlm/history', {
        params: { limit: 10 },
      })
      expect(result).toEqual(messages)
    })
  })

  describe('addFavorite', () => {
    it('should POST /nlm/favorites with query', async () => {
      mockInstance.post.mockResolvedValue({ data: null })

      await NlmService.addFavorite('query1')

      expect(mockInstance.post).toHaveBeenCalledWith('/nlm/favorites', { query: 'query1' })
    })
  })

  describe('removeFavorite', () => {
    it('should DELETE /nlm/favorites with query in data', async () => {
      mockInstance.delete.mockResolvedValue({ data: null })

      await NlmService.removeFavorite('query1')

      expect(mockInstance.delete).toHaveBeenCalledWith('/nlm/favorites', {
        data: { query: 'query1' },
      })
    })
  })

  describe('getFavorites', () => {
    it('should GET /nlm/favorites and return favorites array', async () => {
      const favorites = ['query1', 'query2']
      mockInstance.get.mockResolvedValue({ data: { favorites } })

      const result = await NlmService.getFavorites()

      expect(mockInstance.get).toHaveBeenCalledWith('/nlm/favorites')
      expect(result).toEqual(favorites)
    })
  })

  describe('getQuotaStatus', () => {
    it('should GET /nlm/quota', async () => {
      const expected = {
        requests: { used: 10, limit: 100, reset_at: '2024-01-02T00:00:00Z' },
        llm_calls: { used: 5, limit: 50, reset_at: '2024-01-02T00:00:00Z' },
      }
      mockInstance.get.mockResolvedValue({ data: expected })

      const result = await NlmService.getQuotaStatus()

      expect(mockInstance.get).toHaveBeenCalledWith('/nlm/quota')
      expect(result).toEqual(expected)
    })
  })

  describe('getDailySummary', () => {
    it('should call query with Korean summary request string', async () => {
      const expected = { answer: 'Today summary', sql: '', data: [] }
      mockInstance.post.mockResolvedValue({ data: expected })

      const result = await NlmService.getDailySummary()

      expect(mockInstance.post).toHaveBeenCalledWith('/nlm/query', {
        query: '오늘 생산 현황 요약해줘',
      })
      expect(result).toEqual(expected)
    })
  })
})
