'use client';

/**
 * KPI Card Component
 * Displays a single KPI metric with optional trend indicator
 */

import {
  TrendingUp,
  TrendingDown,
  Minus,
  Activity,
  Package,
  CheckCircle,
  AlertTriangle,
  Percent,
  BarChart3,
  Clipboard,
} from 'lucide-react';
import { KPICardProps } from '@/types/nlm';

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  activity: Activity,
  package: Package,
  check: CheckCircle,
  'check-circle': CheckCircle,
  alert: AlertTriangle,
  percent: Percent,
  chart: BarChart3,
  clipboard: Clipboard,
  'trending-up': TrendingUp,
  'trending-down': TrendingDown,
};

const colorMap: Record<string, { bg: string; text: string; icon: string }> = {
  blue: { bg: 'bg-primary-50', text: 'text-primary-600', icon: 'text-primary-500' },
  green: { bg: 'bg-green-50', text: 'text-green-600', icon: 'text-green-500' },
  amber: { bg: 'bg-amber-50', text: 'text-amber-600', icon: 'text-amber-500' },
  red: { bg: 'bg-red-50', text: 'text-red-600', icon: 'text-red-500' },
  gray: { bg: 'bg-gray-50', text: 'text-gray-600', icon: 'text-gray-500' },
};

export function KPICard({
  title,
  value,
  unit,
  icon,
  trend,
  trendDirection,
  target,
  color = 'blue',
}: KPICardProps) {
  const IconComponent = icon ? iconMap[icon] || Activity : Activity;
  const colors = colorMap[color] || colorMap.blue;

  const TrendIcon =
    trendDirection === 'up'
      ? TrendingUp
      : trendDirection === 'down'
        ? TrendingDown
        : Minus;

  const trendColor =
    trendDirection === 'up'
      ? 'text-green-500'
      : trendDirection === 'down'
        ? 'text-red-500'
        : 'text-gray-400';

  const isAtTarget = target !== undefined && Number(value) >= target;

  return (
    <div className={`rounded-lg p-4 ${colors.bg} border border-gray-100`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-gray-500 mb-1">{title}</p>
          <div className="flex items-baseline gap-1">
            <span className={`text-2xl font-bold ${colors.text}`}>
              {typeof value === 'number' ? value.toLocaleString() : value}
            </span>
            {unit && <span className="text-sm text-gray-500">{unit}</span>}
          </div>

          {/* Trend indicator */}
          {trend && (
            <div className={`flex items-center gap-1 mt-2 text-sm ${trendColor}`}>
              <TrendIcon className="h-4 w-4" />
              <span>{trend}</span>
            </div>
          )}

          {/* Target indicator */}
          {target !== undefined && (
            <div className="mt-2 text-xs text-gray-400">
              목표: {target}
              {unit}{' '}
              {isAtTarget ? (
                <span className="text-green-500">달성</span>
              ) : (
                <span className="text-amber-500">미달</span>
              )}
            </div>
          )}
        </div>

        <div className={`p-2 rounded-lg ${colors.bg}`}>
          <IconComponent className={`h-6 w-6 ${colors.icon}`} />
        </div>
      </div>
    </div>
  );
}

export default KPICard;
