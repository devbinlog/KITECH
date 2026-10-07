'use client';

/**
 * Traceability Timeline Component
 * Displays LOT history in a timeline format
 */

import { TraceabilityTimelineProps, TraceabilityStep } from '@/types/nlm';
import {
  CheckCircle2,
  Circle,
  Clock,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Package,
} from 'lucide-react';
import { useState } from 'react';

type StatusType = 'DONE' | 'RUNNING' | 'RUN' | 'PENDING' | 'READY' | 'IDLE' | 'ERROR' | 'PAUSE';

const STATUS_CONFIG: Record<StatusType, { label: string; color: string; bgColor: string; icon: React.ReactNode }> = {
  DONE: {
    label: '완료',
    color: 'text-green-600',
    bgColor: 'bg-green-500',
    icon: <CheckCircle2 className="h-5 w-5" />,
  },
  RUNNING: {
    label: '진행중',
    color: 'text-primary-600',
    bgColor: 'bg-primary-500',
    icon: <Clock className="h-5 w-5 animate-pulse" />,
  },
  RUN: {
    label: '진행중',
    color: 'text-primary-600',
    bgColor: 'bg-primary-500',
    icon: <Clock className="h-5 w-5 animate-pulse" />,
  },
  PENDING: {
    label: '대기',
    color: 'text-gray-400',
    bgColor: 'bg-gray-300',
    icon: <Circle className="h-5 w-5" />,
  },
  READY: {
    label: '준비',
    color: 'text-gray-400',
    bgColor: 'bg-gray-300',
    icon: <Circle className="h-5 w-5" />,
  },
  IDLE: {
    label: '대기',
    color: 'text-gray-400',
    bgColor: 'bg-gray-300',
    icon: <Circle className="h-5 w-5" />,
  },
  ERROR: {
    label: '에러',
    color: 'text-red-600',
    bgColor: 'bg-red-500',
    icon: <AlertTriangle className="h-5 w-5" />,
  },
  PAUSE: {
    label: '일시정지',
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-500',
    icon: <Clock className="h-5 w-5" />,
  },
};

function getStatusConfig(status: string) {
  const normalized = status?.toUpperCase() as StatusType;
  return STATUS_CONFIG[normalized] || STATUS_CONFIG.PENDING;
}

