"use client";

/**
 * Scheduler shared hooks, constants, and utilities
 * Extracted from the monolithic scheduler page for reuse across
 * /scheduler, /scheduler/execute, and /scheduler/settings pages.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useCallback, useMemo } from "react";
import {
  schedulerService,
  SchedulingResult,
  EquipmentAvailability,
} from "@/services/scheduler";
import { ScheduledTaskForGantt } from "@/components/scheduler";
import { downtimeService, downtimeReasonService } from "@/services/downtime";
import { format } from "date-fns";

// ─── Constants ────────────────────────────────────────

export const SOLVER_OPTIONS = [
  {
    value: "OR_TOOLS",
    label: "OR-Tools (정확)",
    description: "최적해, 소규모 문제에 적합",
  },
  {
    value: "GA",
    label: "유전 알고리즘",
    description: "대규모 문제, 균형잡힌 해",
  },
  { value: "SA", label: "담금질 기법", description: "빠른 근사해" },
  { value: "TABU", label: "타부 서치", description: "지역 최적 탈출" },
  { value: "ALNS", label: "ALNS", description: "적응형 최적화" },
];

// ─── Types ────────────────────────────────────────────

export type WorkflowState =
  | "idle"
  | "solving"
  | "comparing"
  | "detail"
  | "approving"
  | "approved";

export type SchedulingMode = "new" | "reschedule" | "full_rebalance";

export interface SolverResult {
  solver_type: string;
  scheduling_result: SchedulingResult;
  statistics: {
    makespan_hours: number;
    makespan_seconds: number;
    machine_utilization: Record<string, number>;
    total_tasks: number;
    solve_time_sec: number;
    objective_value: number;
    weighted_tardiness_sec?: number;
    weighted_completion_sec?: number;
    total_setup_sec?: number;
  };
  timestamp: string;
}

export const SCHEDULING_MODES: {
  value: SchedulingMode;
  label: string;
  description: string;
  include_running: boolean;
  include_scheduled: boolean;
  severity: "info" | "warning" | "danger";
}[] = [
  {
    value: "new",
    label: "신규 수립",
    description: "READY 작업만 대상으로 새 스케줄 생성",
    include_running: false,
    include_scheduled: false,
    severity: "info",
  },
  {
    value: "reschedule",
    label: "재스케줄링",
    description: "기존 스케줄을 포함하여 재배치",
    include_running: false,
    include_scheduled: true,
    severity: "warning",
  },
  {
    value: "full_rebalance",
    label: "전체 재배치",
    description: "진행중 작업까지 포함 전체 재배치",
    include_running: true,
    include_scheduled: true,
    severity: "danger",
  },
];

// ─── Hooks ────────────────────────────────────────────

export function useSchedulerEquipment() {
  return useQuery({
    queryKey: ["scheduler-equipment"],
    queryFn: () => schedulerService.getEquipmentAvailability(),
  });
}

export function useSchedulerWorkOrders() {
  return useQuery({
    queryKey: ["scheduler-work-orders"],
    queryFn: () => schedulerService.getWorkOrdersForScheduling("READY", 100),
  });
}

export function useCurrentSchedule(date: string, enabled: boolean = true) {
  return useQuery({
    queryKey: ["current-schedule", date],
    queryFn: () => schedulerService.getCurrentSchedule({ date, includeRunning: true }),
    enabled,
  });
}

export function useSolveSchedule(onSuccess: (result: SchedulingResult) => void) {
  return useMutation({
    mutationFn: (params: {
      horizon_hours: number;
      include_running: boolean;
      solver_type: string;
      time_limit_sec: number;
    }) => schedulerService.solveSchedule(params),
    onSuccess: (data) => onSuccess(data.scheduling_result),
  });
}

export function useApproveSchedule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (result: SchedulingResult) => schedulerService.approveSchedule(result),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scheduler-work-orders"] });
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      queryClient.invalidateQueries({ queryKey: ["current-schedule"] });
    },
  });
}

export function useDowntimeForGantt(date: string) {
  const dateFrom = `${date}T00:00:00`;
  const dateTo = `${date}T23:59:59`;

  const { data: downtimes, isLoading: loadingDowntimes } = useQuery({
    queryKey: ["downtime-gantt", date],
    queryFn: () =>
      downtimeService.getAll({ date_from: dateFrom, date_to: dateTo, status: "all" }),
  });

  const { data: reasons } = useQuery({
    queryKey: ["downtime-reasons-gantt"],
    queryFn: () => downtimeReasonService.getAll(true),
  });

  const reasonMap = useMemo(() => {
    const map: Record<number, string> = {};
    for (const r of reasons || []) map[r.id] = r.name;
    return map;
  }, [reasons]);

  const tasks = useMemo((): ScheduledTaskForGantt[] => {
    if (!downtimes) return [];
    const dayStart = new Date(dateFrom);

    return downtimes.map((dt) => {
      const startSec = Math.max(
        0,
        (new Date(dt.start_time).getTime() - dayStart.getTime()) / 1000
      );
      const endTime = dt.end_time ? new Date(dt.end_time) : new Date(dateTo);
      const endSec = Math.max(startSec, (endTime.getTime() - dayStart.getTime()) / 1000);

      return {
        wo_id: `DT-${dt.id}`,
        job_id: "",
        op_id: `DT-${dt.id}`,
        machine_id: `EQ-${dt.equipment_id}`,
        start_time: startSec,
        end_time: Math.min(endSec, 86400),
        quantity: 0,
        product_name: reasonMap[dt.reason_id] || dt.remarks || "다운타임",
        status: "DOWNTIME",
      };
    });
  }, [downtimes, reasonMap, dateFrom, dateTo]);

  return { tasks, isLoading: loadingDowntimes };
}

// ─── Utilities ────────────────────────────────────────

/**
 * Convert equipment availability data to Gantt chart tasks.
 * Uses equipment_id in op_id to ensure uniqueness across machines.
 */
export function convertAvailabilityToTasks(
  availability: EquipmentAvailability[],
  horizonStart: string
): ScheduledTaskForGantt[] {
  const tasks: ScheduledTaskForGantt[] = [];
  const dayStart = new Date(horizonStart);

  availability.forEach((eq) => {
    const equipmentId = eq.equipment_id;
    eq.schedule?.forEach((slot, idx) => {
      if (slot.slot_start && slot.slot_end) {
        const startTime =
          (new Date(slot.slot_start).getTime() - dayStart.getTime()) / 1000;
        const endTime =
          (new Date(slot.slot_end).getTime() - dayStart.getTime()) / 1000;
        // Include equipment_id in op_id to avoid duplicate React keys across machines
        const slotIndex = idx + 1;
        const opId = ["OP", equipmentId, slotIndex].join("-");

        tasks.push({
          wo_id: `WO-${slot.work_order_id}`,
          job_id: slot.lot_no || "",
          op_id: opId,
          machine_id: equipmentId,
          start_time: Math.max(0, startTime),
          end_time: Math.max(0, endTime),
          quantity: 1,
          lot_no: slot.lot_no,
          product_name: slot.product,
          status: slot.status,
        });
      }
    });
  });

  return tasks;
}

export function formatSeconds(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}초`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}분`;
  return `${(seconds / 3600).toFixed(1)}시간`;
}

export function formatDateTime(dateStr: string | null | undefined): string {
  if (!dateStr) return "-";
  return format(new Date(dateStr), "yyyy-MM-dd HH:mm");
}
