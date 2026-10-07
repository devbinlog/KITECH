"use client";

import { useState, useMemo, useCallback, useEffect, useRef } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { schedulerService, SchedulingResult, CurrentScheduleResponse } from "@/services/scheduler";
import { JsonModal } from "@/components/scheduler";
import {
  Play,
  RefreshCw,
  CheckCircle,
  Clock,
  Server,
  FileJson,
  XCircle,
  AlertCircle,
  Zap,
  ExternalLink,
  Calendar,
  BarChart3,
  Shield,
  AlertTriangle,
  StopCircle,
  ArrowRight,
  Layers,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { format } from "date-fns";
import {
  SOLVER_OPTIONS,
  WorkflowState,
  SchedulingMode,
  SolverResult,
  SCHEDULING_MODES,
  useSchedulerEquipment,
  useSchedulerWorkOrders,
  formatSeconds,
  formatDateTime,
} from "@/hooks/useScheduler";

// ─── Helpers ──────────────────────────────────────────

function calcAvgUtilization(utilization: Record<string, number>): number {
  const vals = Object.values(utilization || {});
  if (vals.length === 0) return 0;
  return vals.reduce((a, b) => a + b, 0) / vals.length;
}

function formatHoursMinutes(seconds: number): string {
  if (seconds <= 0) return "-";
  const h = Math.floor(seconds / 3600);
  const m = Math.round((seconds % 3600) / 60);
  if (h === 0) return `${m}분`;
  return `${h}시간 ${m}분`;
}

// ─── Component ────────────────────────────────────────

export default function ScheduleExecutePage() {
  const queryClient = useQueryClient();
  const router = useRouter();

  // B-6: Load saved settings from localStorage
  const [horizonHours, setHorizonHours] = useState(24);
  const [solverType, setSolverType] = useState("OR_TOOLS");
  const [timeLimitSec, setTimeLimitSec] = useState(60);
  const [lotSize, setLotSize] = useState(1);
  const [amrTransferTimeSec, setAmrTransferTimeSec] = useState(60);

  // B-2: Mode selection (replaces includeRunning checkbox)
  const [schedulingMode, setSchedulingMode] = useState<SchedulingMode>("new");

  // B-3: Multi-solver comparison state
  const [workflowState, setWorkflowState] = useState<WorkflowState>("idle");
  const [results, setResults] = useState<SolverResult[]>([]);
  const [selectedResult, setSelectedResult] = useState<SolverResult | null>(null);
  const [approvalResult, setApprovalResult] = useState<any>(null);

  // B-5: Existing schedule baseline
  const [currentBaseline, setCurrentBaseline] = useState<{
    makespan_seconds: number;
    avg_utilization: number;
    total_tasks: number;
  } | null>(null);

  // B-4: All-solver comparison progress
  const [solveProgress, setSolveProgress] = useState<{ current: number; total: number } | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const solvingRef = useRef(false);

  // Modal state
  const [showJsonModal, setShowJsonModal] = useState(false);
  const [jsonModalTitle, setJsonModalTitle] = useState("");
  const [jsonModalData, setJsonModalData] = useState<any>(null);

  // Load equipment availability
  const { data: equipmentData, isLoading: loadingEquipment } = useSchedulerEquipment();

  // Load work orders for scheduling
  const { data: workOrdersData, isLoading: loadingOrders, refetch: refetchOrders } = useSchedulerWorkOrders();

  // B-6: Load settings from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem("scheduler-settings");
      if (stored) {
        const parsed = JSON.parse(stored);
        if (parsed.defaultHorizonHours) setHorizonHours(parsed.defaultHorizonHours);
        if (parsed.defaultSolver) setSolverType(parsed.defaultSolver);
        if (parsed.timeLimitSec) setTimeLimitSec(parsed.timeLimitSec);
        if (parsed.defaultMode) setSchedulingMode(parsed.defaultMode);
        if (parsed.lotSize) setLotSize(parsed.lotSize);
        if (parsed.amrTransferTimeSec) setAmrTransferTimeSec(parsed.amrTransferTimeSec);
      }
    } catch {
      // ignore parse error
    }
  }, []);

  // Get mode config
  const modeConfig = useMemo(
    () => SCHEDULING_MODES.find((m) => m.value === schedulingMode) || SCHEDULING_MODES[0],
    [schedulingMode]
  );

  // B-5: Fetch existing schedule baseline when entering comparing state
  const fetchBaseline = useCallback(async () => {
    try {
      const today = format(new Date(), "yyyy-MM-dd");
      const data: CurrentScheduleResponse = await schedulerService.getCurrentSchedule({
        date: today,
        includeRunning: true,
      });
      if (data?.availability) {
        let maxEnd = 0;
        let totalRunning = 0;
        let totalSlots = 0;
        data.availability.forEach((eq) => {
          eq.schedule?.forEach((slot) => {
            if (slot.slot_start && slot.slot_end) {
              const end = new Date(slot.slot_end).getTime();
              const start = new Date(slot.slot_start).getTime();
              if (end > maxEnd) maxEnd = end;
              if (slot.status === "RUNNING" || slot.status === "READY" || slot.status === "DONE" || slot.status === "SCHEDULED") {
                totalRunning += (end - start) / 1000;
              }
              totalSlots += (end - start) / 1000;
            }
          });
        });
        const dayStart = new Date(`${today}T00:00:00`).getTime();
        const makespan = maxEnd > dayStart ? (maxEnd - dayStart) / 1000 : 0;
        const utilization = totalSlots > 0 ? (totalRunning / totalSlots) * 100 : 0;
        setCurrentBaseline({
          makespan_seconds: makespan,
          avg_utilization: utilization,
          total_tasks: data.summary.total_scheduled_orders,
        });
      }
    } catch {
      setCurrentBaseline(null);
    }
  }, []);

  // Single solve
  const handleSolve = useCallback(async () => {
    if (solvingRef.current) return;
    solvingRef.current = true;
    setWorkflowState("solving");
    setSolveProgress(null);
    try {
      const data = await schedulerService.solveSchedule({
        horizon_hours: horizonHours,
        include_running: modeConfig.include_running,
        include_scheduled: modeConfig.include_scheduled,
        solver_type: solverType,
        time_limit_sec: timeLimitSec,
        lot_size: lotSize,
        amr_transfer_time_sec: amrTransferTimeSec,
      });
      const newResult: SolverResult = {
        solver_type: solverType,
        scheduling_result: data.scheduling_result,
        statistics: {
          makespan_hours: data.scheduling_result.statistics.makespan_hours,
          makespan_seconds: data.scheduling_result.statistics.makespan_seconds,
          machine_utilization: data.scheduling_result.statistics.machine_utilization,
          total_tasks: data.scheduling_result.statistics.total_tasks,
          solve_time_sec: data.scheduling_result.statistics.solve_time_sec,
          objective_value: data.scheduling_result.statistics.objective_value,
          weighted_tardiness_sec: data.scheduling_result.statistics.weighted_tardiness_sec,
          weighted_completion_sec: data.scheduling_result.statistics.weighted_completion_sec,
          total_setup_sec: data.scheduling_result.statistics.total_setup_sec,
        },
        timestamp: new Date().toISOString(),
      };
      // Deduplicate: replace existing result for same solver type
      setResults((prev) => {
        const filtered = prev.filter((r) => r.solver_type !== solverType);
        return [...filtered, newResult];
      });
      setWorkflowState("comparing");
      fetchBaseline();
    } catch (error: any) {
      alert(`스케줄링 실패: ${error.response?.data?.detail || error.message}`);
      setWorkflowState(results.length > 0 ? "comparing" : "idle");
    } finally {
      solvingRef.current = false;
    }
  }, [horizonHours, modeConfig, solverType, timeLimitSec, lotSize, amrTransferTimeSec, fetchBaseline, results.length]);

  // B-4: All-solver comparison (sequential)
  const handleSolveAll = useCallback(async () => {
    if (solvingRef.current) return;
    solvingRef.current = true;
    setWorkflowState("solving");
    const controller = new AbortController();
    abortRef.current = controller;
    const solvers = SOLVER_OPTIONS.map((s) => s.value);
    setSolveProgress({ current: 0, total: solvers.length });
    const failedSolvers: string[] = [];

    fetchBaseline();

    try {
      for (let i = 0; i < solvers.length; i++) {
        if (controller.signal.aborted) break;
        setSolveProgress({ current: i, total: solvers.length });
        try {
          const data = await schedulerService.solveSchedule({
            horizon_hours: horizonHours,
            include_running: modeConfig.include_running,
            include_scheduled: modeConfig.include_scheduled,
            solver_type: solvers[i],
            time_limit_sec: timeLimitSec,
            lot_size: lotSize,
            amr_transfer_time_sec: amrTransferTimeSec,
            signal: controller.signal,
          });
          if (controller.signal.aborted) break;
          const newResult: SolverResult = {
            solver_type: solvers[i],
            scheduling_result: data.scheduling_result,
            statistics: {
              makespan_hours: data.scheduling_result.statistics.makespan_hours,
              makespan_seconds: data.scheduling_result.statistics.makespan_seconds,
              machine_utilization: data.scheduling_result.statistics.machine_utilization,
              total_tasks: data.scheduling_result.statistics.total_tasks,
              solve_time_sec: data.scheduling_result.statistics.solve_time_sec,
              objective_value: data.scheduling_result.statistics.objective_value,
              weighted_tardiness_sec: data.scheduling_result.statistics.weighted_tardiness_sec,
              weighted_completion_sec: data.scheduling_result.statistics.weighted_completion_sec,
              total_setup_sec: data.scheduling_result.statistics.total_setup_sec,
            },
            timestamp: new Date().toISOString(),
          };
          // Deduplicate: replace existing result for same solver type
          setResults((prev) => {
            const filtered = prev.filter((r) => r.solver_type !== solvers[i]);
            return [...filtered, newResult];
          });
        } catch {
          // Skip failed solver, track for error reporting
          failedSolvers.push(solvers[i]);
        }
      }
      setSolveProgress(null);
      abortRef.current = null;
      setResults((prev) => {
        if (prev.length === 0 && failedSolvers.length > 0) {
          alert(`모든 솔버가 실패했습니다. 스케줄 대상 작업지시가 있는지 확인해주세요.\n실패한 솔버: ${failedSolvers.join(", ")}`);
        }
        setWorkflowState(prev.length > 0 ? "comparing" : "idle");
        return prev;
      });
    } finally {
      solvingRef.current = false;
    }
  }, [horizonHours, modeConfig, timeLimitSec, lotSize, amrTransferTimeSec, fetchBaseline]);

  const handleAbortSolveAll = useCallback(() => {
    abortRef.current?.abort();
    setSolveProgress(null);
    setWorkflowState(results.length > 0 ? "comparing" : "idle");
  }, [results.length]);

  // Select a result for detail view
  const handleSelectResult = useCallback((result: SolverResult) => {
    setSelectedResult(result);
    setWorkflowState("detail");
  }, []);

  // Approve selected result
  const approveMutation = useMutation({
    mutationFn: (result: SchedulingResult) => schedulerService.approveSchedule(result),
    onSuccess: (data) => {
      setApprovalResult(data);
      setWorkflowState("approved");
      queryClient.invalidateQueries({ queryKey: ["scheduler-work-orders"] });
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      queryClient.invalidateQueries({ queryKey: ["current-schedule"] });
      // W1: Invalidate dashboard queries that depend on order data
      queryClient.invalidateQueries({ queryKey: ["dashboard-orders-stats"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-orders-display"] });
      // W2: Reset selected result and results after 3s to clean up approval state
      setTimeout(() => {
        setSelectedResult(null);
        setResults([]);
      }, 3000);
    },
    onError: (error: any) => {
      alert(`승인 실패: ${error.response?.data?.detail || error.message}`);
      setWorkflowState("detail");
    },
  });

  const handleApprove = useCallback(() => {
    if (!selectedResult) return;

    const taskCount = selectedResult.scheduling_result.scheduled_tasks.length;

    // B-2: Mode-specific warning dialogs
    if (schedulingMode === "full_rebalance") {
      if (!window.confirm(`[경고] 전체 재배치 모드입니다.\n진행중 작업을 포함한 ${taskCount}개 작업이 재배치됩니다.\n현장 작업자에게 알림이 필요합니다.\n\n정말 승인하시겠습니까?`)) {
        return;
      }
    } else if (schedulingMode === "reschedule") {
      if (!window.confirm(`[주의] 재스케줄링 모드입니다.\n기존 스케줄이 새 결과(${taskCount}개 작업)로 덮어씌워집니다.\n\n승인하시겠습니까?`)) {
        return;
      }
    } else {
      if (!window.confirm(`${taskCount}개 작업의 계획시간이 업데이트됩니다. 승인하시겠습니까?`)) {
        return;
      }
    }

    setWorkflowState("approving");
    approveMutation.mutate(selectedResult.scheduling_result);
  }, [selectedResult, schedulingMode, approveMutation]);

  // Back to comparing from detail
  const handleBackToCompare = useCallback(() => {
    setSelectedResult(null);
    setWorkflowState("comparing");
  }, []);

  // Cancel all → idle
  const handleCancel = useCallback(() => {
    setResults([]);
    setSelectedResult(null);
    setApprovalResult(null);
    setCurrentBaseline(null);
    setWorkflowState("idle");
  }, []);

  // Reset results only (stay in idle to rerun)
  const handleResetResults = useCallback(() => {
    setResults([]);
    setSelectedResult(null);
    setCurrentBaseline(null);
    setWorkflowState("idle");
  }, []);

  const showJson = useCallback((data: any, title: string) => {
    setJsonModalData(data);
    setJsonModalTitle(title);
    setShowJsonModal(true);
  }, []);

  // ─── Comparison Table Helpers ──────────────────────

  const comparisonKPIs = useMemo(() => {
    if (results.length === 0) return null;

    const kpis = results.map((r) => ({
      solver: r.solver_type,
      makespan: r.statistics.makespan_seconds,
      utilization: calcAvgUtilization(r.statistics.machine_utilization),
      tasks: r.statistics.total_tasks,
      solveTime: r.statistics.solve_time_sec,
      objective: r.statistics.objective_value,
      // Lexicographic 컴포넌트 (납기 → 우선순위 → makespan → 셋업)
      tardiness: r.statistics.weighted_tardiness_sec ?? r.statistics.objective_value,
      completion: r.statistics.weighted_completion_sec ?? 0,
      setup: r.statistics.total_setup_sec ?? 0,
    }));

    // Best values (min for makespan/solveTime/objective/tardiness/completion/setup, max for utilization/tasks)
    const bestMakespan = Math.min(...kpis.map((k) => k.makespan));
    const bestUtilization = Math.max(...kpis.map((k) => k.utilization));
    const bestTasks = Math.max(...kpis.map((k) => k.tasks));
    const bestSolveTime = Math.min(...kpis.map((k) => k.solveTime));
    const bestObjective = Math.min(...kpis.map((k) => k.objective));
    const bestTardiness = Math.min(...kpis.map((k) => k.tardiness));
    const bestCompletion = Math.min(...kpis.map((k) => k.completion));
    const bestSetup = Math.min(...kpis.map((k) => k.setup));

    return {
      kpis, bestMakespan, bestUtilization, bestTasks, bestSolveTime,
      bestObjective, bestTardiness, bestCompletion, bestSetup,
    };
  }, [results]);

  // Status display
  const statusDisplay = useMemo(() => {
    const statusMap: Record<WorkflowState, { text: string; color: string }> = {
      idle: { text: "대기", color: "bg-gray-100 text-gray-800" },
      solving: { text: "실행중", color: "bg-primary-100 text-primary-800" },
      comparing: { text: "비교중", color: "bg-yellow-100 text-yellow-800" },
      detail: { text: "검토중", color: "bg-yellow-100 text-yellow-800" },
      approving: { text: "승인중", color: "bg-purple-100 text-purple-800" },
      approved: { text: "승인완료", color: "bg-green-100 text-green-800" },
    };
    return statusMap[workflowState];
  }, [workflowState]);

  const isIdle = workflowState === "idle";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">스케줄 실행</h1>
          <p className="text-sm text-gray-500">
            솔버를 실행하고 결과를 검토/승인합니다
          </p>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${statusDisplay.color}`}>
          {statusDisplay.text}
        </span>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Equipment Status */}
        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-primary-100 rounded-lg">
              <Server className="text-primary-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-500">가용 설비</p>
              <p className="text-2xl font-bold">
                {loadingEquipment ? "-" : equipmentData?.count || 0}
              </p>
            </div>
          </div>
          <button
            onClick={() => equipmentData && showJson(equipmentData.machines, "설비 데이터")}
            className="mt-3 text-sm text-primary-600 hover:underline flex items-center gap-1"
            disabled={!equipmentData}
          >
            <FileJson size={14} /> JSON 보기
          </button>
        </div>

        {/* Work Orders Status */}
        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-green-100 rounded-lg">
              <Clock className="text-green-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-500 flex items-center gap-1">
                스케줄 대상
                <span className="relative group">
                  <span className="w-3.5 h-3.5 bg-gray-200 text-gray-600 rounded-full text-[10px] flex items-center justify-center cursor-help">?</span>
                  <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-gray-800 text-white text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50">
                    이번 스케줄링 실행에 포함될 작업
                  </span>
                </span>
              </p>
              <p className="text-2xl font-bold">
                {loadingOrders ? "-" : workOrdersData?.count || 0}
              </p>
            </div>
          </div>
          <button
            onClick={() => workOrdersData && showJson(workOrdersData.work_orders, "작업지시 데이터")}
            className="mt-3 text-sm text-green-600 hover:underline flex items-center gap-1"
            disabled={!workOrdersData}
          >
            <FileJson size={14} /> JSON 보기
          </button>
        </div>

        {/* Scheduling Status */}
        <div className="card">
          <div className="flex items-center gap-3">
            <div className={`p-3 rounded-lg ${results.length > 0 ? "bg-purple-100" : "bg-gray-100"}`}>
              <Calendar className={results.length > 0 ? "text-purple-600" : "text-gray-400"} size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-500">스케줄 결과</p>
              <p className="text-2xl font-bold">
                {results.length > 0 ? `${results.length}개 솔버 결과` : "-"}
              </p>
            </div>
          </div>
          {results.length > 0 && (
            <button
              onClick={() => showJson(results, "전체 솔버 결과")}
              className="mt-3 text-sm text-purple-600 hover:underline flex items-center gap-1"
            >
              <FileJson size={14} /> JSON 보기
            </button>
          )}
        </div>
      </div>

      {/* B-2: Mode Selection Cards */}
      {isIdle && (
        <div className="card">
          <h2 className="card-header flex items-center gap-2">
            <Layers size={20} />
            스케줄링 모드
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {SCHEDULING_MODES.map((mode) => (
              <div
                key={mode.value}
                data-testid={`mode-${mode.value}`}
                onClick={() => setSchedulingMode(mode.value)}
                className={`p-4 rounded-lg border-2 cursor-pointer transition-all hover:shadow-md ${
                  schedulingMode === mode.value
                    ? mode.severity === "danger"
                      ? "border-red-500 bg-red-50"
                      : mode.severity === "warning"
                      ? "border-yellow-500 bg-yellow-50"
                      : "border-primary-500 bg-primary-50"
                    : "border-gray-200 hover:border-gray-300"
                }`}
              >
                <div className="flex items-center gap-2 mb-2">
                  {mode.severity === "danger" ? (
                    <AlertTriangle className="text-red-500" size={20} />
                  ) : mode.severity === "warning" ? (
                    <AlertCircle className="text-yellow-600" size={20} />
                  ) : (
                    <Shield className="text-primary-500" size={20} />
                  )}
                  <h3 className="font-semibold text-gray-800">{mode.label}</h3>
                  {schedulingMode === mode.value && (
                    <CheckCircle size={16} className="text-primary-600 ml-auto" />
                  )}
                </div>
                <p className="text-sm text-gray-600">{mode.description}</p>
                <div className="mt-2 flex gap-2">
                  <span className={`text-xs px-2 py-0.5 rounded ${mode.include_running ? "bg-red-100 text-red-700" : "bg-gray-100 text-gray-600"}`}>
                    진행중: {mode.include_running ? "포함" : "제외"}
                  </span>
                  <span className={`text-xs px-2 py-0.5 rounded ${mode.include_scheduled ? "bg-yellow-100 text-yellow-700" : "bg-gray-100 text-gray-600"}`}>
                    기스케줄: {mode.include_scheduled ? "포함" : "제외"}
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Mode Warning Banners */}
          {schedulingMode === "reschedule" && (
            <div className="mt-4 bg-yellow-50 border border-yellow-300 rounded-lg p-3 flex items-start gap-2">
              <AlertCircle className="text-yellow-600 flex-shrink-0 mt-0.5" size={18} />
              <div>
                <p className="text-yellow-800 font-medium text-sm">재스케줄링 모드</p>
                <p className="text-yellow-700 text-xs">기존 스케줄이 새 결과로 덮어씌워집니다. 승인 전 결과를 신중히 검토하세요.</p>
              </div>
            </div>
          )}
          {schedulingMode === "full_rebalance" && (
            <div className="mt-4 bg-red-50 border border-red-300 rounded-lg p-3 flex items-start gap-2">
              <AlertTriangle className="text-red-600 flex-shrink-0 mt-0.5" size={18} />
              <div>
                <p className="text-red-800 font-medium text-sm">전체 재배치 모드</p>
                <p className="text-red-700 text-xs">진행중 작업까지 재배치됩니다. 현장 작업자에게 사전 알림이 필요합니다.</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Scheduling Settings & Execute */}
      {(isIdle || workflowState === "solving" || workflowState === "comparing") && (
        <div className="card">
          <h2 className="card-header flex items-center gap-2">
            <Zap size={20} />
            스케줄 실행
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-3">
            {/* Horizon Hours */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                계획 기간 (시간)
              </label>
              <input
                type="number"
                value={horizonHours}
                onChange={(e) => setHorizonHours(parseInt(e.target.value) || 24)}
                className="w-full px-3 py-2 border rounded-md"
                min={1}
                max={168}
                disabled={workflowState === "solving"}
              />
            </div>

            {/* Solver Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                솔버 선택
              </label>
              <select
                value={solverType}
                onChange={(e) => setSolverType(e.target.value)}
                className="w-full px-3 py-2 border rounded-md"
                disabled={workflowState === "solving"}
              >
                {SOLVER_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Time Limit */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                시간 제한 (초)
              </label>
              <input
                type="number"
                value={timeLimitSec}
                onChange={(e) => setTimeLimitSec(parseInt(e.target.value) || 60)}
                className="w-full px-3 py-2 border rounded-md"
                min={10}
                max={300}
                disabled={workflowState === "solving"}
              />
            </div>

            {/* Action Buttons */}
            <div className="flex items-end gap-2">
              <button
                onClick={handleSolve}
                disabled={workflowState === "solving" || !workOrdersData?.count}
                className="btn btn-primary flex items-center gap-2 flex-1 justify-center"
              >
                {workflowState === "solving" && !solveProgress ? (
                  <>
                    <RefreshCw className="animate-spin" size={16} />
                    실행 중...
                  </>
                ) : (
                  <>
                    <Play size={16} />
                    스케줄 실행
                  </>
                )}
              </button>
              <button
                onClick={handleSolveAll}
                disabled={workflowState === "solving" || !workOrdersData?.count}
                className="btn btn-secondary flex items-center gap-2 justify-center"
                title="5개 솔버 순차 실행"
              >
                <BarChart3 size={16} />
                전체 비교
              </button>
            </div>
          </div>

          {/* Advanced scheduler parameters */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4 pt-3 border-t border-gray-100">
            {/* Lot Size */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Lot 크기
              </label>
              <input
                type="number"
                value={lotSize}
                onChange={(e) => setLotSize(parseInt(e.target.value) || 1)}
                className="w-full px-3 py-2 border rounded-md"
                min={1}
                disabled={workflowState === "solving"}
              />
              <p className="text-xs text-gray-400 mt-1">작업지시를 나눌 단위 수량 (1 = 분할 없음)</p>
            </div>

            {/* AMR Transfer Time */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                AMR 이동 시간 (초)
              </label>
              <input
                type="number"
                value={amrTransferTimeSec}
                onChange={(e) => setAmrTransferTimeSec(parseInt(e.target.value) || 60)}
                className="w-full px-3 py-2 border rounded-md"
                min={0}
                disabled={workflowState === "solving"}
              />
              <p className="text-xs text-gray-400 mt-1">설비 간 AMR 이동 소요 시간</p>
            </div>
          </div>

          {/* Solver description */}
          <p className="text-sm text-gray-500">
            {SOLVER_OPTIONS.find((o) => o.value === solverType)?.description}
          </p>
        </div>
      )}

      {/* B-4: Solve Progress Bar */}
      {workflowState === "solving" && solveProgress && (
        <div className="card">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-medium text-gray-700">전체 솔버 비교 실행중</h3>
            <button
              onClick={handleAbortSolveAll}
              className="btn btn-secondary btn-sm flex items-center gap-1"
            >
              <StopCircle size={14} />
              중단
            </button>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3 mb-2">
            <div
              className="bg-primary-600 h-3 rounded-full transition-all duration-300"
              style={{ width: `${((solveProgress.current + 1) / solveProgress.total) * 100}%` }}
            />
          </div>
          <p className="text-sm text-gray-500">
            {solveProgress.current + 1}/{solveProgress.total} 솔버 실행중 ({SOLVER_OPTIONS[solveProgress.current]?.label || ""})
          </p>
        </div>
      )}

      {/* Solving spinner (single solver) */}
      {workflowState === "solving" && !solveProgress && (
        <div className="card text-center py-8">
          <RefreshCw className="animate-spin mx-auto mb-3 text-primary-500" size={32} />
          <p className="text-gray-600">
            {SOLVER_OPTIONS.find((o) => o.value === solverType)?.label} 솔버 실행 중...
          </p>
        </div>
      )}

      {/* B-3: Comparison Table */}
      {workflowState === "comparing" && comparisonKPIs && (
        <div className="card border-2 border-primary-300">
          <div className="flex items-center justify-between mb-4">
            <h2 className="card-header flex items-center gap-2 text-primary-700">
              <BarChart3 size={20} />
              스케줄 결과 비교
            </h2>
            <button
              onClick={handleResetResults}
              className="btn btn-secondary btn-sm flex items-center gap-1"
            >
              <XCircle size={14} />
              결과 초기화
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 px-3 font-medium text-gray-600">KPI</th>
                  {currentBaseline && (
                    <th className="text-center py-2 px-3 font-medium text-gray-500 bg-gray-50">기존 스케줄</th>
                  )}
                  {comparisonKPIs.kpis.map((k, i) => (
                    <th key={i} className="text-center py-2 px-3 font-medium text-gray-700">
                      {SOLVER_OPTIONS.find((o) => o.value === k.solver)?.label || k.solver}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {/* Makespan */}
                <tr className="border-b">
                  <td className="py-2 px-3 font-medium text-gray-600">Makespan</td>
                  {currentBaseline && (
                    <td className="text-center py-2 px-3 bg-gray-50">
                      {formatHoursMinutes(currentBaseline.makespan_seconds)}
                    </td>
                  )}
                  {comparisonKPIs.kpis.map((k, i) => (
                    <td
                      key={i}
                      className={`text-center py-2 px-3 font-semibold ${
                        k.makespan === comparisonKPIs.bestMakespan ? "text-green-700 bg-green-50" : ""
                      }`}
                    >
                      {formatHoursMinutes(k.makespan)}
                    </td>
                  ))}
                </tr>
                {/* Utilization */}
                <tr className="border-b">
                  <td className="py-2 px-3 font-medium text-gray-600">평균 가동률</td>
                  {currentBaseline && (
                    <td className="text-center py-2 px-3 bg-gray-50">
                      {currentBaseline.avg_utilization.toFixed(1)}%
                    </td>
                  )}
                  {comparisonKPIs.kpis.map((k, i) => (
                    <td
                      key={i}
                      className={`text-center py-2 px-3 font-semibold ${
                        k.utilization === comparisonKPIs.bestUtilization ? "text-green-700 bg-green-50" : ""
                      }`}
                    >
                      {k.utilization.toFixed(1)}%
                    </td>
                  ))}
                </tr>
                {/* Tasks */}
                <tr className="border-b">
                  <td className="py-2 px-3 font-medium text-gray-600">작업 수</td>
                  {currentBaseline && (
                    <td className="text-center py-2 px-3 bg-gray-50">
                      {currentBaseline.total_tasks}
                    </td>
                  )}
                  {comparisonKPIs.kpis.map((k, i) => (
                    <td
                      key={i}
                      className={`text-center py-2 px-3 font-semibold ${
                        k.tasks === comparisonKPIs.bestTasks ? "text-green-700 bg-green-50" : ""
                      }`}
                    >
                      {k.tasks}
                    </td>
                  ))}
                </tr>
                {/* Solve Time */}
                <tr className="border-b">
                  <td className="py-2 px-3 font-medium text-gray-600">실행 시간</td>
                  {currentBaseline && (
                    <td className="text-center py-2 px-3 bg-gray-50">-</td>
                  )}
                  {comparisonKPIs.kpis.map((k, i) => (
                    <td
                      key={i}
                      className={`text-center py-2 px-3 font-semibold ${
                        k.solveTime === comparisonKPIs.bestSolveTime ? "text-green-700 bg-green-50" : ""
                      }`}
                    >
                      {k.solveTime.toFixed(2)}초
                    </td>
                  ))}
                </tr>
                {/* 납기지연(가중) — lexicographic tier-1 (= objective_value) */}
                <tr className="border-b">
                  <td className="py-2 px-3 font-medium text-gray-600" title="우선순위 가중 납기지연(낮을수록 좋음). 0이면 전 작업 납기 충족">
                    납기지연(가중)
                  </td>
                  {currentBaseline && (
                    <td className="text-center py-2 px-3 bg-gray-50">-</td>
                  )}
                  {comparisonKPIs.kpis.map((k, i) => (
                    <td
                      key={i}
                      className={`text-center py-2 px-3 font-semibold ${
                        k.tardiness === comparisonKPIs.bestTardiness ? "text-green-700 bg-green-50" : ""
                      }`}
                    >
                      {k.tardiness > 0 ? `${(k.tardiness / 60).toFixed(0)}분` : "0"}
                    </td>
                  ))}
                </tr>
                {/* 우선순위(가중완료) — lexicographic tier-2 */}
                <tr className="border-b">
                  <td className="py-2 px-3 font-medium text-gray-600" title="우선순위 가중 완료시간(Σ weight·완료). 낮을수록 우선순위 높은 주문을 빨리 완료. OR-Tools가 makespan보다 이 값을 먼저 최적화">
                    우선순위(가중완료)
                  </td>
                  {currentBaseline && (
                    <td className="text-center py-2 px-3 bg-gray-50">-</td>
                  )}
                  {comparisonKPIs.kpis.map((k, i) => (
                    <td
                      key={i}
                      className={`text-center py-2 px-3 font-semibold ${
                        k.completion === comparisonKPIs.bestCompletion ? "text-green-700 bg-green-50" : ""
                      }`}
                    >
                      {k.completion > 0 ? `${(k.completion / 60).toFixed(0)}분` : "0"}
                    </td>
                  ))}
                </tr>
                {/* 셋업 시간 — lexicographic tier-4 */}
                <tr className="border-b">
                  <td className="py-2 px-3 font-medium text-gray-600" title="총 셋업(준비교체) 시간. 낮을수록 좋음">
                    셋업 시간
                  </td>
                  {currentBaseline && (
                    <td className="text-center py-2 px-3 bg-gray-50">-</td>
                  )}
                  {comparisonKPIs.kpis.map((k, i) => (
                    <td
                      key={i}
                      className={`text-center py-2 px-3 font-semibold ${
                        k.setup === comparisonKPIs.bestSetup ? "text-green-700 bg-green-50" : ""
                      }`}
                    >
                      {k.setup > 0 ? `${(k.setup / 60).toFixed(0)}분` : "0"}
                    </td>
                  ))}
                </tr>
                {/* Approve buttons row */}
                <tr>
                  <td className="py-3 px-3"></td>
                  {currentBaseline && <td className="py-3 px-3"></td>}
                  {results.map((r, i) => (
                    <td key={i} className="text-center py-3 px-3">
                      <button
                        onClick={() => handleSelectResult(r)}
                        className="btn btn-primary btn-sm flex items-center gap-1 mx-auto"
                      >
                        <ArrowRight size={14} />
                        선택
                      </button>
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Detail View (selected result for review) */}
      {(workflowState === "detail" || workflowState === "approving") && selectedResult && (
        <div className="card border-2 border-yellow-400">
          <div className="flex items-center justify-between mb-4">
            <h2 className="card-header flex items-center gap-2 text-yellow-700">
              <AlertCircle size={20} />
              스케줄 결과 검토 - {SOLVER_OPTIONS.find((o) => o.value === selectedResult.solver_type)?.label || selectedResult.solver_type}
            </h2>
            <button
              onClick={() => showJson(selectedResult.scheduling_result, "스케줄 결과")}
              className="text-sm text-gray-600 hover:underline flex items-center gap-1"
            >
              <FileJson size={14} /> JSON 보기
            </button>
          </div>

          {/* Statistics Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-primary-50 p-4 rounded-lg">
              <p className="text-sm text-gray-500">Makespan</p>
              <p className="text-xl font-bold text-primary-700">
                {formatSeconds(selectedResult.statistics.makespan_seconds)}
              </p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <p className="text-sm text-gray-500">평균 가동률</p>
              <p className="text-xl font-bold text-green-700">
                {calcAvgUtilization(selectedResult.statistics.machine_utilization).toFixed(1)}%
              </p>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <p className="text-sm text-gray-500">스케줄 작업</p>
              <p className="text-xl font-bold text-purple-700">
                {selectedResult.statistics.total_tasks}개
              </p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-500">실행 시간</p>
              <p className="text-xl font-bold text-gray-700">
                {selectedResult.statistics.solve_time_sec.toFixed(2)}초
              </p>
            </div>
          </div>

          {/* Scheduled Tasks Table */}
          {selectedResult.scheduling_result.scheduled_tasks.length > 0 && (
            <div className="overflow-x-auto mb-6">
              <table className="table">
                <thead>
                  <tr>
                    <th>WO ID</th>
                    <th>공정 ID</th>
                    <th>설비</th>
                    <th>시작 시간</th>
                    <th>종료 시간</th>
                    <th>수량</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedResult.scheduling_result.scheduled_tasks.slice(0, 20).map((task, idx) => {
                    const ganttStart = selectedResult.scheduling_result.gantt_data?.start;
                    const startDate = ganttStart
                      ? new Date(new Date(ganttStart).getTime() + task.start_time * 1000)
                      : null;
                    const endDate = ganttStart
                      ? new Date(new Date(ganttStart).getTime() + task.end_time * 1000)
                      : null;
                    return (
                      <tr key={idx}>
                        <td className="font-mono text-sm">{task.wo_id}</td>
                        <td className="font-mono text-sm">{task.op_id}</td>
                        <td>{task.machine_id}</td>
                        <td className="text-sm">
                          {startDate ? format(startDate, "MM/dd HH:mm") : formatSeconds(task.start_time)}
                        </td>
                        <td className="text-sm">
                          {endDate ? format(endDate, "MM/dd HH:mm") : formatSeconds(task.end_time)}
                        </td>
                        <td>{task.quantity}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              {selectedResult.scheduling_result.scheduled_tasks.length > 20 && (
                <p className="text-sm text-gray-500 mt-2">
                  ... 외 {selectedResult.scheduling_result.scheduled_tasks.length - 20}개 작업
                </p>
              )}
            </div>
          )}

          {/* Gantt Chart PNG (cell-scheduler가 저장한 파일을 직접 표시) */}
          {process.env.NEXT_PUBLIC_SCHEDULER_URL && (
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">간트차트</h3>
              <img
                src={`${process.env.NEXT_PUBLIC_SCHEDULER_URL}/output/gantt_${selectedResult.solver_type}.png`}
                alt={`${selectedResult.solver_type} 간트차트`}
                className="w-full rounded border border-gray-200 bg-gray-50"
                onError={(e) => {
                  (e.currentTarget as HTMLImageElement).style.display = "none";
                }}
              />
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <button
              onClick={handleCancel}
              className="btn btn-secondary flex items-center gap-2"
            >
              <XCircle size={16} />
              취소
            </button>
            {results.length > 1 && (
              <button
                onClick={handleBackToCompare}
                className="btn btn-secondary flex items-center gap-2"
              >
                <BarChart3 size={16} />
                비교로 돌아가기
              </button>
            )}
            <button
              onClick={handleApprove}
              disabled={approveMutation.isPending}
              className="btn btn-primary flex items-center gap-2"
            >
              {approveMutation.isPending ? (
                <>
                  <RefreshCw className="animate-spin" size={16} />
                  승인 중...
                </>
              ) : (
                <>
                  <CheckCircle size={16} />
                  스케줄 승인
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Approval Result */}
      {workflowState === "approved" && approvalResult && (
        <div className="card border-2 border-green-400">
          <div className="flex items-start justify-between">
            <h2 className="card-header flex items-center gap-2 text-green-700">
              <CheckCircle size={20} />
              스케줄 승인 완료
            </h2>
            <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium">
              {approvalResult.updated_orders?.length || 0}개 작업지시 업데이트됨
            </span>
          </div>

          {/* Success Summary */}
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
            <p className="text-green-800 font-medium mb-2">
              {approvalResult.message || "스케줄이 성공적으로 적용되었습니다."}
            </p>
            <p className="text-green-700 text-sm">
              작업지시의 계획 시작/종료 시간이 업데이트되었습니다.
              작업지시 페이지에서 확인할 수 있습니다.
            </p>
          </div>

          {approvalResult.updated_orders && approvalResult.updated_orders.length > 0 && (
            <div className="overflow-x-auto mb-4">
              <table className="table">
                <thead>
                  <tr>
                    <th>작업지시 ID</th>
                    <th>Lot No</th>
                    <th>계획 시작</th>
                    <th>계획 종료</th>
                    <th>할당 설비</th>
                  </tr>
                </thead>
                <tbody>
                  {approvalResult.updated_orders.map((order: any, idx: number) => (
                    <tr key={idx} className="bg-green-50">
                      <td className="font-mono font-medium">WO-{order.mes_order_id}</td>
                      <td className="text-sm text-gray-600">{order.lot_no || "-"}</td>
                      <td className="text-sm">
                        <span className="px-2 py-1 bg-green-100 text-green-800 rounded">
                          {order.scheduled_start}
                        </span>
                      </td>
                      <td className="text-sm">
                        <span className="px-2 py-1 bg-green-100 text-green-800 rounded">
                          {order.scheduled_end}
                        </span>
                      </td>
                      <td>{order.machine_id || "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div className="flex justify-between items-center pt-4 border-t mt-4">
            <button
              onClick={() => router.push("/production/orders?view=all")}
              className="btn btn-secondary flex items-center gap-2"
            >
              <ExternalLink size={16} />
              작업지시 목록 보기
            </button>
            <button
              onClick={() => {
                setWorkflowState("idle");
                setResults([]);
                setSelectedResult(null);
                setApprovalResult(null);
                setCurrentBaseline(null);
                refetchOrders();
              }}
              className="btn btn-primary"
            >
              새 스케줄 생성
            </button>
          </div>
        </div>
      )}

      {/* Equipment List */}
      {equipmentData && equipmentData.machines.length > 0 && isIdle && (
        <div className="card">
          <h2 className="card-header">가용 설비 목록</h2>
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th>Machine ID</th>
                  <th>이름</th>
                  <th>타입</th>
                  <th>상태</th>
                  <th>가용 시간</th>
                  <th>위치</th>
                </tr>
              </thead>
              <tbody>
                {equipmentData.machines.map((machine) => (
                  <tr key={machine.machine_id}>
                    <td className="font-mono text-sm">{machine.machine_id}</td>
                    <td>{machine.machine_name}</td>
                    <td>
                      <span className="px-2 py-1 bg-gray-100 rounded text-sm">
                        {machine.machine_type}
                      </span>
                    </td>
                    <td>
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-medium ${
                          machine.status === "AVAILABLE"
                            ? "bg-green-100 text-green-800"
                            : machine.status === "RUNNING"
                            ? "bg-primary-100 text-primary-800"
                            : "bg-gray-100 text-gray-800"
                        }`}
                      >
                        {machine.status}
                      </span>
                    </td>
                    <td className="text-sm text-gray-500">
                      {formatDateTime(machine.available_from)}
                    </td>
                    <td className="text-sm text-gray-500">{machine.location || "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Work Orders List */}
      {workOrdersData && workOrdersData.work_orders.length > 0 && isIdle && (
        <div className="card">
          <h2 className="card-header flex items-center gap-2">
            스케줄 대상 작업 목록
            <span className="relative group">
              <span className="w-4 h-4 bg-gray-200 text-gray-600 rounded-full text-xs flex items-center justify-center cursor-help">?</span>
              <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-gray-800 text-white text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50">
                이번 스케줄링 실행에 포함될 작업
              </span>
            </span>
          </h2>
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th>WO ID</th>
                  <th>Lot No</th>
                  <th>제품</th>
                  <th>수량</th>
                  <th>우선순위</th>
                  <th>납기일</th>
                  <th>예정 시작</th>
                </tr>
              </thead>
              <tbody>
                {workOrdersData.work_orders.map((wo: any) => (
                  <tr key={wo.wo_id}>
                    <td className="font-mono text-sm">{wo.wo_id}</td>
                    <td className="font-mono text-sm text-gray-600">{wo.lot_no || "-"}</td>
                    <td>
                      <p className="font-medium">{wo.product_name}</p>
                    </td>
                    <td>{wo.order_quantity}</td>
                    <td>
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-medium ${
                          wo.priority === "high"
                            ? "bg-red-100 text-red-800"
                            : wo.priority === "medium"
                            ? "bg-yellow-100 text-yellow-800"
                            : "bg-gray-100 text-gray-800"
                        }`}
                      >
                        {wo.priority === "high" ? "높음" : wo.priority === "medium" ? "중간" : "낮음"}
                      </span>
                    </td>
                    <td className="text-sm text-gray-500">
                      {wo.due_date ? formatDateTime(wo.due_date) : "-"}
                    </td>
                    <td className="text-sm text-gray-500">
                      {wo.release_date ? formatDateTime(wo.release_date) : "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* JSON Modal */}
      <JsonModal
        isOpen={showJsonModal}
        title={jsonModalTitle}
        data={jsonModalData}
        onClose={() => setShowJsonModal(false)}
      />
    </div>
  );
}
