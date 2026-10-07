'use client';

/**
 * AI Summary Widget
 * Displays AI-generated production summary on the dashboard
 */

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { NlmService } from '@/services/nlm';
import { Bot, ArrowRight, RefreshCw, AlertCircle, Sparkles } from 'lucide-react';

export function AISummaryWidget() {
  const [summary, setSummary] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);

  const fetchSummary = async (signal?: AbortSignal) => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await NlmService.getDailySummary(signal);
      setSummary(result.text_response);
    } catch (err) {
      if (err instanceof Error && err.name === 'CanceledError') return;
      console.error('Failed to fetch AI summary:', err);
      setError('AI 요약을 불러오지 못했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const controller = new AbortController();
    abortControllerRef.current = controller;
    fetchSummary(controller.signal);
    return () => {
      controller.abort();
    };
  }, []);

  return (
    <div className="card bg-gradient-to-br from-primary-50 to-primary-50 border-primary-200">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-primary-500 rounded-lg">
            <Bot className="h-5 w-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-800">AI 생산 요약</h3>
            <p className="text-xs text-gray-500">오늘의 생산 현황을 AI가 분석했습니다</p>
          </div>
        </div>
        <button
          onClick={() => {
            abortControllerRef.current?.abort();
            const controller = new AbortController();
            abortControllerRef.current = controller;
            fetchSummary(controller.signal);
          }}
          disabled={isLoading}
          className="p-2 text-gray-400 hover:text-primary-500 hover:bg-primary-100 rounded-lg transition-colors disabled:opacity-50"
          title="새로고침"
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Content */}
      <div className="min-h-[80px]">
        {isLoading ? (
          <div className="space-y-2">
            <div className="h-4 bg-primary-100 rounded animate-pulse w-full" />
            <div className="h-4 bg-primary-100 rounded animate-pulse w-4/5" />
            <div className="h-4 bg-primary-100 rounded animate-pulse w-3/5" />
          </div>
        ) : error ? (
          <div className="flex items-center gap-2 text-amber-600">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">{error}</span>
          </div>
        ) : summary ? (
          <p className="text-gray-600 text-sm leading-relaxed whitespace-pre-line">
            {summary}
          </p>
        ) : (
          <div className="flex items-center gap-2 text-gray-500">
            <Sparkles className="h-4 w-4" />
            <span className="text-sm">요약 정보가 없습니다.</span>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="mt-4 pt-3 border-t border-primary-200">
        <Link
          href="/chat"
          className="inline-flex items-center gap-1 text-sm text-primary-600 hover:text-primary-700 font-medium"
        >
          더 자세히 물어보기
          <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </div>
  );
}

export default AISummaryWidget;
