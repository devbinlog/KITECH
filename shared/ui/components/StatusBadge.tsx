import React from 'react';

type StatusType = 'success' | 'warning' | 'error' | 'info' | 'neutral';

interface StatusBadgeProps {
  status: StatusType | string;
  label?: string;
  size?: 'sm' | 'md';
}

const statusColors: Record<StatusType, string> = {
  success: 'bg-green-100 text-green-800',
  warning: 'bg-yellow-100 text-yellow-800',
  error: 'bg-red-100 text-red-800',
  info: 'bg-blue-100 text-blue-800',
  neutral: 'bg-gray-100 text-gray-800',
};

const statusMapping: Record<string, StatusType> = {
  // Equipment status
  RUN: 'success',
  RUNNING: 'success',
  AVAILABLE: 'success',
  IDLE: 'neutral',
  STOP: 'warning',
  ERROR: 'error',
  ALARM: 'error',
  OFFLINE: 'neutral',
  // Work order status
  READY: 'info',
  PAUSE: 'warning',
  DONE: 'success',
  COMPLETED: 'success',
  CANCELLED: 'neutral',
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  label,
  size = 'md',
}) => {
  const normalizedStatus = status.toUpperCase();
  const statusType = statusMapping[normalizedStatus] || 'neutral';
  const colorClass = statusColors[statusType];

  const sizeClass = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-sm';

  return (
    <span
      className={`inline-flex items-center font-medium rounded-full ${colorClass} ${sizeClass}`}
    >
      {label || status}
    </span>
  );
};
