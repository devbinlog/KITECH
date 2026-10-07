'use client';

/**
 * Scheduler Gantt Chart Component
 * Displays schedule timeline with equipment rows and time-based task blocks
 */

import { useMemo, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { format, addHours, differenceInMinutes } from 'date-fns';
import { ko } from 'date-fns/locale';
import { Clock, Calendar, ExternalLink } from 'lucide-react';
import { Tooltip } from '@/components/ui/Tooltip';

export interface ScheduledTaskForGantt {
  wo_id: string;
  job_id: string;
  op_id: string;
  machine_id: string;
  start_time: number;  // seconds from horizon start
  end_time: number;
  quantity: number;
  lot_no?: string;
  product_name?: string;
  status?: string;  // READY, RUNNING, DONE, PAUSE, ERROR
}

export interface GanttResource {
  id: string;
  name: string;
  type?: string;
}

export interface SchedulerGanttChartProps {
  title: string;
  tasks: ScheduledTaskForGantt[];
  resources: GanttResource[];
  horizonStart: string;  // ISO datetime
  horizonEnd: string;
  onTaskClick?: (task: ScheduledTaskForGantt) => void;
}

const HOUR_WIDTH = 60;  // 1 hour = 60px
const ROW_HEIGHT = 50;

const STATUS_COLORS = {
  scheduled: 'bg-primary-200 border-primary-400 text-primary-800',    // READY
  running: 'bg-green-200 border-green-400 text-green-800',   // RUNNING
  completed: 'bg-gray-200 border-gray-400 text-gray-600',    // DONE
  paused: 'bg-yellow-200 border-yellow-400 text-yellow-800', // PAUSE
  error: 'bg-red-200 border-red-400 text-red-800',           // ERROR
  downtime: 'border-red-400 text-red-800',                   // DOWNTIME (bg via inline style)
};

const DOWNTIME_BG_STYLE = {
  background: `repeating-linear-gradient(45deg, transparent, transparent 3px, rgba(239,68,68,0.25) 3px, rgba(239,68,68,0.25) 6px), #FEE2E2`,
};

const isDowntimeTask = (task: ScheduledTaskForGantt) =>
  task.status === 'DOWNTIME' || task.wo_id.startsWith('DT-');

// Get color based on work order status
const getTaskColor = (status?: string) => {
  switch (status) {
    case 'RUNNING': return STATUS_COLORS.running;
    case 'DONE': return STATUS_COLORS.completed;
    case 'PAUSE': return STATUS_COLORS.paused;
    case 'ERROR': return STATUS_COLORS.error;
    case 'DOWNTIME': return STATUS_COLORS.downtime;
    case 'SCHEDULED': return STATUS_COLORS.scheduled;
    default: return STATUS_COLORS.scheduled;  // READY or undefined
  }
};

// Task tooltip content component
function TaskTooltipContent({ task, resource, horizonStart }: {
  task: ScheduledTaskForGantt;
  resource?: GanttResource;
  horizonStart: Date;
}) {
  const startTime = new Date(horizonStart.getTime() + task.start_time * 1000);
  const endTime = new Date(horizonStart.getTime() + task.end_time * 1000);
  const durationMin = (task.end_time - task.start_time) / 60;
  const durationHours = Math.floor(durationMin / 60);
  const durationMins = Math.round(durationMin % 60);
  const isDt = isDowntimeTask(task);
  const isOngoingDt = isDt && task.end_time >= 86340;

  return (
    <div className="space-y-1.5 text-left">
      <div className="font-semibold text-white border-b border-gray-700 pb-1.5 mb-1.5">
        {isDt ? (isOngoingDt ? '진행중 다운타임' : '다운타임') : task.wo_id}
      </div>
      <div className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1">
        {!isDt && task.lot_no && (
          <>
            <span className="text-gray-400">Lot No:</span>
            <span>{task.lot_no}</span>
          </>
        )}
        {task.product_name && (
          <>
            <span className="text-gray-400">{isDt ? '사유:' : '제품:'}</span>
            <span>{task.product_name}</span>
          </>
        )}
        <span className="text-gray-400">설비:</span>
        <span>{resource?.name || task.machine_id}</span>
        <span className="text-gray-400">시작:</span>
        <span>{format(startTime, 'MM/dd HH:mm', { locale: ko })}</span>
        <span className="text-gray-400">종료:</span>
        <span>{isOngoingDt ? '진행중' : format(endTime, 'MM/dd HH:mm', { locale: ko })}</span>
        <span className="text-gray-400">소요:</span>
        <span>{isOngoingDt ? '진행중' : `${durationHours > 0 ? `${durationHours}시간 ` : ''}${durationMins}분`}</span>
        {!isDt && (
          <>
            <span className="text-gray-400">수량:</span>
            <span>{task.quantity}개</span>
          </>
        )}
        <span className="text-gray-400">상태:</span>
        <span className={
          isDt ? 'text-red-400' :
          task.status === 'RUNNING' ? 'text-green-400' :
          task.status === 'DONE' ? 'text-gray-400' :
          task.status === 'PAUSE' ? 'text-yellow-400' :
          task.status === 'ERROR' ? 'text-red-400' :
          'text-primary-400'
        }>
          {isDt ? (isOngoingDt ? '진행중' : '정지') :
           task.status === 'RUNNING' ? '진행중' :
           task.status === 'DONE' ? '완료' :
           task.status === 'PAUSE' ? '일시정지' :
           task.status === 'ERROR' ? '에러' :
           '예정'}
        </span>
      </div>
      {!isDt && (
        <div className="text-gray-400 text-[10px] pt-1 border-t border-gray-700 mt-1">
          클릭하여 작업지시 보기
        </div>
      )}
    </div>
  );
}

export function SchedulerGanttChart({
  title,
  tasks,
  resources,
  horizonStart,
  horizonEnd,
  onTaskClick,
}: SchedulerGanttChartProps) {
  const router = useRouter();

  // Handle task click - navigate to work orders page
  const handleTaskClick = useCallback((task: ScheduledTaskForGantt) => {
    // Call the provided callback if any
    onTaskClick?.(task);
    // Navigate to orders page with lot_no highlight (orders page matches on lot_no)
    const highlightKey = task.lot_no || task.wo_id;
    router.push(`/production/orders?view=all&highlight=${encodeURIComponent(highlightKey)}`);
  }, [onTaskClick, router]);

  // Calculate time range
  const timeRange = useMemo(() => {
    const start = new Date(horizonStart);
    const end = new Date(horizonEnd);
    const hours = differenceInMinutes(end, start) / 60;
    return { start, end, hours: Math.max(hours, 1) };
  }, [horizonStart, horizonEnd]);

  // Generate time markers (hourly)
  const timeMarkers = useMemo(() => {
    const markers: Date[] = [];
    let current = new Date(timeRange.start);
    while (current < timeRange.end) {
      markers.push(new Date(current));
      current = addHours(current, 1);
    }
    return markers;
  }, [timeRange]);

  // Group tasks by resource (machine_id)
  const tasksByResource = useMemo(() => {
    const map = new Map<string, ScheduledTaskForGantt[]>();
    resources.forEach(r => map.set(r.id, []));

    tasks.forEach(task => {
      const resourceTasks = map.get(task.machine_id) || [];
      resourceTasks.push(task);
      map.set(task.machine_id, resourceTasks);
    });

    return map;
  }, [tasks, resources]);

  // Calculate task position and width
  const getTaskStyle = (task: ScheduledTaskForGantt) => {
    const startMinutes = task.start_time / 60;
    const durationMinutes = (task.end_time - task.start_time) / 60;
    const left = (startMinutes / 60) * HOUR_WIDTH;
    const width = Math.max((durationMinutes / 60) * HOUR_WIDTH, 40);  // minimum 40px

    return {
      left: `${left}px`,
      width: `${width}px`,
    };
  };

  const totalWidth = Math.max(timeRange.hours * HOUR_WIDTH, 200);

  if (resources.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
        <Calendar className="mx-auto h-12 w-12 text-gray-300 mb-3" />
        <p className="text-gray-500">표시할 설비가 없습니다</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 flex items-center justify-between bg-gray-50">
        <h3 className="font-semibold text-gray-800 flex items-center gap-2">
          <Calendar className="h-5 w-5 text-gray-500" />
          {title}
        </h3>
        <span className="text-sm text-gray-500 flex items-center gap-1">
          <Clock className="h-4 w-4" />
          {format(timeRange.start, 'MM/dd HH:mm', { locale: ko })} ~
          {format(timeRange.end, 'MM/dd HH:mm', { locale: ko })}
        </span>
      </div>

      {/* Gantt Content */}
      <div className="overflow-auto" style={{ maxHeight: '500px' }}>
        <div style={{ minWidth: `${200 + totalWidth}px` }}>
          {/* Time Header */}
          <div className="flex sticky top-0 bg-white z-10 border-b border-gray-200">
            <div className="w-[200px] flex-shrink-0 border-r border-gray-200 p-2 bg-gray-50">
              <span className="text-sm font-medium text-gray-600">설비</span>
            </div>
            <div className="flex">
              {timeMarkers.map((time, idx) => (
                <div
                  key={idx}
                  className="border-r border-gray-200 text-center text-xs text-gray-500 py-2 bg-gray-50"
                  style={{ width: `${HOUR_WIDTH}px` }}
                >
                  {format(time, 'HH:mm')}
                </div>
              ))}
            </div>
          </div>

          {/* Resource Rows */}
          {resources.map((resource) => (
            <div key={resource.id} className="flex" style={{ height: `${ROW_HEIGHT}px` }}>
              {/* Resource Label */}
              <div className="w-[200px] flex-shrink-0 border-r border-b border-gray-200 p-2 bg-gray-50 flex flex-col justify-center">
                <div className="font-medium text-sm text-gray-800 truncate">
                  {resource.name}
                </div>
                {resource.type && (
                  <div className="text-xs text-gray-500">{resource.type}</div>
                )}
              </div>

              {/* Timeline */}
              <div
                className="relative border-b border-gray-100 bg-white"
                style={{ width: `${totalWidth}px` }}
              >
                {/* Hour grid lines */}
                {timeMarkers.map((_, idx) => (
                  <div
                    key={idx}
                    className="absolute top-0 bottom-0 border-r border-gray-100"
                    style={{ left: `${idx * HOUR_WIDTH}px` }}
                  />
                ))}

                {/* Tasks */}
                {(tasksByResource.get(resource.id) || []).map((task, idx) => {
                  const isDt = isDowntimeTask(task);
                  const isOngoingDt = isDt && task.end_time >= 86340; // 23:59:00 — ongoing DT extends to end of day
                  return (
                    <Tooltip
                      key={`${task.wo_id}-${task.op_id}-${idx}`}
                      content={
                        <TaskTooltipContent
                          task={task}
                          resource={resource}
                          horizonStart={timeRange.start}
                        />
                      }
                      position="top"
                      delay={0}
                    >
                      <div
                        className={`absolute top-1 rounded border px-2 py-1 text-xs transition-all
                          ${isDt ? 'cursor-default z-[1]' : 'cursor-pointer z-[5] hover:shadow-md hover:z-20 hover:scale-105'}
                          ${getTaskColor(task.status)}`}
                        style={{
                          ...getTaskStyle(task),
                          height: `${ROW_HEIGHT - 8}px`,
                          ...(isDt ? DOWNTIME_BG_STYLE : {}),
                          ...(isOngoingDt ? { opacity: 0.35, pointerEvents: 'none' as const } : {}),
                        }}
                        onClick={isDt ? undefined : () => handleTaskClick(task)}
                      >
                        <div className="font-medium truncate flex items-center gap-1">
                          {isDt ? (isOngoingDt ? '진행중 다운타임' : '다운타임') : task.wo_id}
                          {!isDt && <ExternalLink size={10} className="opacity-50" />}
                        </div>
                        <div className="truncate opacity-75">
                          {isDt ? (task.product_name || '') : (task.lot_no || task.product_name || task.job_id)}
                        </div>
                      </div>
                    </Tooltip>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="p-3 bg-gray-50 border-t border-gray-200 flex items-center justify-between text-xs text-gray-500">
        <span>총 {resources.length}개 설비, {tasks.filter(t => !isDowntimeTask(t)).length}개 작업{tasks.some(t => isDowntimeTask(t)) ? `, ${tasks.filter(t => isDowntimeTask(t)).length}개 다운타임` : ''}</span>
        <div className="flex gap-3">
          <span className="flex items-center gap-1">
            <div className="w-3 h-3 rounded bg-primary-200 border border-primary-400" />
            예정
          </span>
          <span className="flex items-center gap-1">
            <div className="w-3 h-3 rounded bg-green-200 border border-green-400" />
            진행중
          </span>
          <span className="flex items-center gap-1">
            <div className="w-3 h-3 rounded bg-gray-200 border border-gray-400" />
            완료
          </span>
          <span className="flex items-center gap-1">
            <div className="w-3 h-3 rounded bg-yellow-200 border border-yellow-400" />
            일시정지
          </span>
          <span className="flex items-center gap-1">
            <div className="w-3 h-3 rounded border border-red-400" style={DOWNTIME_BG_STYLE} />
            다운타임
          </span>
        </div>
      </div>
    </div>
  );
}

export default SchedulerGanttChart;
