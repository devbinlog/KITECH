/**
 * NLM (Natural Language MES) API Service
 * Handles communication with the NL Router Gateway
 */

import axios from 'axios';
import { QueryResult, Message } from '@/types/nlm';

const NL_ROUTER_URL = process.env.NEXT_PUBLIC_NL_ROUTER_URL || 'http://localhost:8001/api/v1';

// Create axios instance for NL Router
const nlmApi = axios.create({
  baseURL: NL_ROUTER_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout for LLM calls
});

// Request interceptor - add auth token
nlmApi.interceptors.request.use(
  (config) => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle errors
nlmApi.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNABORTED') {
      return Promise.reject(new Error('요청 시간이 초과되었습니다. 다시 시도해 주세요.'));
    }
    if (error.response?.status === 429) {
      return Promise.reject(new Error('요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.'));
    }
    if (error.response?.status === 503) {
      return Promise.reject(new Error('AI 서비스를 사용할 수 없습니다. 잠시 후 다시 시도해 주세요.'));
    }
    return Promise.reject(error);
  }
);

export class NlmService {
  /**
   * Send a natural language query to the NL Router
   */
  static async query(query: string, signal?: AbortSignal): Promise<QueryResult> {
    const response = await nlmApi.post<QueryResult>('/nlm/query', { query }, { signal });
    return response.data;
  }

  /**
   * Get query history for the current user
   */
  static async getHistory(limit = 50): Promise<Message[]> {
    const response = await nlmApi.get<{ messages: Message[] }>('/nlm/history', {
      params: { limit },
    });
    return response.data.messages;
  }

  /**
   * Add a query to favorites
   */
  static async addFavorite(query: string): Promise<void> {
    await nlmApi.post('/nlm/favorites', { query });
  }

  /**
   * Remove a query from favorites
   */
  static async removeFavorite(query: string): Promise<void> {
    await nlmApi.delete('/nlm/favorites', { data: { query } });
  }

  /**
   * Get list of favorite queries
   */
  static async getFavorites(): Promise<string[]> {
    const response = await nlmApi.get<{ favorites: string[] }>('/nlm/favorites');
    return response.data.favorites;
  }

  /**
   * Get usage quota status
   */
  static async getQuotaStatus(): Promise<{
    requests: { used: number; limit: number; reset_at: string };
    llm_calls: { used: number; limit: number; reset_at: string };
  }> {
    const response = await nlmApi.get('/nlm/quota');
    return response.data;
  }

  /**
   * Get a quick summary for dashboard widget
   */
  static async getDailySummary(signal?: AbortSignal): Promise<QueryResult> {
    return this.query('오늘 생산 현황 요약해줘', signal);
  }
}

export default NlmService;
