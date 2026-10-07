'use client';

/**
 * Chat Interface Component
 * Main chat UI for natural language MES queries
 * Connected to agent-orchestrator via WebSocket /ws/chat
 * Extended: tool call visualization, history sidebar, session persistence
 */

import { useRef, useEffect, useState, useCallback } from 'react';
import { useChatStore } from '@/stores/chatStore';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { QuickActions } from './QuickActions';
import { ToolCallCard, ToolCallData } from './ToolCallCard';
import { saveSession, loadSession } from './SessionStore';
import { Bot, Trash2, Sparkles, RefreshCw } from 'lucide-react';
import { Message } from '@/types/nlm';

const WS_URL = (() => {
  const base = process.env.NEXT_PUBLIC_AGENT_ORCHESTRATOR_URL || 'http://localhost:8020';
  // Browser → orchestrator WebSocket auth (audit C1).
  // Dev: NEXT_PUBLIC_AGENT_WS_TOKEN === INTERNAL_SERVICE_KEY (build-time inject).
  // Prod: switch to user JWT validation in orchestrator (future cycle).
  const token = process.env.NEXT_PUBLIC_AGENT_WS_TOKEN || '';
  const wsBase = base.replace(/^http/, 'ws') + '/ws/chat';
  return token ? `${wsBase}?key=${encodeURIComponent(token)}` : wsBase;
})();

/** Extend the Message type locally to carry tool_call info */
interface ExtendedMessage extends Message {
  toolCall?: ToolCallData;
}

interface ChatInterfaceProps {
  /** Session ID passed from the parent page when user selects a history session */
  sessionId?: string;
  onSessionChange?: (id: string) => void;
}

