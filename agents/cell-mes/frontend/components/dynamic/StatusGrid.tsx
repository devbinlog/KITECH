'use client';

/**
 * Status Grid Component
 * Displays equipment status in a grid layout
 */

import { StatusGridProps, StatusItem } from '@/types/nlm';
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Power,
  Settings,
  Wifi,
  WifiOff,
} from 'lucide-react';

type StatusType = 'RUN' | 'RUNNING' | 'IDLE' | 'READY' | 'ERROR' | 'MAINTENANCE' | 'OFFLINE' | 'DONE' | 'PAUSE';

const STATUS_CONFIG: Record<StatusType, { label: string; color: string; bgColor: string; icon: React.ReactNode }> = {
  RUN: {
    label: '가동중',
    color: 'text-green-600',
    bgColor: 'bg-green-50 border-green-200',
    icon: <Activity className="h-4 w-4" />,
  },
  RUNNING: {
    label: '가동중',
    color: 'text-green-600',
    bgColor: 'bg-green-50 border-green-200',
    icon: <Activity className="h-4 w-4" />,
  },
  IDLE: {
    label: '대기',
    color: 'text-amber-600',
    bgColor: 'bg-amber-50 border-amber-200',
    icon: <Clock className="h-4 w-4" />,
  },
  READY: {
    label: '준비',
    color: 'text-primary-600',
    bgColor: 'bg-primary-50 border-primary-200',
    icon: <CheckCircle2 className="h-4 w-4" />,
  },
  ERROR: {
    label: '에러',
    color: 'text-red-600',
    bgColor: 'bg-red-50 border-red-200',
    icon: <AlertTriangle className="h-4 w-4" />,
  },
  MAINTENANCE: {
    label: '정비중',
    color: 'text-purple-600',
    bgColor: 'bg-purple-50 border-purple-200',
    icon: <Settings className="h-4 w-4" />,
  },
  OFFLINE: {
    label: '오프라인',
    color: 'text-gray-500',
    bgColor: 'bg-gray-50 border-gray-200',
    icon: <Power className="h-4 w-4" />,
  },
  DONE: {
    label: '완료',
    color: 'text-green-600',
    bgColor: 'bg-green-50 border-green-200',
    icon: <CheckCircle2 className="h-4 w-4" />,
  },
  PAUSE: {
    label: '일시정지',
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-50 border-yellow-200',
    icon: <Clock className="h-4 w-4" />,
  },
};

function getStatusConfig(status: string) {
  const normalized = status?.toUpperCase() as StatusType;
  return STATUS_CONFIG[normalized] || STATUS_CONFIG.IDLE;
}

function StatusCard({ item }: { item: StatusItem }) {
  const config = getStatusConfig(item.status);

  return (
    <div
      className={`rounded-lg border p-4 transition-shadow hover:shadow-md ${config.bgColor}`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <h4 className="font-semibold text-gray-800">{item.name}</h4>
          <p className="text-xs text-gray-500">{item.id}</p>
        </div>
        <div className={`flex items-center gap-1 ${config.color}`}>
          {config.icon}
          <span className="text-xs font-medium">{config.label}</span>
        </div>
      </div>

      {/* Equipment Type */}
      {item.type && (
        <div className="text-xs text-gray-500 mb-2">타입: {item.type}</div>
      )}

      {/* Current Job */}
      {item.currentJob && (
        <div className="text-sm text-gray-700 mb-2 truncate">
          <span className="text-gray-500">작업: </span>
          {item.currentJob}
        </div>
      )}

      {/* Metrics */}
      {item.metrics && Object.keys(item.metrics).length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(item.metrics).map(([key, value]) => (
              <div key={key} className="text-xs">
                <span className="text-gray-500">{formatMetricLabel(key)}: </span>
                <span className="font-medium text-gray-700">{value}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Last Updated */}
      {item.lastUpdated && (
        <div className="mt-3 flex items-center gap-1 text-xs text-gray-400">
          {item.status === 'OFFLINE' ? (
            <WifiOff className="h-3 w-3" />
          ) : (
            <Wifi className="h-3 w-3" />
          )}
          <span>{formatLastUpdated(item.lastUpdated)}</span>
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
  };
  return labels[key] || key;
}

function formatLastUpdated(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return '방금 전';
  if (diffMins < 60) return `${diffMins}분 전`;

  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}시간 전`;

  return date.toLocaleDateString('ko-KR', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function StatusGrid({ title, items, columns = 4 }: StatusGridProps) {
  if (!items || items.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        {title && <h3 className="font-semibold text-gray-800 mb-4">{title}</h3>}
        <div className="h-32 flex items-center justify-center text-gray-500">
          설비 데이터가 없습니다
        </div>
      </div>
    );
  }

  // Status summary
  const statusCounts = items.reduce(
    (acc, item) => {
      acc[item.status] = (acc[item.status] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      {title && (
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-800">{title}</h3>
          <div className="flex items-center gap-3 text-xs">
            {Object.entries(statusCounts).map(([status, count]) => {
              const config = getStatusConfig(status);
              return (
                <div key={status} className={`flex items-center gap-1 ${config.color}`}>
                  {config.icon}
                  <span>
                    {config.label}: {count}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
      <div
        className="grid gap-4"
        style={{
          gridTemplateColumns: `repeat(${Math.min(columns, items.length)}, minmax(0, 1fr))`,
        }}
      >
        {items.map((item) => (
          <StatusCard key={item.id} item={item} />
        ))}
      </div>
    </div>
  );
}

export default StatusGrid;
