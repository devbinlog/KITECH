import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useWebSocket } from '@/hooks/useWebSocket'

// Mock WebSocket
class MockWebSocket {
  static OPEN = 1
  static CONNECTING = 0
  static CLOSING = 2
  static CLOSED = 3

  readyState: number = MockWebSocket.CONNECTING
  url: string
  onopen: ((event: Event) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  sentMessages: string[] = []

  constructor(url: string) {
    this.url = url
    instances.push(this)
  }

  send(data: string) {
    this.sentMessages.push(data)
  }

  close() {
    this.readyState = MockWebSocket.CLOSED
    this.onclose?.({} as CloseEvent)
  }

  // Test helpers to simulate events
  simulateOpen() {
    this.readyState = MockWebSocket.OPEN
    this.onopen?.({} as Event)
  }

  simulateMessage(data: unknown) {
    this.onmessage?.(new MessageEvent('message', { data: JSON.stringify(data) }))
  }

  simulateError() {
    this.onerror?.({} as Event)
  }

  simulateClose() {
    this.readyState = MockWebSocket.CLOSED
    this.onclose?.({} as CloseEvent)
  }
}

let instances: MockWebSocket[] = []

beforeEach(() => {
  instances = []
  vi.stubGlobal('WebSocket', MockWebSocket)
  vi.useFakeTimers()
  // Clear localStorage
  localStorage.clear()
})

afterEach(() => {
  vi.useRealTimers()
  vi.restoreAllMocks()
})

describe('useWebSocket', () => {
  describe('initial state', () => {
    it('starts disconnected with no last message', () => {
      const { result } = renderHook(() => useWebSocket())

      expect(result.current.isConnected).toBe(false)
      expect(result.current.connectionStatus).toBe('disconnected')
      expect(result.current.lastMessage).toBeNull()
    })

    it('does not auto-connect when autoConnect is false (default)', () => {
      renderHook(() => useWebSocket({ url: 'ws://test' }))
      expect(instances).toHaveLength(0)
    })
  })

  describe('autoConnect', () => {
    it('connects automatically when autoConnect is true', () => {
      renderHook(() => useWebSocket({ url: 'ws://test', autoConnect: true }))
      expect(instances).toHaveLength(1)
    })

    it('sets connectionStatus to connecting when autoConnect triggers', () => {
      const { result } = renderHook(() =>
        useWebSocket({ url: 'ws://test', autoConnect: true })
      )
      expect(result.current.connectionStatus).toBe('connecting')
    })
  })

  describe('manual connect', () => {
    it('creates WebSocket when connect() is called', () => {
      const { result } = renderHook(() => useWebSocket({ url: 'ws://test' }))

      act(() => {
        result.current.connect()
      })

      expect(instances).toHaveLength(1)
      expect(instances[0].url).toBe('ws://test')
    })

    it('appends token to url when token is in localStorage', () => {
      localStorage.setItem('token', 'my-token')
      const { result } = renderHook(() => useWebSocket({ url: 'ws://test' }))

      act(() => {
        result.current.connect()
      })

      expect(instances[0].url).toBe('ws://test?token=my-token')
    })

    it('does not create second WebSocket when already connected', () => {
      const { result } = renderHook(() => useWebSocket({ url: 'ws://test' }))

      act(() => {
        result.current.connect()
      })
      act(() => {
        instances[0].simulateOpen()
      })
      act(() => {
        result.current.connect() // second call - should be no-op
      })

      expect(instances).toHaveLength(1)
    })

    it('sets isConnected and connectionStatus on open', () => {
      const { result } = renderHook(() => useWebSocket({ url: 'ws://test' }))

      act(() => {
        result.current.connect()
      })
      act(() => {
        instances[0].simulateOpen()
      })

      expect(result.current.isConnected).toBe(true)
      expect(result.current.connectionStatus).toBe('connected')
    })

    it('calls onConnect callback when connection opens', () => {
      const onConnect = vi.fn()
      const { result } = renderHook(() =>
        useWebSocket({ url: 'ws://test', onConnect })
      )

      act(() => {
        result.current.connect()
      })
      act(() => {
        instances[0].simulateOpen()
      })

      expect(onConnect).toHaveBeenCalledOnce()
    })
  })

  describe('disconnect', () => {
    it('sets isConnected false and status disconnected after disconnect()', () => {
      const { result } = renderHook(() => useWebSocket({ url: 'ws://test' }))

      act(() => {
        result.current.connect()
      })
      act(() => {
        instances[0].simulateOpen()
      })
      act(() => {
        result.current.disconnect()
      })

      expect(result.current.isConnected).toBe(false)
      expect(result.current.connectionStatus).toBe('disconnected')
    })

    it('calls onDisconnect callback when connection closes naturally', () => {
      const onDisconnect = vi.fn()
      const { result } = renderHook(() =>
        useWebSocket({ url: 'ws://test', onDisconnect, reconnect: false })
      )

      act(() => {
        result.current.connect()
      })
      act(() => {
        instances[0].simulateOpen()
      })
      act(() => {
        instances[0].simulateClose()
      })

      expect(onDisconnect).toHaveBeenCalledOnce()
    })
  })

  describe('reconnection', () => {
    it('attempts reconnect after close when reconnect is true', () => {
      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://test',
          reconnect: true,
          reconnectInterval: 1000,
          maxReconnectAttempts: 3,
        })
      )

      act(() => {
        result.current.connect()
      })
      act(() => {
        instances[0].simulateOpen()
      })
      act(() => {
        instances[0].simulateClose()
      })

      // No new connection yet - still waiting for timer
      expect(instances).toHaveLength(1)

      act(() => {
        vi.advanceTimersByTime(1000)
      })

      expect(instances).toHaveLength(2)
    })

    it('does not reconnect when reconnect is false', () => {
      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://test',
          reconnect: false,
        })
      )

