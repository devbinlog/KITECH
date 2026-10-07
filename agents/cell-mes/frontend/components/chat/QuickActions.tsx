'use client';

/**
 * Quick Actions Component
 * Predefined quick action buttons for common queries
 */

import {
  BarChart3,
  ClipboardList,
  Cpu,
  TrendingUp,
  Package,
  Calendar,
} from 'lucide-react';

interface QuickAction {
  label: string;
  query: string;
  icon: React.ReactNode;
}

const QUICK_ACTIONS: QuickAction[] = [
  {
    label: '오늘 생산 현황',
    query: '오늘 생산 현황 보여줘',
    icon: <ClipboardList className="h-4 w-4" />,
  },
  {
    label: '설비 상태',
    query: '설비 상태 조회',
    icon: <Cpu className="h-4 w-4" />,
  },
  {
    label: '가동률',
    query: '가동률 보여줘',
    icon: <BarChart3 className="h-4 w-4" />,
  },
  {
    label: '이번 주 수율',
    query: '이번 주 수율 추이',
    icon: <TrendingUp className="h-4 w-4" />,
  },
  {
    label: '작업지시 목록',
    query: '진행중인 작업지시 목록 보여줘',
    icon: <Package className="h-4 w-4" />,
  },
  {
    label: '오늘 스케줄',
    query: '오늘 생산 스케줄 보여줘',
    icon: <Calendar className="h-4 w-4" />,
  },
];

interface QuickActionsProps {
  onSelect: (query: string) => void;
  disabled?: boolean;
}

export function QuickActions({ onSelect, disabled = false }: QuickActionsProps) {
  return (
    <div className="px-4 py-3 border-t border-gray-100 bg-gray-50">
      <p className="text-xs text-gray-500 mb-2">자주 묻는 질문</p>
      <div className="flex gap-2 flex-wrap">
        {QUICK_ACTIONS.map((action) => (
          <button
            key={action.label}
            onClick={() => onSelect(action.query)}
            disabled={disabled}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-white border border-gray-200 hover:border-primary-300 hover:bg-primary-50 rounded-full transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {action.icon}
            <span>{action.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

export default QuickActions;
