'use client';

/**
 * Query History Hook
 * Manages query history and favorites with React Query
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { NlmService } from '@/services/nlm';
import { useChatStore } from '@/stores/chatStore';
import { POLLING, STALE_TIME } from '@/config/constants';

// Query keys
const QUERY_KEYS = {
  history: ['nlm', 'history'] as const,
  favorites: ['nlm', 'favorites'] as const,
  quota: ['nlm', 'quota'] as const,
};

/**
 * Hook for managing query history
 */
export function useQueryHistory(limit = 50) {
  return useQuery({
    queryKey: [...QUERY_KEYS.history, limit],
    queryFn: () => NlmService.getHistory(limit),
    staleTime: STALE_TIME.MEDIUM,
  });
}

/**
 * Hook for managing favorites
 */
export function useFavorites() {
  const queryClient = useQueryClient();
  const { favorites: localFavorites, addFavorite: addLocalFavorite, removeFavorite: removeLocalFavorite } =
    useChatStore();

  // Fetch favorites from server (falls back to local)
  const query = useQuery({
    queryKey: QUERY_KEYS.favorites,
    queryFn: async () => {
      try {
        return await NlmService.getFavorites();
      } catch {
        // Fall back to local favorites if API fails
        return localFavorites;
      }
    },
    initialData: localFavorites,
    staleTime: STALE_TIME.LONG,
  });

  // Add favorite mutation
  const addMutation = useMutation({
    mutationFn: async (queryText: string) => {
      // Optimistically update local store
      addLocalFavorite(queryText);
      try {
        await NlmService.addFavorite(queryText);
      } catch {
        // API might not be available, local is still updated
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.favorites });
    },
  });

  // Remove favorite mutation
  const removeMutation = useMutation({
    mutationFn: async (queryText: string) => {
      // Optimistically update local store
      removeLocalFavorite(queryText);
      try {
        await NlmService.removeFavorite(queryText);
      } catch {
        // API might not be available, local is still updated
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.favorites });
    },
  });

  return {
    favorites: query.data || [],
    isLoading: query.isLoading,
    addFavorite: addMutation.mutate,
    removeFavorite: removeMutation.mutate,
    isFavorite: (queryText: string) =>
      (query.data || []).includes(queryText) || localFavorites.includes(queryText),
  };
}

/**
 * Hook for checking API quota status
 */
export function useQuotaStatus() {
  return useQuery({
    queryKey: QUERY_KEYS.quota,
    queryFn: () => NlmService.getQuotaStatus(),
    staleTime: STALE_TIME.SHORT,
    refetchInterval: POLLING.SLOW,
  });
}

export default useQueryHistory;
