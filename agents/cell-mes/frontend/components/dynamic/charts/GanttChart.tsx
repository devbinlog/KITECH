'use client';

/**
 * Gantt Chart Component
 * Displays schedule and availability data in a timeline view
 */

import { useMemo } from 'react';
import { GanttChartProps, EquipmentAvailability, ScheduleSlot } from '@/types/nlm';
import { Calendar, Clock, Activity, AlertTriangle } from 'lucide-react';

const STATUS_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  RUNNING: { bg: 'bg-green-100', border: 'border-green-400', text: 'text-green-700' },
  AVAILABLE: { bg: 'bg-gray-100', border: 'border-gray-300', text: 'text-gray-500' },
  MAINTENANCE: { bg: 'bg-primary-100', border: 'border-primary-400', text: 'text-primary-700' },
  OFFLINE: { bg: 'bg-red-100', border: 'border-red-400', text: 'text-red-700' },
};

function formatTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' });
}

function EquipmentRow({ equipment }: { equipment: EquipmentAvailability }) {
  const schedule = equipment.schedule || [];

  return (
    <div className="flex items-stretch border-b border-gray-200 last:border-b-0">
      {/* Equipment name */}
      <div className="w-32 flex-shrink-0 p-3 bg-gray-50 border-r border-gray-200">
        <div className="font-medium text-sm text-gray-800">{equipment.equipment_name}</div>
        <div className="text-xs text-gray-500">{equipment.equipment_id}</div>
        {equipment.summary && (
          <div className="mt-1 text-xs text-gray-400">
            {equipment.summary.utilization?.toFixed(1)}% 가동
          </div>
        )}
      </div>

      {/* Timeline slots */}
      <div className="flex-1 flex items-center gap-1 p-2 overflow-x-auto">
        {schedule.length > 0 ? (
          schedule.map((slot, idx) => (
            <SlotBlock key={idx} slot={slot} />
          ))
        ) : (
          <div className="text-sm text-gray-400 p-2">스케줄 없음</div>
        )}
      </div>
    </div>
  );
}

function SlotBlock({ slot }: { slot: ScheduleSlot }) {
  const colors = STATUS_COLORS[slot.status] || STATUS_COLORS.AVAILABLE;

  return (
    <div
      className={`rounded px-3 py-2 border ${colors.bg} ${colors.border} min-w-[120px]`}
      title={`${slot.status}: ${formatTime(slot.slot_start)} - ${formatTime(slot.slot_end)}`}
    >
      <div className={`text-xs font-medium ${colors.text}`}>
        {formatTime(slot.slot_start)} - {formatTime(slot.slot_end)}
      </div>
      {slot.lot_no && (
        <div className="text-xs text-gray-600 mt-1 truncate">{slot.lot_no}</div>
      )}
      {slot.product && (
        <div className="text-xs text-gray-500 truncate">{slot.product}</div>
      )}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="h-48 flex flex-col items-center justify-center text-gray-400">
      <Calendar className="h-12 w-12 mb-3 opacity-50" />
      <p className="text-sm">스케줄 데이터가 없습니다</p>
    </div>
  );
}

export function GanttChart({ title, data }: GanttChartProps) {
  // Parse availability data
  const availability = useMemo(() => {
    if (!data) return [];

    // Handle different data structures
    if (Array.isArray(data)) {
      return data as EquipmentAvailability[];
    }
    if (data.availability && Array.isArray(data.availability)) {
      return data.availability;
    }
    if (data.schedule && Array.isArray(data.schedule)) {
      // Convert GanttTask[] to ScheduleSlot[] format
      const scheduleSlots = data.schedule.map((task) => ({
        slot_start: task.startTime,
        slot_end: task.endTime,
        status: 'RUNNING' as const,
        work_order_id: undefined,
        lot_no: task.lotNo,
        product: task.product,
      }));
      
      return [{
        equipment_id: 'all',
        equipment_name: '전체 스케줄',
        schedule: scheduleSlots,
      }];
    }

    return [];
  }, [data]);

  if (!availability || availability.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        {title && <h3 className="font-semibold text-gray-800 mb-4">{title}</h3>}
        <EmptyState />
      </div>
    );
  }

  // Get time range for header
  const timeRange = useMemo(() => {
    let minTime: Date | null = null;
    let maxTime: Date | null = null;

    availability.forEach(eq => {
      eq.schedule?.forEach(slot => {
        const start = new Date(slot.slot_start);
        const end = new Date(slot.slot_end);
        if (!minTime || start < minTime) minTime = start;
        if (!maxTime || end > maxTime) maxTime = end;
      });
    });

    return { start: minTime, end: maxTime };
  }, [availability]);

  return (
    <div className="bg-white rounded-lg border border-gray-200">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-gray-800 flex items-center gap-2">
            <Calendar className="h-5 w-5 text-gray-500" />
            {title || '생산 스케줄'}
          </h3>
          {timeRange.start && timeRange.end && (
            <div className="text-sm text-gray-500 flex items-center gap-1">
              <Clock className="h-4 w-4" />
              {formatDate((timeRange.start as Date).toISOString())}
              {' '}
              {formatTime((timeRange.start as Date).toISOString())} - {formatTime((timeRange.end as Date).toISOString())}
            </div>
          )}
        </div>

        {/* Legend */}
        <div className="mt-3 flex items-center gap-4 text-xs">
          {Object.entries(STATUS_COLORS).map(([status, colors]) => (
            <div key={status} className="flex items-center gap-1">
              <div className={`w-3 h-3 rounded ${colors.bg} ${colors.border} border`}></div>
              <span className="text-gray-600">
                {status === 'RUNNING' ? '가동' :
                 status === 'AVAILABLE' ? '대기' :
                 status === 'MAINTENANCE' ? '정비' : '오프라인'}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Equipment rows */}
      <div className="divide-y divide-gray-100">
        {availability.map((eq) => (
          <EquipmentRow key={eq.equipment_id} equipment={eq} />
        ))}
      </div>

      {/* Summary */}
      <div className="p-3 bg-gray-50 border-t border-gray-200 text-xs text-gray-500">
        총 {availability.length}개 설비
      </div>
    </div>
  );
}

export default GanttChart;
