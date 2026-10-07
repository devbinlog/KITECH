'use client';

/**
 * WebSocket Hook for NL Router
 * Manages WebSocket connection and message handling
 */

import { useEffect, useRef, useCallback, useState } from 'react';

export type ChannelType =
  | 'equipment_status'
  | 'production_results'
  | 'kpi_updates'
  | 'work_order_status'
  | 'alerts';

export interface WebSocketMessage {
  type: string;
  channel?: string;
  data?: unknown;
  timestamp?: string;
  error?: string;
}

export interface UseWebSocketOptions {
  url?: string;
  autoConnect?: boolean;
  reconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onMessage?: (message: WebSocketMessage) => void;
  onError?: (error: Event) => void;
  onReconnect?: () => void;
}

export interface UseWebSocketReturn {
  isConnected: boolean;
  connect: () => void;
  disconnect: () => void;
  send: (message: Record<string, unknown>) => void;
  subscribe: (channel: ChannelType, filters?: Record<string, unknown>) => void;
  unsubscribe: (channel: ChannelType) => void;
  sendQuery: (query: string) => void;
  lastMessage: WebSocketMessage | null;
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
}

const DEFAULT_WS_URL =
  process.env.NEXT_PUBLIC_NL_ROUTER_WS_URL || 'ws://localhost:8001/ws';

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    url = DEFAULT_WS_URL,
    autoConnect = false,
    reconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    onConnect,
    onDisconnect,
    onMessage,
    onError,
  } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isMountedRef = useRef(true);
  const optionsRef = useRef<{ reconnect: boolean; reconnectInterval: number; maxReconnectAttempts: number; onConnect?: () => void; onDisconnect?: () => void; onMessage?: (message: WebSocketMessage) => void; onError?: (error: Event) => void; onReconnect?: () => void }>({ reconnect, reconnectInterval, maxReconnectAttempts, onConnect, onDisconnect, onMessage, onError, onReconnect: options.onReconnect });

  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<
    'connecting' | 'connected' | 'disconnected' | 'error'
  >('disconnected');

  // Keep options ref up to date without re-creating connect
  optionsRef.current = { reconnect, reconnectInterval, maxReconnectAttempts, onConnect, onDisconnect, onMessage, onError, onReconnect: options.onReconnect };

  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    // Don't connect if already connected or connecting
    if (
      wsRef.current?.readyState === WebSocket.OPEN ||
      wsRef.current?.readyState === WebSocket.CONNECTING
    ) {
      return;
    }

    setConnectionStatus('connecting');

    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
      const wsUrl = token ? `${url}?token=${token}` : url;

      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        if (!isMountedRef.current) return;
        setIsConnected(true);
        setConnectionStatus('connected');
        if (reconnectAttemptsRef.current > 0) {
          optionsRef.current.onReconnect?.();
        }
        reconnectAttemptsRef.current = 0;
        optionsRef.current.onConnect?.();
      };

      wsRef.current.onclose = () => {
        if (!isMountedRef.current) return;
        setIsConnected(false);
        setConnectionStatus('disconnected');
        optionsRef.current.onDisconnect?.();

        // Attempt reconnection using ref values to avoid stale closure
        const { reconnect: shouldReconnect, maxReconnectAttempts: maxAttempts, reconnectInterval: interval } = optionsRef.current;
        if (shouldReconnect && reconnectAttemptsRef.current < maxAttempts) {
          reconnectAttemptsRef.current++;
          reconnectTimeoutRef.current = setTimeout(() => {
            if (isMountedRef.current) connect();
          }, interval);
        }
      };

      wsRef.current.onerror = (error) => {
        if (!isMountedRef.current) return;
        setConnectionStatus('error');
        optionsRef.current.onError?.(error);
      };

      wsRef.current.onmessage = (event) => {
        if (!isMountedRef.current) return;
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);
          optionsRef.current.onMessage?.(message);
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };
    } catch (error) {
      console.error('WebSocket connection error:', error);
      setConnectionStatus('error');
    }
  }, [url]); // url is the only stable dep needed; all options accessed via ref

  const disconnect = useCallback(() => {
    clearReconnectTimeout();
    reconnectAttemptsRef.current = optionsRef.current.maxReconnectAttempts; // Prevent auto-reconnect

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
    setConnectionStatus('disconnected');
  }, [clearReconnectTimeout]);

  const send = useCallback((message: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected. Message not sent.');
    }
  }, []);

  const subscribe = useCallback(
    (channel: ChannelType, filters?: Record<string, unknown>) => {
      send({
        action: 'subscribe',
        channel,
        filters: filters || {},
      });
    },
    [send]
  );

  const unsubscribe = useCallback(
    (channel: ChannelType) => {
      send({
        action: 'unsubscribe',
        channel,
      });
    },
    [send]
  );

  const sendQuery = useCallback(
    (query: string) => {
      send({
        action: 'query',
        query,
      });
    },
    [send]
  );

  // Auto-connect if enabled
  useEffect(() => {
    isMountedRef.current = true;
    if (autoConnect) {
      connect();
    }

    return () => {
      isMountedRef.current = false;
      clearReconnectTimeout();
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [autoConnect, connect, clearReconnectTimeout]);

  return {
    isConnected,
    connect,
    disconnect,
    send,
    subscribe,
    unsubscribe,
    sendQuery,
    lastMessage,
    connectionStatus,
  };
}

export default useWebSocket;
