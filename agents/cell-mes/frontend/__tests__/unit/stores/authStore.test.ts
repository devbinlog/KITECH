import { describe, it, expect, beforeEach } from 'vitest'
import { useAuthStore } from '@/stores/authStore'

describe('authStore', () => {
  beforeEach(() => {
    // Clear localStorage first (removes both "token" and persist storage "auth-storage")
    localStorage.clear()
    // Reset Zustand store state to defaults
    useAuthStore.setState({ user: null, isAuthenticated: false })
  })

  it('starts with unauthenticated state', () => {
    const state = useAuthStore.getState()
    expect(state.isAuthenticated).toBe(false)
    expect(state.user).toBeNull()
  })

  it('setAuth stores token in localStorage and sets user + isAuthenticated', () => {
    const user = { id: 1, username: 'admin', role: 'admin' }
    useAuthStore.getState().setAuth('test-token', user)

    const state = useAuthStore.getState()
    expect(state.isAuthenticated).toBe(true)
    expect(state.user).toEqual(user)
    expect(localStorage.getItem('token')).toBe('test-token')
  })

  it('logout clears token from localStorage and resets state', () => {
    const user = { id: 1, username: 'admin', role: 'admin' }
    useAuthStore.getState().setAuth('test-token', user)

    // Verify setup
    expect(useAuthStore.getState().isAuthenticated).toBe(true)

    useAuthStore.getState().logout()

    const state = useAuthStore.getState()
    expect(state.isAuthenticated).toBe(false)
    expect(state.user).toBeNull()
    expect(localStorage.getItem('token')).toBeNull()
  })

  it('checkAuth returns true when both token and user exist', () => {
    localStorage.setItem('token', 'test-token')
    useAuthStore.setState({ user: { id: 1, username: 'admin', role: 'admin' } })

    const result = useAuthStore.getState().checkAuth()

    expect(result).toBe(true)
    expect(useAuthStore.getState().isAuthenticated).toBe(true)
  })

  it('checkAuth returns false when no token in localStorage', () => {
    useAuthStore.setState({
      user: { id: 1, username: 'admin', role: 'admin' },
      isAuthenticated: true,
    })

    const result = useAuthStore.getState().checkAuth()

    expect(result).toBe(false)
    expect(useAuthStore.getState().isAuthenticated).toBe(false)
    // checkAuth also clears user when missing token
    expect(useAuthStore.getState().user).toBeNull()
  })

  it('checkAuth returns false when no user in state', () => {
    localStorage.setItem('token', 'test-token')
    useAuthStore.setState({ user: null, isAuthenticated: true })

    const result = useAuthStore.getState().checkAuth()

    expect(result).toBe(false)
    expect(useAuthStore.getState().isAuthenticated).toBe(false)
    // checkAuth also removes orphaned token
    expect(localStorage.getItem('token')).toBeNull()
  })

  it('checkAuth restores isAuthenticated when token and user exist but flag is false', () => {
    localStorage.setItem('token', 'test-token')
    useAuthStore.setState({
      user: { id: 2, username: 'operator', role: 'operator' },
      isAuthenticated: false,
    })

    const result = useAuthStore.getState().checkAuth()

    expect(result).toBe(true)
    expect(useAuthStore.getState().isAuthenticated).toBe(true)
  })

  it('checkAuth is idempotent when already authenticated', () => {
    localStorage.setItem('token', 'test-token')
    useAuthStore.setState({
      user: { id: 1, username: 'admin', role: 'admin' },
      isAuthenticated: true,
    })

    // Call twice - should not change anything
    useAuthStore.getState().checkAuth()
    const result = useAuthStore.getState().checkAuth()

    expect(result).toBe(true)
    expect(useAuthStore.getState().isAuthenticated).toBe(true)
  })

  it('setAuth overwrites previous authentication', () => {
    const user1 = { id: 1, username: 'admin', role: 'admin' }
    const user2 = { id: 2, username: 'operator', role: 'operator' }

    useAuthStore.getState().setAuth('token-1', user1)
    useAuthStore.getState().setAuth('token-2', user2)

    const state = useAuthStore.getState()
    expect(state.user).toEqual(user2)
    expect(state.isAuthenticated).toBe(true)
    expect(localStorage.getItem('token')).toBe('token-2')
  })
})