export function ChatInterface({ sessionId: externalSessionId, onSessionChange }: ChatInterfaceProps) {
  const { messages, addMessage, clearMessages, setLoading, isLoading } = useChatStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const sessionIdRef = useRef<string>(externalSessionId ?? crypto.randomUUID());
  const [connected, setConnected] = useState(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // When external sessionId changes (user selected a history session), load its messages
  useEffect(() => {
    if (externalSessionId && externalSessionId !== sessionIdRef.current) {
      sessionIdRef.current = externalSessionId;
      const loaded = loadSession(externalSessionId) as ExtendedMessage[];
      clearMessages();
      loaded.forEach((m) => addMessage(m));
    }
  }, [externalSessionId, clearMessages, addMessage]);

  // Persist messages to localStorage whenever they change
  useEffect(() => {
    if (messages.length > 0) {
      saveSession(sessionIdRef.current, messages);
    }
  }, [messages]);

  const connect = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
    };

    ws.onclose = () => {
      setConnected(false);
      setLoading(false);
    };

    ws.onerror = () => {
      setConnected(false);
      setLoading(false);
    };

    ws.onmessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data as string) as {
          type?: string;
          content?: string;
          role?: string;
          data?: unknown;
          error?: string;
          tool_name?: string;
          input?: unknown;
          output?: unknown;
        };

        if (data.type === 'tool_call') {
          // Tool call event — show as a dedicated tool message
          const toolMsg: ExtendedMessage = {
            role: 'assistant',
            content: `[tool] ${data.tool_name ?? 'unknown'}`,
            timestamp: new Date().toISOString(),
            toolCall: {
              tool_name: data.tool_name ?? 'unknown',
              input: data.input,
              output: data.output,
            },
          };
          addMessage(toolMsg);
        } else if (data.type === 'tool_result') {
          // Update the last tool_call message with the output, or add a new message
          const toolMsg: ExtendedMessage = {
            role: 'assistant',
            content: `[tool_result] ${data.tool_name ?? ''}`,
            timestamp: new Date().toISOString(),
            toolCall: {
              tool_name: data.tool_name ?? 'unknown',
              input: data.input,
              output: data.output ?? data.data,
            },
          };
          addMessage(toolMsg);
        } else if (data.type === 'chunk' || data.type === 'message') {
          // Unwrap nested chunk: {"type":"chunk","data":{"type":"message","role":"ai","content":"..."}}
          const inner = (data.data as { role?: string; content?: string; type?: string } | undefined) ?? null;
          const role = (inner?.role ?? data.role ?? 'ai') as string;
          const content = (inner?.content ?? data.content ?? '') as string;

          // Skip server's echo of the user's own message — already shown on submit.
          if (role === 'user' || role === 'human') {
            return;
          }

          // Skip empty content (sometimes intermediate state snapshots have no message body).
          if (!content) return;

          addMessage({
            role: 'assistant',
            content,
            timestamp: new Date().toISOString(),
          });
        } else if (data.type === 'done') {
          setLoading(false);
        } else if (data.type === 'error') {
          addMessage({
            role: 'assistant',
            content: `오류: ${data.error ?? JSON.stringify(data)}`,
            isError: true,
            timestamp: new Date().toISOString(),
          });
          setLoading(false);
        }
      } catch {
        // Non-JSON fallback
        addMessage({
          role: 'assistant',
          content: event.data as string,
          timestamp: new Date().toISOString(),
        });
        setLoading(false);
      }
    };
  }, [addMessage, setLoading]);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
    };
  }, [connect]);

  const handleSubmit = async (query: string) => {
    if (!query.trim() || isLoading) return;

    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      addMessage({
        role: 'assistant',
        content: 'AI 어시스턴트 서비스에 연결할 수 없습니다. 재연결 후 다시 시도해 주세요.',
        isError: true,
        timestamp: new Date().toISOString(),
      });
      return;
    }

    addMessage({
      role: 'user',
      content: query,
      timestamp: new Date().toISOString(),
    });
    setLoading(true);

    ws.send(JSON.stringify({ session_id: sessionIdRef.current, message: query }));
  };

  const handleClearChat = () => {
    if (window.confirm('대화 내용을 모두 삭제하시겠습니까?')) {
      clearMessages();
      // Start a fresh session
      const newId = crypto.randomUUID();
      sessionIdRef.current = newId;
      onSessionChange?.(newId);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gradient-to-r from-primary-50 to-primary-50">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center">
            <Bot className="h-5 w-5 text-white" />
          </div>
          <div>
            <h2 className="font-semibold text-gray-800">MES AI 어시스턴트</h2>
            <p className="text-xs text-gray-500">자연어로 생산 현황을 조회하세요</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {/* Connection status */}
          <span
            className={`text-xs flex items-center gap-1 ${connected ? 'text-green-600' : 'text-gray-400'}`}
            title={`session: ${sessionIdRef.current.slice(0, 8)}`}
          >
            <span className={`inline-block w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-gray-300'}`} />
            {connected ? '연결됨' : '끊김'}
          </span>
          {/* Reconnect button — shown when disconnected */}
          {!connected && (
            <button
              onClick={connect}
              className="p-1.5 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
              title="재연결"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
          )}
          {messages.length > 0 && (
            <button
              onClick={handleClearChat}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              title="대화 내용 삭제"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* Messages Area */}
      <div
        ref={containerRef}
        className="flex-1 overflow-y-auto p-4 space-y-4"
      >
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center py-12">
            <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mb-4">
              <Sparkles className="h-8 w-8 text-primary-500" />
            </div>
            <h3 className="text-lg font-semibold text-gray-800 mb-2">
              안녕하세요! MES AI 어시스턴트입니다.
            </h3>
            <p className="text-gray-500 max-w-md">
              생산 현황, 설비 상태, KPI 등을 자연어로 질문해 보세요.
              <br />
              아래 빠른 질문을 클릭하거나 직접 입력하세요.
            </p>
          </div>
        ) : (
          messages.map((msg, idx) => {
            const extended = msg as ExtendedMessage;
            // Render tool call messages via ToolCallCard directly
            if (extended.toolCall) {
              return (
                <div key={idx} className="flex gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-yellow-400 text-yellow-900">
                    <Bot className="h-4 w-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <ToolCallCard toolCall={extended.toolCall} />
                  </div>
                </div>
              );
            }
            return <ChatMessage key={idx} message={msg} />;
          })
        )}

        {/* Loading Indicator */}
        {isLoading && (
          <div className="flex gap-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-gray-200 text-gray-600">
              <Bot className="h-4 w-4" />
            </div>
            <div className="flex items-center gap-2 text-gray-500 bg-gray-100 rounded-2xl rounded-tl-sm px-4 py-2.5">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
              <span className="text-sm">응답 생성 중...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Actions */}
      <QuickActions onSelect={handleSubmit} disabled={isLoading || !connected} />

      {/* Input Area */}
      <ChatInput onSubmit={handleSubmit} disabled={isLoading || !connected} />
    </div>
  );
}

export default ChatInterface;
