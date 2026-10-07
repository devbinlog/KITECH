'use client';

/**
 * Status Cards Component
 * Displays equipment/item status in a card grid layout
 * Similar to StatusGrid but with a different card style
 */

import { StatusCardsProps, StatusCardItem } from '@/types/nlm';
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Power,
  Settings,
  Wifi,
  WifiOff,
  Server,
} from 'lucide-react';

type StatusType = 'RUN' | 'RUNNING' | 'IDLE' | 'READY' | 'ERROR' | 'MAINTENANCE' | 'OFFLINE' | 'DONE' | 'PAUSE';

const STATUS_CONFIG: Record<StatusType, { label: string; color: string; bgColor: string; icon: React.ReactNode }> = {
  RUN: {
    label: '가동중',
    color: 'text-green-600',
    bgColor: 'bg-green-50 border-green-200',
    icon: <Activity className="h-5 w-5" />,
  },
  RUNNING: {
    label: '가동중',
    color: 'text-green-600',
    bgColor: 'bg-green-50 border-green-200',
    icon: <Activity className="h-5 w-5" />,
  },
  IDLE: {
    label: '대기',
    color: 'text-amber-600',
    bgColor: 'bg-amber-50 border-amber-200',
    icon: <Clock className="h-5 w-5" />,
  },
  READY: {
    label: '준비',
    color: 'text-primary-600',
    bgColor: 'bg-primary-50 border-primary-200',
    icon: <CheckCircle2 className="h-5 w-5" />,
  },
  ERROR: {
    label: '에러',
    color: 'text-red-600',
    bgColor: 'bg-red-50 border-red-200',
    icon: <AlertTriangle className="h-5 w-5" />,
  },
  MAINTENANCE: {
    label: '정비중',
    color: 'text-purple-600',
    bgColor: 'bg-purple-50 border-purple-200',
    icon: <Settings className="h-5 w-5" />,
  },
  OFFLINE: {
    label: '오프라인',
    color: 'text-gray-500',
    bgColor: 'bg-gray-50 border-gray-200',
    icon: <Power className="h-5 w-5" />,
  },
  DONE: {
    label: '완료',
    color: 'text-green-600',
    bgColor: 'bg-green-50 border-green-200',
    icon: <CheckCircle2 className="h-5 w-5" />,
  },
  PAUSE: {
    label: '일시정지',
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-50 border-yellow-200',
    icon: <Clock className="h-5 w-5" />,
  },
};

function getStatusConfig(status: string) {
  const normalized = status?.toUpperCase() as StatusType;
  return STATUS_CONFIG[normalized] || STATUS_CONFIG.IDLE;
}

function StatusCard({ item }: { item: StatusCardItem }) {
  const config = getStatusConfig(item.status);

  return (
    <div
      className={`rounded-xl border-2 p-4 transition-all hover:shadow-lg ${config.bgColor}`}
    >
      {/* Header with icon and status */}
      <div className="flex items-start justify-between mb-3">
        <div className={`p-2 rounded-lg ${config.bgColor}`}>
          {config.icon}
        </div>
        <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${config.color} ${config.bgColor}`}>
          <span className="relative flex h-2 w-2">
            <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${item.status === 'RUN' || item.status === 'RUNNING' ? 'bg-green-400' : 'bg-transparent'}`}></span>
            <span className={`relative inline-flex rounded-full h-2 w-2 ${item.status === 'RUN' || item.status === 'RUNNING' ? 'bg-green-500' : item.status === 'ERROR' ? 'bg-red-500' : 'bg-gray-400'}`}></span>
          </span>
          {config.label}
        </div>
      </div>

      {/* Name and ID */}
      <div className="mb-3">
        <h4 className="font-bold text-gray-800 text-lg">{item.name}</h4>
        <p className="text-xs text-gray-500">{item.id}</p>
      </div>

      {/* Type badge */}
      {item.type && (
        <div className="mb-3">
          <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-700">
            <Server className="h-3 w-3 mr-1" />
            {item.type}
          </span>
        </div>
      )}

      {/* Metrics */}
      {item.metrics && Object.keys(item.metrics).length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-200/50">
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(item.metrics).slice(0, 4).map(([key, value]) => (
              <div key={key} className="text-xs">
                <span className="text-gray-500 block">{formatMetricLabel(key)}</span>
                <span className="font-semibold text-gray-700">
                  {formatMetricValue(key, value)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function formatMetricLabel(key: string): string {
  const labels: Record<string, string> = {
    spindle_rpm: 'RPM',
    load_percent: '부하',
    temperature: '온도',
    cycle_time: '사이클',
    utilization: '가동률',
    ok_count: '양품',
    ng_count: '불량',
    feed_rate: '이송속도',
    current: '전류',
  };
  return labels[key] || key.replace(/_/g, ' ');
}

function formatMetricValue(key: string, value: unknown): string {
  if (value === null || value === undefined) return '-';

  if (typeof value === 'number') {
    if (key.includes('percent') || key === 'utilization') {
      return `${value.toFixed(1)}%`;
    }
    if (key === 'temperature') {
      return `${value.toFixed(1)}°C`;
    }
    if (key === 'spindle_rpm') {
      return `${value.toLocaleString()}`;
    }
    return value.toLocaleString();
  }

  return String(value);
}

function EmptyState() {
  return (
    <div className="h-48 flex flex-col items-center justify-center text-gray-400">
      <Server className="h-12 w-12 mb-3 opacity-50" />
      <p className="text-sm">설비 데이터가 없습니다</p>
    </div>
  );
}

export function StatusCards({ title, items }: StatusCardsProps) {
  if (!items || items.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        {title && <h3 className="font-semibold text-gray-800 mb-4">{title}</h3>}
        <EmptyState />
      </div>
    );
  }

  // Status summary
  const statusCounts = items.reduce(
    (acc, item) => {
      const status = item.status?.toUpperCase() || 'IDLE';
      acc[status] = (acc[status] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      {/* Header with summary */}
      {title && (
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-800">{title}</h3>
          <div className="flex items-center gap-3 text-xs">
            {Object.entries(statusCounts).map(([status, count]) => {
              const config = getStatusConfig(status);
              return (
                <div key={status} className={`flex items-center gap-1 ${config.color}`}>
                  {config.icon}
                  <span>{config.label}: {count}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Cards grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {items.map((item) => (
          <StatusCard key={item.id} item={item} />
        ))}
      </div>
    </div>
  );
}

export default StatusCards;
