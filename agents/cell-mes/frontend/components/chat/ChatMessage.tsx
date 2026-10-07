'use client';

/**
 * Chat Message Component
 * Displays a single message in the chat interface
 */

import { Message } from '@/types/nlm';
import { DynamicRenderer } from '@/components/dynamic/DynamicRenderer';
import { User, Bot, AlertCircle, Clock } from 'lucide-react';

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';
  const isError = message.isError;

  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return null;
    const date = new Date(timestamp);
    return date.toLocaleTimeString('ko-KR', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser ? 'bg-primary-500 text-white' : 'bg-gray-200 text-gray-600'
        }`}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      {/* Message Content */}
      <div className={`flex-1 max-w-[85%] ${isUser ? 'flex flex-col items-end' : ''}`}>
        {/* Text Bubble */}
        <div
          className={`rounded-2xl px-4 py-2.5 ${
            isUser
              ? 'bg-primary-500 text-white rounded-tr-sm'
              : isError
              ? 'bg-red-50 text-red-700 border border-red-200 rounded-tl-sm'
              : 'bg-gray-100 text-gray-800 rounded-tl-sm'
          }`}
        >
          {isError && (
            <div className="flex items-center gap-1 mb-1 text-red-600">
              <AlertCircle className="h-4 w-4" />
              <span className="text-xs font-medium">오류</span>
            </div>
          )}
          <p className="whitespace-pre-wrap text-sm leading-relaxed">
            {message.content}
          </p>
        </div>

        {/* Timestamp */}
        {message.timestamp && (
          <div
            className={`flex items-center gap-1 mt-1 text-xs text-gray-400 ${
              isUser ? 'justify-end' : ''
            }`}
          >
            <Clock className="h-3 w-3" />
            <span>{formatTimestamp(message.timestamp)}</span>
          </div>
        )}

        {/* Dynamic UI Schema Rendering */}
        {message.uiSchema && message.uiSchema.components && message.uiSchema.components.length > 0 && (
          <div className="mt-3 w-full bg-white rounded-lg border border-gray-200 overflow-hidden">
            <DynamicRenderer schema={message.uiSchema} />
          </div>
        )}

        {/* Metadata (Debug info - can be removed in production) */}
        {message.metadata?.intent && (
          <div className="mt-2 text-xs text-gray-400">
            <span>
              의도: {message.metadata.intent} ({((message.metadata.confidence ?? 0) * 100).toFixed(0)}%)
            </span>
            {message.metadata.processing_time_ms != null && (
              <>
                <span className="mx-2">|</span>
                <span>처리: {message.metadata.processing_time_ms}ms</span>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default ChatMessage;
