'use client';

/**
 * HistorySidebar
 * 300px left sidebar listing past chat sessions from localStorage.
 * Clicking a session loads its messages into the active chat.
 */

import { useEffect, useState } from 'react';
import { MessageSquarePlus, Clock, Hash, ChevronLeft, ChevronRight, Trash2 } from 'lucide-react';
import { listSessions, deleteSession, SessionMeta } from './SessionStore';

interface HistorySidebarProps {
  currentSessionId: string;
  onNewSession: () => void;
  onSelectSession: (id: string) => void;
  /** Collapse/expand controlled by parent so mobile layout can manage it */
  collapsed: boolean;
  onToggleCollapse: () => void;
}

function formatRelativeTime(isoString: string): string {
  const now = Date.now();
  const ts = new Date(isoString).getTime();
  const diffMs = now - ts;
  const diffMin = Math.floor(diffMs / 60_000);
  const diffHr = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHr / 24);

  if (diffMin < 1) return '방금';
  if (diffMin < 60) return `${diffMin}분 전`;
  if (diffHr < 24) return `${diffHr}시간 전`;
  if (diffDay < 7) return `${diffDay}일 전`;
  return new Date(isoString).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' });
}

export function HistorySidebar({
  currentSessionId,
  onNewSession,
  onSelectSession,
  collapsed,
  onToggleCollapse,
}: HistorySidebarProps) {
  const [sessions, setSessions] = useState<SessionMeta[]>([]);

  // Refresh list whenever sidebar becomes visible or a new session is created
  useEffect(() => {
    setSessions(listSessions());
  }, [collapsed, currentSessionId]);

  const handleDelete = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (!window.confirm('이 대화를 삭제하시겠습니까?')) return;
    deleteSession(id);
    setSessions(listSessions());
  };

  if (collapsed) {
    return (
      <div className="flex flex-col items-center py-3 w-10 border-r border-gray-200 bg-gray-50 flex-shrink-0">
        <button
          onClick={onToggleCollapse}
          className="p-1.5 text-gray-400 hover:text-gray-700 hover:bg-gray-200 rounded-lg transition-colors"
          title="사이드바 열기"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col w-[300px] flex-shrink-0 border-r border-gray-200 bg-gray-50 overflow-hidden">
      {/* Sidebar header */}
      <div className="flex items-center justify-between px-3 py-3 border-b border-gray-200">
        <span className="text-sm font-semibold text-gray-700">대화 기록</span>
        <button
          onClick={onToggleCollapse}
          className="p-1.5 text-gray-400 hover:text-gray-700 hover:bg-gray-200 rounded-lg transition-colors"
          title="사이드바 닫기"
        >
          <ChevronLeft className="h-4 w-4" />
        </button>
      </div>

      {/* New chat button */}
      <div className="px-3 py-2 border-b border-gray-200">
        <button
          onClick={onNewSession}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium text-white bg-primary-500 hover:bg-primary-600 rounded-lg transition-colors"
        >
          <MessageSquarePlus className="h-4 w-4" />
          새 대화
        </button>
      </div>

      {/* Session list */}
      <div className="flex-1 overflow-y-auto">
        {sessions.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center px-4">
            <Clock className="h-8 w-8 text-gray-300 mb-2" />
            <p className="text-sm text-gray-400">대화 기록이 없습니다.</p>
          </div>
        ) : (
          <ul className="py-1">
            {sessions.map((session) => {
              const isActive = session.id === currentSessionId;
              return (
                <li key={session.id}>
                  <button
                    onClick={() => onSelectSession(session.id)}
                    className={`group w-full text-left px-3 py-2.5 transition-colors hover:bg-gray-100 ${
                      isActive ? 'bg-primary-50 border-r-2 border-primary-500' : ''
                    }`}
                  >
                    <div className="flex items-start justify-between gap-1">
                      <p className={`text-sm truncate flex-1 ${isActive ? 'text-primary-700 font-medium' : 'text-gray-700'}`}>
                        {session.preview || '(빈 대화)'}
                      </p>
                      <button
                        onClick={(e) => handleDelete(e, session.id)}
                        className="flex-shrink-0 opacity-0 group-hover:opacity-100 p-0.5 text-gray-400 hover:text-red-500 transition-colors"
                        title="삭제"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-gray-400 flex items-center gap-0.5">
                        <Clock className="h-3 w-3" />
                        {formatRelativeTime(session.updatedAt)}
                      </span>
                      <span className="text-xs text-gray-400 flex items-center gap-0.5">
                        <Hash className="h-3 w-3" />
                        {session.id.slice(0, 8)}
                      </span>
                    </div>
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}

export default HistorySidebar;
