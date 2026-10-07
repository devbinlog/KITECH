/**
 * SessionStore
 * localStorage-based client-side chat session history
 * Key convention: "mes-chat-sessions" (index) + "mes-chat-session:{id}" (per-session)
 */

import { Message } from '@/types/nlm';

const INDEX_KEY = 'mes-chat-sessions';
const SESSION_PREFIX = 'mes-chat-session:';
const MAX_SESSIONS = 50;

export interface SessionMeta {
  id: string;
  preview: string;     // first user message, max 50 chars
  createdAt: string;   // ISO string
  updatedAt: string;
  messageCount: number;
}

function getIndex(): SessionMeta[] {
  try {
    const raw = localStorage.getItem(INDEX_KEY);
    return raw ? (JSON.parse(raw) as SessionMeta[]) : [];
  } catch {
    return [];
  }
}

function saveIndex(index: SessionMeta[]): void {
  try {
    localStorage.setItem(INDEX_KEY, JSON.stringify(index));
  } catch {
    // localStorage quota exceeded — silently ignore
  }
}

export function saveSession(id: string, messages: Message[]): void {
  if (!messages.length) return;

  const userMessage = messages.find((m) => m.role === 'user');
  const preview = userMessage
    ? userMessage.content.slice(0, 50)
    : messages[0].content.slice(0, 50);

  const now = new Date().toISOString();

  // Save full messages
  try {
    localStorage.setItem(SESSION_PREFIX + id, JSON.stringify(messages));
  } catch {
    return;
  }

  // Update index
  const index = getIndex();
  const existing = index.findIndex((s) => s.id === id);
  const meta: SessionMeta = {
    id,
    preview,
    createdAt: existing >= 0 ? index[existing].createdAt : now,
    updatedAt: now,
    messageCount: messages.length,
  };

  if (existing >= 0) {
    index[existing] = meta;
  } else {
    index.unshift(meta);
  }

  // Trim old sessions beyond MAX_SESSIONS
  const trimmed = index.slice(0, MAX_SESSIONS);
  // Remove pruned sessions from storage
  for (let i = MAX_SESSIONS; i < index.length; i++) {
    try {
      localStorage.removeItem(SESSION_PREFIX + index[i].id);
    } catch {
      // ignore
    }
  }

  saveIndex(trimmed);
}

export function loadSession(id: string): Message[] {
  try {
    const raw = localStorage.getItem(SESSION_PREFIX + id);
    return raw ? (JSON.parse(raw) as Message[]) : [];
  } catch {
    return [];
  }
}

export function listSessions(): SessionMeta[] {
  return getIndex();
}

export function deleteSession(id: string): void {
  try {
    localStorage.removeItem(SESSION_PREFIX + id);
  } catch {
    // ignore
  }
  const index = getIndex().filter((s) => s.id !== id);
  saveIndex(index);
}
