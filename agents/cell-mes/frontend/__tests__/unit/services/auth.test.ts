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

import { authService } from '@/services/auth'

beforeEach(() => {
  vi.clearAllMocks()
})

describe('authService', () => {
  describe('login', () => {
    it('should POST /api/v1/auth/login with URLSearchParams body and form-urlencoded header', async () => {
      const expected = { access_token: 'token123', token_type: 'bearer' }
      mockApi.post.mockResolvedValue({ data: expected })

      const result = await authService.login('admin', 'pass')

      const call = mockApi.post.mock.calls[0]
      expect(call[0]).toBe('/api/v1/auth/login')
      expect(call[1]).toBeInstanceOf(URLSearchParams)
      expect(call[1].get('username')).toBe('admin')
      expect(call[1].get('password')).toBe('pass')
      expect(call[2]).toEqual({
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })
      expect(result).toEqual(expected)
    })
  })

  describe('register', () => {
    it('should POST /api/v1/auth/register with default OPERATOR role', async () => {
      const expected = { id: 1, username: 'user', role: 'OPERATOR' }
      mockApi.post.mockResolvedValue({ data: expected })

      const result = await authService.register('user', 'pass')

      expect(mockApi.post).toHaveBeenCalledWith('/api/v1/auth/register', {
        username: 'user',
        password: 'pass',
        role: 'OPERATOR',
      })
      expect(result).toEqual(expected)
    })

    it('should POST /api/v1/auth/register with specified role', async () => {
      const expected = { id: 1, username: 'user', role: 'ADMIN' }
      mockApi.post.mockResolvedValue({ data: expected })

      const result = await authService.register('user', 'pass', 'ADMIN')

      expect(mockApi.post).toHaveBeenCalledWith('/api/v1/auth/register', {
        username: 'user',
        password: 'pass',
        role: 'ADMIN',
      })
      expect(result).toEqual(expected)
    })
  })

  describe('getCurrentUser', () => {
    it('should GET /api/v1/auth/me', async () => {
      const expected = { id: 1, username: 'admin', role: 'ADMIN' }
      mockApi.get.mockResolvedValue({ data: expected })

      const result = await authService.getCurrentUser()

      expect(mockApi.get).toHaveBeenCalledWith('/api/v1/auth/me')
      expect(result).toEqual(expected)
    })
  })
})
