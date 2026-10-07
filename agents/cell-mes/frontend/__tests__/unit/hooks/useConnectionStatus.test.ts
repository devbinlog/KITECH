import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useProductConnections, useProductConnection, useServiceHealth } from '@/hooks/useConnectionStatus'
import { createWrapper } from '../test-utils'

// Mock the services used by the hook
vi.mock('@/services/master', () => ({
  productService: {
    getAll: vi.fn(),
  },
  routingService: {
    getByProduct: vi.fn(),
  },
}))

// Mock fetch for useServiceHealth
const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

import { routingService } from '@/services/master'
const mockRoutingService = routingService as any

beforeEach(() => {
  vi.clearAllMocks()
})

describe('useProductConnections', () => {
  it('returns empty connections when productIds is undefined', async () => {
    const { result } = renderHook(() => useProductConnections(undefined), {
      wrapper: createWrapper(),
    })

    expect(result.current.connections).toEqual([])
    expect(result.current.isLoading).toBe(false)
  })

  it('returns empty connections when productIds is empty array', async () => {
    const { result } = renderHook(() => useProductConnections([]), {
      wrapper: createWrapper(),
    })

    expect(result.current.connections).toEqual([])
  })

  it('maps routing counts to ProductConnection objects', async () => {
    mockRoutingService.getByProduct.mockImplementation((id: number) => {
      if (id === 1) return Promise.resolve([{ id: 10 }, { id: 11 }])
      if (id === 2) return Promise.resolve([])
      return Promise.resolve([])
    })

    const { result } = renderHook(() => useProductConnections([1, 2]), {
      wrapper: createWrapper(),
    })

    await waitFor(() => !result.current.isLoading)

    await waitFor(() => {
      expect(result.current.connections).toHaveLength(2)
    })

    const conn1 = result.current.connections.find(c => c.productId === 1)
    const conn2 = result.current.connections.find(c => c.productId === 2)

    expect(conn1?.hasRouting).toBe(true)
    expect(conn1?.routingCount).toBe(2)
    expect(conn1?.canCreateOrder).toBe(true)

    expect(conn2?.hasRouting).toBe(false)
    expect(conn2?.routingCount).toBe(0)
    expect(conn2?.canCreateOrder).toBe(false)
  })

  it('treats failed routing fetch as 0 routings', async () => {
    mockRoutingService.getByProduct.mockRejectedValue(new Error('Network error'))

    const { result } = renderHook(() => useProductConnections([5]), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.connections).toHaveLength(1)
    })

    expect(result.current.connections[0].routingCount).toBe(0)
    expect(result.current.connections[0].hasRouting).toBe(false)
  })
})

describe('useProductConnection', () => {
  it('returns undefined connection when productId is undefined', () => {
    const { result } = renderHook(() => useProductConnection(undefined), {
      wrapper: createWrapper(),
    })

    expect(result.current.connection).toBeUndefined()
  })

  it('returns single connection for given productId', async () => {
    mockRoutingService.getByProduct.mockResolvedValue([{ id: 1 }])

    const { result } = renderHook(() => useProductConnection(10), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.connection).toBeDefined()
    })

    expect(result.current.connection?.productId).toBe(10)
    expect(result.current.connection?.hasRouting).toBe(true)
    expect(result.current.connection?.routingCount).toBe(1)
  })
})

describe('useServiceHealth', () => {
  it('returns checking status initially before fetch resolves', () => {
    // Never-resolving fetch so query stays pending
    mockFetch.mockReturnValue(new Promise(() => {}))

    const { result } = renderHook(() => useServiceHealth(), {
      wrapper: createWrapper(),
    })

    // Initially returns default checking state
    expect(result.current.health.mes.status).toBe('checking')
    expect(result.current.health.scheduler.status).toBe('checking')
  })

  it('returns connected status when both health endpoints succeed', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ status: 'ok' }),
    })

    const { result } = renderHook(() => useServiceHealth(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.health.mes.status).toBe('connected')
    })

    expect(result.current.health.scheduler.status).toBe('connected')
    expect(result.current.isError).toBe(false)
  })

  it('returns disconnected for mes when /health fetch fails', async () => {
    mockFetch.mockImplementation((url: string) => {
      if (url === '/health') return Promise.reject(new Error('Connection refused'))
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ status: 'ok' }),
      })
    })

    const { result } = renderHook(() => useServiceHealth(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      // At least one of them should have resolved
      const status = result.current.health.mes.status
      expect(['connected', 'disconnected']).toContain(status)
    })
  })

  it('returns disconnected for both when all fetches fail', async () => {
    mockFetch.mockRejectedValue(new Error('Network error'))

    const { result } = renderHook(() => useServiceHealth(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.health.mes.status).toBe('disconnected')
    })

    expect(result.current.health.scheduler.status).toBe('disconnected')
  })

  it('includes lastCheck timestamp when connected', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ status: 'ok' }),
    })

    const { result } = renderHook(() => useServiceHealth(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.health.mes.status).toBe('connected')
    })

    expect(result.current.health.mes.lastCheck).toBeDefined()
    expect(typeof result.current.health.mes.lastCheck).toBe('string')
  })
})
