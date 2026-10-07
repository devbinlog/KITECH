import { describe, it, expect, beforeEach } from 'vitest'
import { useChatStore } from '@/stores/chatStore'

describe('chatStore', () => {
  beforeEach(() => {
    localStorage.clear()
    useChatStore.setState({ messages: [], isLoading: false, favorites: [] })
  })

  describe('initial state', () => {
    it('has empty messages array', () => {
      const state = useChatStore.getState()
      expect(state.messages).toEqual([])
    })

    it('has isLoading set to false', () => {
      const state = useChatStore.getState()
      expect(state.isLoading).toBe(false)
    })

    it('has empty favorites array', () => {
      const state = useChatStore.getState()
      expect(state.favorites).toEqual([])
    })
  })

  describe('addMessage', () => {
    it('appends a message to the messages array', () => {
      useChatStore.getState().addMessage({
        role: 'user',
        content: 'hello',
        timestamp: '2024-01-01T00:00:00Z',
      })
      const state = useChatStore.getState()
      expect(state.messages).toHaveLength(1)
      expect(state.messages[0]).toEqual({
        role: 'user',
        content: 'hello',
        timestamp: '2024-01-01T00:00:00Z',
      })
    })

    it('appends multiple messages in order', () => {
      useChatStore.getState().addMessage({
        role: 'user',
        content: 'hello',
        timestamp: '2024-01-01T00:00:00Z',
      })
      useChatStore.getState().addMessage({
        role: 'assistant',
        content: 'hi there',
        timestamp: '2024-01-01T00:00:01Z',
      })
      const state = useChatStore.getState()
      expect(state.messages).toHaveLength(2)
      expect(state.messages[0].role).toBe('user')
      expect(state.messages[1].role).toBe('assistant')
    })
  })

  describe('clearMessages', () => {
    it('resets messages to empty array', () => {
      useChatStore.getState().addMessage({
        role: 'user',
        content: 'hello',
        timestamp: '2024-01-01T00:00:00Z',
      })
      useChatStore.getState().clearMessages()
      expect(useChatStore.getState().messages).toEqual([])
    })
  })

  describe('setLoading', () => {
    it('sets isLoading to true', () => {
      useChatStore.getState().setLoading(true)
      expect(useChatStore.getState().isLoading).toBe(true)
    })

    it('sets isLoading to false', () => {
      useChatStore.getState().setLoading(true)
      useChatStore.getState().setLoading(false)
      expect(useChatStore.getState().isLoading).toBe(false)
    })
  })

  describe('favorites', () => {
    it('addFavorite adds a query to favorites', () => {
      useChatStore.getState().addFavorite('query1')
      expect(useChatStore.getState().favorites).toEqual(['query1'])
    })

    it('addFavorite is idempotent - does not duplicate', () => {
      useChatStore.getState().addFavorite('query1')
      useChatStore.getState().addFavorite('query1')
      expect(useChatStore.getState().favorites).toEqual(['query1'])
    })

    it('removeFavorite removes a query from favorites', () => {
      useChatStore.getState().addFavorite('query1')
      useChatStore.getState().removeFavorite('query1')
      expect(useChatStore.getState().favorites).toEqual([])
    })

    it('removeFavorite with non-existent query does not error', () => {
      useChatStore.getState().addFavorite('query1')
      useChatStore.getState().removeFavorite('nonexistent')
      expect(useChatStore.getState().favorites).toEqual(['query1'])
    })

    it('isFavorite returns true when query is present', () => {
      useChatStore.getState().addFavorite('query1')
      expect(useChatStore.getState().isFavorite('query1')).toBe(true)
    })

    it('isFavorite returns false when query is not present', () => {
      expect(useChatStore.getState().isFavorite('query1')).toBe(false)
    })
  })
})
