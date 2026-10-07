import { useState, useCallback } from 'react';

interface UseApiState<T> {
  data: T | null;
  error: string | null;
  isLoading: boolean;
}

interface UseApiOptions {
  baseUrl?: string;
  headers?: Record<string, string>;
}

export function useApi<T = any>(options: UseApiOptions = {}) {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    error: null,
    isLoading: false,
  });

  const getHeaders = useCallback(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    return {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    };
  }, [options.headers]);

  const request = useCallback(
    async (
      endpoint: string,
      method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE' = 'GET',
      body?: any
    ): Promise<T | null> => {
      setState((prev) => ({ ...prev, isLoading: true, error: null }));

      try {
        const baseUrl = options.baseUrl || process.env.NEXT_PUBLIC_API_URL || '';
        const response = await fetch(`${baseUrl}${endpoint}`, {
          method,
          headers: getHeaders(),
          body: body ? JSON.stringify(body) : undefined,
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        const data = await response.json();
        setState({ data, error: null, isLoading: false });
        return data;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error';
        setState({ data: null, error: errorMessage, isLoading: false });
        return null;
      }
    },
    [options.baseUrl, getHeaders]
  );

  const get = useCallback((endpoint: string) => request(endpoint, 'GET'), [request]);
  const post = useCallback((endpoint: string, body: any) => request(endpoint, 'POST', body), [request]);
  const put = useCallback((endpoint: string, body: any) => request(endpoint, 'PUT', body), [request]);
  const patch = useCallback((endpoint: string, body: any) => request(endpoint, 'PATCH', body), [request]);
  const del = useCallback((endpoint: string) => request(endpoint, 'DELETE'), [request]);

  return {
    ...state,
    get,
    post,
    put,
    patch,
    delete: del,
    request,
  };
}
