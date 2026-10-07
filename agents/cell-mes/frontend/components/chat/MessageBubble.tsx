'use client';

/**
 * MessageBubble
 * Role-aware message renderer.
 * Roles: user | assistant | tool | system
 * markdown rendering is deferred to next cycle — raw text only.
 */

import { User, Bot, Wrench, Info, AlertCircle, Clock } from 'lucide-react';
import { ToolCallCard, ToolCallData } from './ToolCallCard';

export type MessageRole = 'user' | 'assistant' | 'tool' | 'system';

export interface BubbleMessage {
  role: MessageRole;
  content: string;
  isError?: boolean;
  timestamp?: string;
  toolCall?: ToolCallData;
}

interface MessageBubbleProps {
  message: BubbleMessage;
}

function Avatar({ role, isError }: { role: MessageRole; isError?: boolean }) {
  const base = 'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center';
  if (role === 'user')
    return (
      <div className={`${base} bg-primary-500 text-white`}>
        <User className="h-4 w-4" />
      </div>
    );
  if (role === 'tool')
    return (
      <div className={`${base} bg-yellow-400 text-yellow-900`}>
        <Wrench className="h-4 w-4" />
      </div>
    );
  if (role === 'system')
    return (
      <div className={`${base} bg-purple-100 text-purple-600`}>
        <Info className="h-4 w-4" />
      </div>
    );
  // assistant
  return (
    <div className={`${base} ${isError ? 'bg-red-100 text-red-600' : 'bg-gray-200 text-gray-600'}`}>
      <Bot className="h-4 w-4" />
    </div>
  );
}

function bubbleClasses(role: MessageRole, isError?: boolean): string {
  if (role === 'user') return 'bg-primary-500 text-white rounded-2xl rounded-tr-sm px-4 py-2.5';
  if (role === 'tool') return 'bg-yellow-50 border border-yellow-200 text-yellow-900 rounded-2xl rounded-tl-sm px-4 py-2.5';
  if (role === 'system') return 'bg-purple-50 border border-purple-200 text-purple-800 rounded-2xl rounded-tl-sm px-4 py-2.5 italic text-xs';
  if (isError) return 'bg-red-50 border border-red-200 text-red-700 rounded-2xl rounded-tl-sm px-4 py-2.5';
  return 'bg-gray-100 text-gray-800 rounded-2xl rounded-tl-sm px-4 py-2.5';
}

function formatTimestamp(ts?: string): string | null {
  if (!ts) return null;
  return new Date(ts).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const { role, content, isError, timestamp, toolCall } = message;
  const isUser = role === 'user';

  // tool role with a structured toolCall — render ToolCallCard inline
  if (role === 'tool' && toolCall) {
    return (
      <div className="flex gap-3">
        <Avatar role="tool" />
        <div className="flex-1 min-w-0">
          <ToolCallCard toolCall={toolCall} />
          {timestamp && (
            <div className="flex items-center gap-1 mt-1 text-xs text-gray-400">
              <Clock className="h-3 w-3" />
              <span>{formatTimestamp(timestamp)}</span>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <Avatar role={role} isError={isError} />

      <div className={`flex-1 max-w-[85%] min-w-0 ${isUser ? 'flex flex-col items-end' : ''}`}>
        <div className={bubbleClasses(role, isError)}>
          {isError && (
            <div className="flex items-center gap-1 mb-1 text-red-600">
              <AlertCircle className="h-4 w-4" />
              <span className="text-xs font-medium">오류</span>
            </div>
          )}
          <p className="whitespace-pre-wrap text-sm leading-relaxed">{content}</p>
        </div>

        {timestamp && (
          <div className={`flex items-center gap-1 mt-1 text-xs text-gray-400 ${isUser ? 'justify-end' : ''}`}>
            <Clock className="h-3 w-3" />
            <span>{formatTimestamp(timestamp)}</span>
          </div>
        )}
      </div>
    </div>
  );
}

export default MessageBubble;
