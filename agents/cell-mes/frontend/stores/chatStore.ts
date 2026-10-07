/**
 * Chat Store
 * Zustand store for managing chat state
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Message } from '@/types/nlm';

interface ChatState {
  // Messages
  messages: Message[];
  isLoading: boolean;

  // Favorites
  favorites: string[];

  // Actions
  addMessage: (message: Message) => void;
  clearMessages: () => void;
  setLoading: (loading: boolean) => void;

  // Favorites actions
  addFavorite: (query: string) => void;
  removeFavorite: (query: string) => void;
  isFavorite: (query: string) => boolean;
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      // Initial state
      messages: [],
      isLoading: false,
      favorites: [],

      // Message actions
      addMessage: (message) =>
        set((state) => ({
          messages: [...state.messages, message],
        })),

      clearMessages: () =>
        set({ messages: [] }),

      setLoading: (loading) =>
        set({ isLoading: loading }),

      // Favorites actions
      addFavorite: (query) =>
        set((state) => {
          if (state.favorites.includes(query)) {
            return state;
          }
          return { favorites: [...state.favorites, query] };
        }),

      removeFavorite: (query) =>
        set((state) => ({
          favorites: state.favorites.filter((f) => f !== query),
        })),

      isFavorite: (query) => {
        return get().favorites.includes(query);
      },
    }),
    {
      name: 'chat-storage',
      // Only persist favorites, not messages (ephemeral)
      partialize: (state) => ({
        favorites: state.favorites,
      }),
    }
  )
);

export default useChatStore;