      act(() => {
        result.current.connect()
      })
      act(() => {
        instances[0].simulateOpen()
      })
      act(() => {
        instances[0].simulateClose()
      })

      act(() => {
        vi.advanceTimersByTime(5000)
      })

      expect(instances).toHaveLength(1)
    })

    it('stops reconnecting after maxReconnectAttempts', () => {
      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://test',
          reconnect: true,
          reconnectInterval: 100,
          maxReconnectAttempts: 2,
        })
      )

      act(() => {
        result.current.connect()
      })
      act(() => {
        instances[0].simulateClose()
      })

      // Attempt 1
      act(() => { vi.advanceTimersByTime(100) })
      act(() => { instances[1]?.simulateClose() })

      // Attempt 2
      act(() => { vi.advanceTimersByTime(100) })
      act(() => { instances[2]?.simulateClose() })

      // Should not attempt a 3rd reconnect
      act(() => { vi.advanceTimersByTime(1000) })

      // 1 original + up to 2 reconnects
      expect(instances.length).toBeLessThanOrEqual(3)
    })

    it('does not reconnect after explicit disconnect()', () => {
      const { result } = renderHook(() =>
        useWebSocket({
          url: 'ws://test',
          reconnect: true,
          reconnectInterval: 100,
          maxReconnectAttempts: 5,
        })
      )

      act(() => {
        result.current.connect()
      })
      act(() => {
        instances[0].simulateOpen()
      })
      act(() => {
        result.current.disconnect()
      })

      act(() => { vi.advanceTimersByTime(500) })

      // Still only 1 WebSocket - no reconnect after explicit disconnect
      expect(instances).toHaveLength(1)
    })
  })

  describe('message handling', () => {
    it('sets lastMessage on incoming message', () => {
      const { result } = renderHook(() => useWebSocket({ url: 'ws://test' }))

      act(() => {
        result.current.connect()
      })
      act(() => {
        instances[0].simulateOpen()
      })
      act(() => {
        instances[0].simulateMessage({ type: 'update', data: { value: 42 } })
      })

      expect(result.current.lastMessage).toEqual({ type: 'update', data: { value: 42 } })
    })

    it('calls onMessage callback with parsed message', () => {
      const onMessage = vi.fn()
      const { result } = renderHook(() =>
        useWebSocket({ url: 'ws://test', onMessage })
      )

      act(() => {
        result.current.connect()
      })
      act(() => {
        instances[0].simulateOpen()
      })
      act(() => {
        instances[0].simulateMessage({ type: 'kpi_updates', data: 99 })
      })

      expect(onMessage).toHaveBeenCalledWith({ type: 'kpi_updates', data: 99 })
    })

    it('does not throw when receiving invalid JSON', () => {
      const { result } = renderHook(() => useWebSocket({ url: 'ws://test' }))

      act(() => {
        result.current.connect()
      })
      act(() => {
        instances[0].simulateOpen()
      })

      expect(() => {
        act(() => {
          // Simulate malformed JSON directly
          instances[0].onmessage?.(new MessageEvent('message', { data: 'not-json' }))
        })
      }).not.toThrow()

      // lastMessage should remain null
      expect(result.current.lastMessage).toBeNull()
    })
  })

  describe('send operations', () => {
    it('sends JSON message when connected', () => {
      const { result } = renderHook(() => useWebSocket({ url: 'ws://test' }))

      act(() => {
        result.current.connect()
      })
      act(() => {
        instances[0].simulateOpen()
      })
      act(() => {
        result.current.send({ action: 'ping' })
      })

      expect(instances[0].sentMessages).toHaveLength(1)
      expect(JSON.parse(instances[0].sentMessages[0])).toEqual({ action: 'ping' })
    })

    it('does not send when disconnected', () => {
      const { result } = renderHook(() => useWebSocket({ url: 'ws://test' }))

      act(() => {
        result.current.send({ action: 'ping' })
      })

      expect(instances).toHaveLength(0)
    })

    it('subscribe sends correct subscribe message', () => {
      const { result } = renderHook(() => useWebSocket({ url: 'ws://test' }))

      act(() => {
        result.current.connect()
      })
      act(() => {
        instances[0].simulateOpen()
      })
      act(() => {
        result.current.subscribe('equipment_status', { equipment_id: 1 })
      })

      const msg = JSON.parse(instances[0].sentMessages[0])
      expect(msg).toEqual({
        action: 'subscribe',
        channel: 'equipment_status',
        filters: { equipment_id: 1 },
      })
    })

    it('subscribe sends empty filters when none provided', () => {
      const { result } = renderHook(() => useWebSocket({ url: 'ws://test' }))

      act(() => {
        result.current.connect()
      })
      act(() => {
        instances[0].simulateOpen()
      })
      act(() => {
        result.current.subscribe('kpi_updates')
      })

      const msg = JSON.parse(instances[0].sentMessages[0])
      expect(msg.filters).toEqual({})
    })

    it('unsubscribe sends correct unsubscribe message', () => {
      const { result } = renderHook(() => useWebSocket({ url: 'ws://test' }))

      act(() => {
        result.current.connect()
      })
      act(() => {
        instances[0].simulateOpen()
      })
      act(() => {
        result.current.unsubscribe('alerts')
      })

      const msg = JSON.parse(instances[0].sentMessages[0])
      expect(msg).toEqual({ action: 'unsubscribe', channel: 'alerts' })
    })

    it('sendQuery sends query action', () => {
      const { result } = renderHook(() => useWebSocket({ url: 'ws://test' }))

      act(() => {
        result.current.connect()
      })
      act(() => {
        instances[0].simulateOpen()
      })
      act(() => {
        result.current.sendQuery('show me recent alarms')
      })

      const msg = JSON.parse(instances[0].sentMessages[0])
      expect(msg).toEqual({ action: 'query', query: 'show me recent alarms' })
    })
  })

  describe('error handling', () => {
    it('sets connectionStatus to error on WebSocket error', () => {
      const { result } = renderHook(() => useWebSocket({ url: 'ws://test' }))

      act(() => {
        result.current.connect()
      })
      act(() => {
        instances[0].simulateError()
      })

      expect(result.current.connectionStatus).toBe('error')
    })

    it('calls onError callback on WebSocket error', () => {
      const onError = vi.fn()
      const { result } = renderHook(() =>
        useWebSocket({ url: 'ws://test', onError })
      )

      act(() => {
        result.current.connect()
      })
      act(() => {
        instances[0].simulateError()
      })

      expect(onError).toHaveBeenCalledOnce()
    })
  })

  describe('cleanup on unmount', () => {
    it('closes WebSocket on unmount', () => {
      const { result, unmount } = renderHook(() =>
        useWebSocket({ url: 'ws://test', autoConnect: true })
      )

      act(() => {
        instances[0].simulateOpen()
      })

      unmount()

      expect(instances[0].readyState).toBe(MockWebSocket.CLOSED)
    })
  })
})
