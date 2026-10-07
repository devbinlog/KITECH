"use client";

import { useState, useMemo } from "react";
import { SchedulerGanttChart, GanttResource } from "@/components/scheduler";
import {
  Calendar,
  Play,
  RefreshCw,
  Server,
} from "lucide-react";
import { format } from "date-fns";
import { useCurrentSchedule, convertAvailabilityToTasks, useDowntimeForGantt } from "@/hooks/useScheduler";

export default function ScheduleStatusPage() {
  const [selectedDate, setSelectedDate] = useState(format(new Date(), "yyyy-MM-dd"));

  const { data: currentSchedule, isLoading: loadingCurrentSchedule } = useCurrentSchedule(selectedDate);
  const { tasks: downtimeTasks } = useDowntimeForGantt(selectedDate);

  // Convert current schedule to Gantt data, merging downtime
  const currentGanttData = useMemo(() => {
    if (!currentSchedule?.availability) return null;

    const horizonStart = `${selectedDate}T00:00:00`;
    const horizonEnd = `${selectedDate}T23:59:59`;
    const scheduleTasks = convertAvailabilityToTasks(currentSchedule.availability, horizonStart);
    const tasks = [...scheduleTasks, ...downtimeTasks];
    const resources: GanttResource[] = currentSchedule.availability.map((a) => ({
      id: a.equipment_id,
      name: a.equipment_name,
      type: a.equipment_type,
    }));

    return { tasks, resources, horizonStart, horizonEnd };
  }, [currentSchedule, selectedDate, downtimeTasks]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-800">스케줄 현황</h1>
        <p className="text-sm text-gray-500">
          일별 생산 스케줄을 간트 차트로 확인합니다
        </p>
      </div>

      {/* Date Picker */}
      <div className="flex items-center gap-4">
        <label className="text-sm font-medium text-gray-700">날짜 선택</label>
        <input
          type="date"
          value={selectedDate}
          onChange={(e) => setSelectedDate(e.target.value)}
          className="px-3 py-2 border rounded-md"
        />
        <button
          onClick={() => setSelectedDate(format(new Date(), "yyyy-MM-dd"))}
          className="btn btn-secondary text-sm"
        >
          오늘
        </button>
      </div>

      {/* Summary Cards */}
      {currentSchedule && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="card">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-primary-100 rounded-lg">
                <Server className="text-primary-600" size={24} />
              </div>
              <div>
                <p className="text-sm text-gray-500">스케줄된 설비</p>
                <p className="text-2xl font-bold">{currentSchedule.summary.total_equipments}</p>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-purple-100 rounded-lg">
                <Calendar className="text-purple-600" size={24} />
              </div>
              <div className="flex items-center gap-2">
                <div>
                  <p className="text-sm text-gray-500 flex items-center gap-1">
                    스케줄된 작업
                    <span className="relative group">
                      <span className="w-3.5 h-3.5 bg-gray-200 text-gray-600 rounded-full text-[10px] flex items-center justify-center cursor-help">?</span>
                      <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-gray-800 text-white text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50">
                        설비와 시간이 배정된 작업 (시작 전)
                      </span>
                    </span>
                  </p>
                  <p className="text-2xl font-bold">{currentSchedule.summary.total_scheduled_orders}</p>
                </div>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-green-100 rounded-lg">
                <Play className="text-green-600" size={24} />
              </div>
              <div>
                <p className="text-sm text-gray-500">진행중</p>
                <p className="text-2xl font-bold text-green-600">{currentSchedule.summary.running_orders}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Gantt Chart */}
      {loadingCurrentSchedule ? (
        <div className="card text-center py-8">
          <RefreshCw className="animate-spin mx-auto mb-2 text-gray-400" size={24} />
          <p className="text-gray-500">로딩 중...</p>
        </div>
      ) : currentGanttData && currentGanttData.tasks.length > 0 ? (
        <SchedulerGanttChart
          title={`${selectedDate} 스케줄 현황`}
          tasks={currentGanttData.tasks}
          resources={currentGanttData.resources}
          horizonStart={currentGanttData.horizonStart}
          horizonEnd={currentGanttData.horizonEnd}
        />
      ) : (
        <div className="card text-center py-12">
          <Calendar className="mx-auto mb-3 text-gray-300" size={48} />
          <p className="text-gray-500 text-lg mb-2">스케줄된 작업지시가 없습니다</p>
          <p className="text-gray-400 text-sm">
            &apos;스케줄 실행&apos; 페이지에서 스케줄링을 실행하세요
          </p>
        </div>
      )}
    </div>
  );
}