function TimelineStep({ step, isLast }: { step: TraceabilityStep; isLast: boolean }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const config = getStatusConfig(step.status);

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('ko-KR', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const calculateDuration = () => {
    if (!step.startTime || !step.endTime) return null;
    const start = new Date(step.startTime);
    const end = new Date(step.endTime);
    const diffMs = end.getTime() - start.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 60) return `${diffMins}분`;
    const hours = Math.floor(diffMins / 60);
    const mins = diffMins % 60;
    return `${hours}시간 ${mins}분`;
  };

  const hasDetails =
    step.parameters || step.qualityData || step.operator;

  return (
    <div className="relative flex gap-4">
      {/* Timeline Line */}
      <div className="flex flex-col items-center">
        <div
          className={`w-8 h-8 rounded-full flex items-center justify-center text-white ${config.bgColor}`}
        >
          {step.sequence}
        </div>
        {!isLast && <div className="w-0.5 flex-1 bg-gray-200 my-2" />}
      </div>

      {/* Content */}
      <div className={`flex-1 pb-6 ${isLast ? '' : ''}`}>
        <div
          className={`rounded-lg border p-4 ${
            step.status === 'RUNNING' ? 'border-primary-300 bg-primary-50' : 'border-gray-200 bg-white'
          }`}
        >
          {/* Header */}
          <div className="flex items-start justify-between">
            <div>
              <h4 className="font-semibold text-gray-800">
                {step.operationName || step.operation}
              </h4>
              <p className="text-sm text-gray-500">{step.equipmentName || step.equipmentId}</p>
            </div>
            <div className={`flex items-center gap-1 ${config.color}`}>
              {config.icon}
              <span className="text-sm font-medium">{config.label}</span>
            </div>
          </div>

          {/* Time Info */}
          <div className="mt-3 flex items-center gap-4 text-sm text-gray-600">
            <div>
              <span className="text-gray-400">시작: </span>
              {formatDateTime(step.startTime)}
            </div>
            {step.endTime && (
              <div>
                <span className="text-gray-400">종료: </span>
                {formatDateTime(step.endTime)}
              </div>
            )}
            {calculateDuration() && (
              <div className="text-primary-600">({calculateDuration()})</div>
            )}
          </div>

          {/* Quantity Info */}
          <div className="mt-2 flex items-center gap-4 text-sm">
            <div className="text-green-600">
              양품: <span className="font-medium">{step.okQty.toLocaleString()}</span>
            </div>
            {step.ngQty > 0 && (
              <div className="text-red-600">
                불량: <span className="font-medium">{step.ngQty.toLocaleString()}</span>
              </div>
            )}
            {step.okQty + step.ngQty > 0 && (
              <div className="text-gray-500">
                수율:{' '}
                <span className="font-medium">
                  {((step.okQty / (step.okQty + step.ngQty)) * 100).toFixed(1)}%
                </span>
              </div>
            )}
          </div>

          {/* Expandable Details */}
          {hasDetails && (
            <>
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="mt-3 flex items-center gap-1 text-sm text-primary-600 hover:text-primary-700"
              >
                {isExpanded ? (
                  <>
                    <ChevronUp className="h-4 w-4" />
                    상세 정보 접기
                  </>
                ) : (
                  <>
                    <ChevronDown className="h-4 w-4" />
                    상세 정보 보기
                  </>
                )}
              </button>

              {isExpanded && (
                <div className="mt-3 pt-3 border-t border-gray-200 space-y-3">
                  {step.operator && (
                    <div className="text-sm">
                      <span className="text-gray-500">작업자: </span>
                      <span className="text-gray-700">{step.operator}</span>
                    </div>
                  )}

                  {step.parameters && Object.keys(step.parameters).length > 0 && (
                    <div>
                      <h5 className="text-sm font-medium text-gray-600 mb-2">공정 파라미터</h5>
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        {Object.entries(step.parameters).map(([key, value]) => (
                          <div key={key} className="flex justify-between bg-gray-50 px-2 py-1 rounded">
                            <span className="text-gray-500">{key}</span>
                            <span className="font-medium text-gray-700">
                              {typeof value === 'number' ? value.toLocaleString() : String(value)}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {step.qualityData && Object.keys(step.qualityData).length > 0 && (
                    <div>
                      <h5 className="text-sm font-medium text-gray-600 mb-2">품질 데이터</h5>
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        {Object.entries(step.qualityData).map(([key, value]) => (
                          <div key={key} className="flex justify-between bg-gray-50 px-2 py-1 rounded">
                            <span className="text-gray-500">{key}</span>
                            <span className="font-medium text-gray-700">
                              {typeof value === 'number' ? value.toLocaleString() : String(value)}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export function TraceabilityTimeline({
  title,
  lotNo,
  product,
  steps,
}: TraceabilityTimelineProps) {
  if (!steps || steps.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        {title && <h3 className="font-semibold text-gray-800 mb-4">{title}</h3>}
        <div className="h-32 flex items-center justify-center text-gray-500">
          추적 이력이 없습니다
        </div>
      </div>
    );
  }

  // Sort steps by sequence
  const sortedSteps = [...steps].sort((a, b) => a.sequence - b.sequence);

  // Calculate summary
  const totalOk = steps.reduce((sum, s) => sum + s.okQty, 0);
  const totalNg = steps.reduce((sum, s) => sum + s.ngQty, 0);
  const completedSteps = steps.filter((s) => s.status === 'DONE').length;
  const hasError = steps.some((s) => s.status === 'ERROR');

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold text-gray-800 text-lg">
            {title || 'LOT 추적 이력'}
          </h3>
          {hasError && (
            <span className="px-2 py-1 bg-red-100 text-red-600 text-xs rounded-full flex items-center gap-1">
              <AlertTriangle className="h-3 w-3" />
              에러 발생
            </span>
          )}
        </div>

        {/* LOT Info */}
        <div className="flex items-center gap-4 text-sm text-gray-600">
          <div className="flex items-center gap-1">
            <Package className="h-4 w-4" />
            <span className="font-medium">{lotNo}</span>
          </div>
          {product && <div>제품: {product}</div>}
        </div>

        {/* Summary */}
        <div className="mt-3 flex items-center gap-6 text-sm">
          <div>
            공정 진행:{' '}
            <span className="font-medium">
              {completedSteps}/{steps.length}
            </span>
          </div>
          <div className="text-green-600">
            총 양품: <span className="font-medium">{totalOk.toLocaleString()}</span>
          </div>
          {totalNg > 0 && (
            <div className="text-red-600">
              총 불량: <span className="font-medium">{totalNg.toLocaleString()}</span>
            </div>
          )}
          {totalOk + totalNg > 0 && (
            <div>
              최종 수율:{' '}
              <span className="font-medium text-primary-600">
                {((totalOk / (totalOk + totalNg)) * 100).toFixed(1)}%
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Timeline */}
      <div>
        {sortedSteps.map((step, index) => (
          <TimelineStep
            key={`${step.sequence}-${step.operation}`}
            step={step}
            isLast={index === sortedSteps.length - 1}
          />
        ))}
      </div>
    </div>
  );
}

export default TraceabilityTimeline;
