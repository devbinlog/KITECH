'use client';

/**
 * NL Chat Page
 * AI Assistant page — 2-pane layout: history sidebar (left) + chat interface (right)
 */

import { useState, useCallback } from 'react';
import { ChatInterface } from '@/components/chat';
import { HistorySidebar } from '@/components/chat/HistorySidebar';
import { loadSession } from '@/components/chat/SessionStore';
import { useChatStore } from '@/stores/chatStore';
import { Message } from '@/types/nlm';

export default function ChatPage() {
  const [sessionId, setSessionId] = useState<string>(() => crypto.randomUUID());
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const { clearMessages, addMessage } = useChatStore();

  const handleNewSession = useCallback(() => {
    clearMessages();
    setSessionId(crypto.randomUUID());
  }, [clearMessages]);

  const handleSelectSession = useCallback(
    (id: string) => {
      if (id === sessionId) return;
      const messages = loadSession(id) as Message[];
      clearMessages();
      messages.forEach((m) => addMessage(m));
      setSessionId(id);
    },
    [sessionId, clearMessages, addMessage],
  );

  return (
    <div className="flex h-[calc(100vh-3rem)] overflow-hidden">
      {/* Left: History Sidebar */}
      <HistorySidebar
        currentSessionId={sessionId}
        onNewSession={handleNewSession}
        onSelectSession={handleSelectSession}
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed((v) => !v)}
      />

      {/* Right: Chat Interface */}
      <div className="flex-1 min-w-0 p-0">
        <ChatInterface
          sessionId={sessionId}
          onSessionChange={setSessionId}
        />
      </div>
    </div>
  );
}
