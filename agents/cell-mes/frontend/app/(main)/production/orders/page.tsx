"use client";

import { useState, useEffect, useMemo, ReactNode } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import { productionService } from "@/services/production";
import { productService, scenarioService } from "@/services/master";
import {
  WorkOrder,
  OrderFilters,
  ProdResult,
  ProductionUnit,
  Scenario,
  MiddlewareResumeMode,
  MiddlewareUnitState,
} from "@/types";
import ErrorBoundary from "@/components/ErrorBoundary";
import { Plus, Play, Pause, CheckCircle, X, ChevronLeft, ChevronRight, ArrowUpDown, ArrowUp, ArrowDown, Eye, Trash2, Activity, FileEdit, AlertTriangle, RotateCcw, Square, StepForward } from "lucide-react";
import LotMonitoringModal from "@/components/production/LotMonitoringModal";
import { POLLING } from "@/config/constants";

const statusColors: Record<string, string> = {
  READY: "bg-gray-100 text-gray-800",
  SCHEDULED: "bg-primary-100 text-primary-800",
  RUNNING: "bg-green-100 text-green-800",
  PAUSE: "bg-yellow-100 text-yellow-800",
  SCENARIO_HOLD: "bg-yellow-100 text-yellow-800",
  DONE: "bg-primary-100 text-primary-800",
  ERROR: "bg-red-100 text-red-800",
};

const statusLabels: Record<string, string> = {
  READY: "대기",
  SCHEDULED: "스케줄됨",
  RUNNING: "진행중",
  PAUSE: "일시정지",
  SCENARIO_HOLD: "시나리오 보류",
  DONE: "완료",
  ERROR: "에러",
};

const viewLabels: Record<string, string> = {
  today: "오늘 작업",
  upcoming: "예정 작업",
  active: "진행중",
  all: "전체",
};

// Sortable column header component
const SortableHeader = ({
  label,
  field,
  currentSort,
  currentOrder,
  onSort
}: {
  label: string;
  field: string;
  currentSort: string;
  currentOrder: string;
  onSort: (field: string) => void;
}) => {
  const isActive = currentSort === field;
  return (
    <button
      onClick={() => onSort(field)}
      className="flex items-center gap-1 hover:text-primary-600 transition-colors"
    >
      {label}
      {isActive ? (
        currentOrder === "asc" ? <ArrowUp size={14} /> : <ArrowDown size={14} />
      ) : (
        <ArrowUpDown size={14} className="text-gray-400" />
      )}
    </button>
  );
};

function ChangeScenarioModal({
  order,
  onConfirm,
  onClose,
  isLoading,
}: {
  order: WorkOrder;
  onConfirm: (scenarioId: number) => void;
  onClose: () => void;
  isLoading: boolean;
}) {
  const [selectedScenarioId, setSelectedScenarioId] = useState<number | "">(order.scenario_id || "");
  const { data: scenarios } = useQuery({
    queryKey: ["scenarios-for-order"],
    queryFn: () => scenarioService.getAll(),
  });

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
        <h2 className="text-lg font-semibold mb-2">단위 시나리오 교체 - {order.lot_no}</h2>
        <p className="text-sm text-gray-600 mb-4 bg-yellow-50 p-3 rounded border border-yellow-200">
          작업이 <strong className="text-yellow-700">PAUSE</strong> 상태일 때만 동작 시나리오를 교체할 수 있습니다.<br />
          변경 시, 큐에서 대기 중인(READY) 유닛들의 시나리오가 일괄 동기화됩니다.
        </p>
        
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-1">새 시나리오 선택</label>
          <select
            value={selectedScenarioId}
            onChange={(e) => setSelectedScenarioId(parseInt(e.target.value) || "")}
            className="w-full px-3 py-2 border rounded-md bg-white"
          >
            <option value="">시나리오를 선택하세요...</option>
            {scenarios?.map((scen: any) => (
              <option key={scen.id} value={scen.id}>{scen.name} ({scen.file_path})</option>
            ))}
          </select>
        </div>

        <div className="flex justify-end gap-3">
          <button onClick={onClose} disabled={isLoading} className="btn btn-secondary">취소</button>
          <button 
             onClick={() => selectedScenarioId && onConfirm(selectedScenarioId as number)} 
             disabled={isLoading || !selectedScenarioId || selectedScenarioId === order.scenario_id} 
             className="btn btn-primary"
          >
            {isLoading ? "변경 중..." : "변경 반영"}
          </button>
        </div>
      </div>
    </div>
  );
}

function UnitScenarioChangeModal({
  order,
  unit,
  onConfirm,
  onRelease,
  onClose,
  isSaving,
  isReleasing,
}: {
  order: WorkOrder;
  unit: ProductionUnit;
  onConfirm: (scenarioId: number) => void;
  onRelease: () => void;
  onClose: () => void;
  isSaving: boolean;
  isReleasing: boolean;
}) {
  const [selectedScenarioId, setSelectedScenarioId] = useState<number | "">(unit.scenario_id || "");
  const { data: scenarios, isLoading } = useQuery({
    queryKey: ["unit-scenarios-for-product", order.product_id],
    queryFn: () => scenarioService.getAll(order.product_id, true),
    enabled: order.product_id > 0,
  });

  useEffect(() => {
    setSelectedScenarioId(unit.scenario_id || "");
  }, [unit.id, unit.scenario_id]);

  const isBusy = isSaving || isReleasing;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60] p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg p-6">
        <div className="flex items-start justify-between gap-4 mb-4">
          <div>
            <h2 className="text-lg font-semibold">유닛 시나리오 변경 - Unit {unit.unit_no}</h2>
            <p className="text-sm text-gray-500 mt-1">{order.lot_no}</p>
          </div>
          <button
            onClick={onClose}
            disabled={isBusy}
            className="p-2 hover:bg-gray-100 rounded"
            aria-label="유닛 시나리오 변경 닫기"
          >
            <X size={18} />
          </button>
        </div>

        <div className="mb-4 rounded-md border border-yellow-200 bg-yellow-50 p-3 text-sm text-yellow-800">
          현재 유닛은 SCENARIO_HOLD 상태로 레디큐에서 숨겨져 있습니다. 변경 반영 또는 보류 해제를 선택하면 READY 상태로 돌아갑니다.
        </div>

        <div className="mb-6 space-y-2">
          <label className="block text-sm font-medium text-gray-700">새 시나리오 선택</label>
          <select
            value={selectedScenarioId}
            onChange={(e) => setSelectedScenarioId(parseInt(e.target.value, 10) || "")}
            className="w-full px-3 py-2 border rounded-md bg-white"
            disabled={isBusy || isLoading}
          >
            <option value="">{isLoading ? "시나리오 불러오는 중..." : "시나리오를 선택하세요..."}</option>
            {scenarios?.map((scenario: Scenario) => (
              <option key={scenario.id} value={scenario.id}>
                {scenario.name} ({scenario.file_path})
              </option>
            ))}
          </select>
          {unit.scenario && (
            <p className="text-xs text-gray-500">
              현재: {unit.scenario.name} ({unit.scenario.file_path})
            </p>
          )}
        </div>

        <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-between">
          <button
            onClick={onRelease}
            disabled={isBusy}
            className="btn btn-secondary text-yellow-700 border-yellow-300 hover:bg-yellow-50"
          >
            {isReleasing ? "해제 중..." : "보류 해제"}
          </button>
          <div className="flex justify-end gap-2">
            <button onClick={onClose} disabled={isBusy} className="btn btn-secondary">
              닫기
            </button>
            <button
              onClick={() => selectedScenarioId && onConfirm(selectedScenarioId as number)}
              disabled={isBusy || !selectedScenarioId || selectedScenarioId === unit.scenario_id}
              className="btn btn-primary"
            >
              {isSaving ? "변경 중..." : "변경 반영"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function ConfirmStartModal({
  order,
  onConfirm,
  onClose,
  isLoading,
}: {
  order: WorkOrder;
  onConfirm: () => void;
  onClose: () => void;
  isLoading: boolean;
}) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
        <h2 className="text-lg font-semibold mb-2">작업 시작 - {order.lot_no}</h2>
        <p className="text-sm text-gray-600 mb-6 bg-primary-50 p-3 rounded border border-primary-100">
          이 작업지시를 실행 상태로 전환합니다.<br />
          <strong className="text-primary-700">시작 후 미들웨어가 READY 유닛과 실행 패키지를 조회할 수 있습니다.</strong>
        </p>
        <div className="flex justify-end gap-3">
          <button onClick={onClose} disabled={isLoading} className="btn btn-secondary">
            취소
          </button>
          <button onClick={() => onConfirm()} disabled={isLoading} className="btn btn-primary flex items-center gap-2">
            {isLoading ? "시작 중..." : "작업 시작"}
          </button>
        </div>
      </div>
    </div>
  );
}

function ConfirmDeleteModal({
  order,
  onConfirm,
  onClose,
  isLoading,
}: {
  order: WorkOrder;
  onConfirm: () => void;
  onClose: () => void;
  isLoading: boolean;
}) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
        <h2 className="text-lg font-semibold mb-2 text-red-600">작업지시 삭제 - {order.lot_no}</h2>
        <p className="text-sm text-gray-600 mb-4 bg-red-50 p-3 rounded border border-red-100">
          <strong className="text-red-700">삭제한 작업지시는 복구할 수 없습니다.</strong><br />
          실행 중(RUNNING) 상태에서는 삭제할 수 없습니다. 해당 작업을 정말 삭제하시겠습니까?
        </p>
        <div className="flex justify-end gap-3">
          <button onClick={onClose} disabled={isLoading} className="btn btn-secondary">
            취소
          </button>
          <button onClick={() => onConfirm()} disabled={isLoading} className="btn bg-red-600 text-white hover:bg-red-700 flex items-center gap-2">
            {isLoading ? "삭제 중..." : "삭제 확인"}
          </button>
        </div>
      </div>
    </div>
  );
}

const middlewareStatusColors: Record<string, string> = {
  READY: "bg-gray-100 text-gray-800",
  RUNNING: "bg-green-100 text-green-800",
  WAITING: "bg-orange-100 text-orange-800",
  STOPPED: "bg-yellow-100 text-yellow-800",
  ALARM: "bg-red-100 text-red-800",
  COMPLETED: "bg-primary-100 text-primary-800",
  DONE: "bg-primary-100 text-primary-800",
  CANCELED: "bg-gray-200 text-gray-700",
  ERROR: "bg-red-100 text-red-800",
};

function middlewareStatusClass(statusValue?: string | null) {
  return middlewareStatusColors[statusValue || ""] || "bg-gray-100 text-gray-700";
}

function formatMiddlewareError(error: any): string {
  const detail = error.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (detail?.message) return detail.message;
  if (detail?.middleware_response?.message) return detail.middleware_response.message;
  return error.message || "미들웨어 요청에 실패했습니다.";
}

function ResumeMiddlewareUnitModal({
  unit,
  onConfirm,
  onClose,
  isLoading,
}: {
  unit: MiddlewareUnitState;
  onConfirm: (payload: { mode: MiddlewareResumeMode; resume_step_id?: string | null; clear_retry: boolean }) => void;
  onClose: () => void;
  isLoading: boolean;
}) {
  const [mode, setMode] = useState<MiddlewareResumeMode>("CURRENT_STEP");
  const [resumeStepId, setResumeStepId] = useState<string>("");
  const steps = unit.recipe_steps || [];

  useEffect(() => {
    setMode("CURRENT_STEP");
    setResumeStepId("");
  }, [unit.unit_no]);

  const canSubmit = mode !== "SPECIFIC_STEP" || !!resumeStepId;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[70] p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg p-6">
        <div className="flex items-start justify-between gap-4 mb-4">
          <div>
            <h2 className="text-lg font-semibold">유닛 재개 - Unit {unit.unit_no}</h2>
            <p className="text-sm text-gray-500 mt-1">
              현재 스텝: {unit.current_step_id || "-"} / 상태: {unit.middleware_status || "-"}
            </p>
          </div>
          <button onClick={onClose} disabled={isLoading} className="p-2 hover:bg-gray-100 rounded" aria-label="재개 모달 닫기">
            <X size={18} />
          </button>
        </div>

        <div className="rounded-md border border-yellow-200 bg-yellow-50 p-3 text-sm text-yellow-800 mb-4">
          이 기능은 미들웨어와 동일하게 STOPPED 상태에서만 사용합니다. ALARM 상태는 먼저 알람 해제를 완료해야 합니다.
        </div>

        <div className="space-y-3">
          <label className="flex items-start gap-3 rounded-md border border-gray-200 p-3 cursor-pointer">
            <input
              type="radio"
              name="resume-mode"
              value="CURRENT_STEP"
              checked={mode === "CURRENT_STEP"}
              onChange={() => setMode("CURRENT_STEP")}
              className="mt-1"
            />
            <span>
              <span className="block text-sm font-medium">현재 스텝에서 재개</span>
              <span className="block text-xs text-gray-500 mt-0.5">중단된 현재 스텝을 다시 실행합니다.</span>
            </span>
          </label>
          <label className="flex items-start gap-3 rounded-md border border-gray-200 p-3 cursor-pointer">
            <input
              type="radio"
              name="resume-mode"
              value="SKIP_CURRENT_STEP"
              checked={mode === "SKIP_CURRENT_STEP"}
              onChange={() => setMode("SKIP_CURRENT_STEP")}
              className="mt-1"
            />
            <span>
              <span className="block text-sm font-medium">현재 스텝 건너뛰기</span>
              <span className="block text-xs text-gray-500 mt-0.5">미들웨어 `resume?skip_step=true`로 다음 스텝부터 실행합니다.</span>
            </span>
          </label>
          <label className="block rounded-md border border-gray-200 p-3">
            <div className="flex items-start gap-3">
              <input
                type="radio"
                name="resume-mode"
                value="SPECIFIC_STEP"
                checked={mode === "SPECIFIC_STEP"}
                onChange={() => setMode("SPECIFIC_STEP")}
                className="mt-1"
              />
              <span>
                <span className="block text-sm font-medium">특정 스텝부터 재개</span>
                <span className="block text-xs text-gray-500 mt-0.5">선택한 스텝 ID를 `resume_step_id`로 전달합니다.</span>
              </span>
            </div>
            <select
              value={resumeStepId}
              onChange={(event) => setResumeStepId(event.target.value)}
              disabled={mode !== "SPECIFIC_STEP" || steps.length === 0}
              className="mt-3 w-full px-3 py-2 border rounded-md bg-white text-sm disabled:bg-gray-100"
            >
              <option value="">{steps.length === 0 ? "스텝 목록 없음" : "스텝 선택"}</option>
              {steps.map((step: any) => (
                <option key={step.id} value={step.id}>
                  {step.id}{step.name ? ` - ${step.name}` : ""}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="flex justify-end gap-2 mt-6">
          <button onClick={onClose} disabled={isLoading} className="btn btn-secondary">취소</button>
          <button
            onClick={() => onConfirm({ mode, resume_step_id: mode === "SPECIFIC_STEP" ? resumeStepId : null, clear_retry: true })}
            disabled={isLoading || !canSubmit}
            className="btn btn-primary"
          >
            {isLoading ? "요청 중..." : "재개 요청"}
          </button>
        </div>
      </div>
    </div>
  );
}

function OrderDetailModal({
  order,
  progressMap,
  orderResults,
  orderResultsError,
  onClose,
  renderActionButtons,
}: {
  order: WorkOrder;
  progressMap: Record<number, { ok: number; ng: number }>;
  orderResults: ProdResult[];
  orderResultsError: boolean;
  onClose: () => void;
  renderActionButtons: (order: WorkOrder) => ReactNode;
}) {
  const queryClient = useQueryClient();
  const [scenarioChangeUnit, setScenarioChangeUnit] = useState<ProductionUnit | null>(null);
  const [resumeUnit, setResumeUnit] = useState<MiddlewareUnitState | null>(null);

  const { data: unitsData, isLoading: isLoadingUnits } = useQuery({
    queryKey: ["order-units", order.id],
    queryFn: () => productionService.getUnitsForOrder(order.id),
    refetchInterval: POLLING.FAST
  });

  const {
    data: middlewareState,
    isLoading: isLoadingMiddlewareState,
    isError: isMiddlewareStateError,
    error: middlewareStateError,
  } = useQuery({
    queryKey: ["order-middleware-state", order.id],
    queryFn: () => productionService.getMiddlewareState(order.id),
    refetchInterval: POLLING.FAST,
    enabled: !!order.id,
  });

  const middlewareCommandMutation = useMutation({
    mutationFn: ({ unitNo, action }: { unitNo: string; action: string }) =>
      productionService.commandMiddlewareUnit(order.id, unitNo, action),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["order-middleware-state", order.id] });
    },
    onError: (error: any) => {
      alert(formatMiddlewareError(error));
    },
  });

  const resumeMiddlewareMutation = useMutation({
    mutationFn: ({
      unitNo,
      payload,
    }: {
      unitNo: string;
      payload: { mode: MiddlewareResumeMode; resume_step_id?: string | null; clear_retry: boolean };
    }) => productionService.resumeMiddlewareUnit(order.id, unitNo, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["order-middleware-state", order.id] });
      setResumeUnit(null);
    },
    onError: (error: any) => {
      alert(formatMiddlewareError(error));
    },
  });
  
  const holdUnitScenarioMutation = useMutation({
    mutationFn: (unit: ProductionUnit) => productionService.holdUnitScenario(order.id, unit.id),
    onSuccess: (data, unit) => {
      const heldUnit = {
        ...unit,
        status: data.status,
        scenario_hold_started_at: data.scenario_hold_started_at,
        scenario_hold_by: data.scenario_hold_by,
      };
      setScenarioChangeUnit(heldUnit);
      queryClient.invalidateQueries({ queryKey: ["order-units", order.id] });
    },
    onError: (error: any) => {
      alert(`시나리오 변경 보류 실패: ${error.response?.data?.detail || error.message}`);
      queryClient.invalidateQueries({ queryKey: ["order-units", order.id] });
    }
  });

  const updateUnitScenarioMutation = useMutation({
    mutationFn: ({ unitId, scenarioId }: { unitId: number; scenarioId: number }) =>
      productionService.updateUnitScenario(order.id, unitId, scenarioId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["order-units", order.id] });
      setScenarioChangeUnit(null);
      alert("유닛 시나리오 변경이 완료되었습니다.");
    },
    onError: (error: any) => {
      alert(`유닛 시나리오 변경 실패: ${error.response?.data?.detail || error.message}`);
      queryClient.invalidateQueries({ queryKey: ["order-units", order.id] });
    }
  });

  const releaseUnitScenarioHoldMutation = useMutation({
    mutationFn: (unitId: number) => productionService.releaseUnitScenarioHold(order.id, unitId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["order-units", order.id] });
      setScenarioChangeUnit(null);
    },
    onError: (error: any) => {
      alert(`시나리오 보류 해제 실패: ${error.response?.data?.detail || error.message}`);
      queryClient.invalidateQueries({ queryKey: ["order-units", order.id] });
    }
  });

  const units: ProductionUnit[] = unitsData?.items || [];
  const middlewareUnits = middlewareState?.units || [];
  const middlewareAlarmCount = middlewareUnits.filter((unit) => unit.middleware_status === "ALARM").length;
  const middlewarePendingStopCount = middlewareUnits.filter((unit) => unit.pending_stop).length;

  const progress = progressMap[order.id];
  const okSum = progress?.ok || 0;
  const ngSum = progress?.ng || 0;
  const pct = order.target_qty > 0 ? Math.min((okSum / order.target_qty) * 100, 100) : 0;
  const barColor = pct >= 95 ? "bg-green-500" : pct >= 50 ? "bg-primary-500" : "bg-gray-400";

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold">작업지시 상세 - {order.lot_no}</h2>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded">
            <X size={20} />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Basic Info */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label className="text-sm text-gray-500">제품</label>
              <p className="font-medium">{order.product ? `${order.product.code} - ${order.product.name}` : `#${order.product_id}`}</p>
            </div>
            <div>
              <label className="text-sm text-gray-500">상태</label>
              <p>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[order.status] || "bg-gray-100"}`}>
                  {statusLabels[order.status] || order.status}
                </span>
              </p>
            </div>
            <div>
              <label className="text-sm text-gray-500">우선순위</label>
              <p className="font-medium">{order.priority}</p>
            </div>
            <div>
              <label className="text-sm text-gray-500">목표수량</label>
              <p className="font-medium">{order.target_qty.toLocaleString()}</p>
            </div>
            <div>
              <label className="text-sm text-gray-500">배정설비</label>
              <p className="font-medium">{order.scheduled_equipment_name || "미배정"}</p>
            </div>
            <div>
              <label className="text-sm text-gray-500">납기일</label>
              <p className="font-medium">{order.due_date ? new Date(order.due_date).toLocaleString() : "-"}</p>
            </div>
            <div>
              <label className="text-sm text-gray-500">계획시작</label>
              <p className="font-medium">{order.plan_start ? new Date(order.plan_start).toLocaleString() : "-"}</p>
            </div>
            <div>
              <label className="text-sm text-gray-500">생성일</label>
              <p className="font-medium">{new Date(order.created_at).toLocaleDateString()}</p>
            </div>
          </div>

          {order.remarks && (
            <div>
              <label className="text-sm text-gray-500">비고</label>
              <p className="p-3 bg-gray-50 rounded-lg text-sm">{order.remarks}</p>
            </div>
          )}

          {/* Progress Bar */}
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">진척률</span>
              <span className="text-sm font-bold">{okSum.toLocaleString()} / {order.target_qty.toLocaleString()} ({pct.toFixed(1)}%)</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div className={`${barColor} h-3 rounded-full transition-all`} style={{ width: `${pct}%` }} />
            </div>
            <div className="flex justify-between mt-2 text-xs text-gray-500">
              <span>양품: {okSum.toLocaleString()}</span>
              <span>불량: {ngSum.toLocaleString()}</span>
              <span>수율: {(okSum + ngSum > 0 ? (okSum / (okSum + ngSum) * 100) : 0).toFixed(1)}%</span>
            </div>
          </div>

          {/* Middleware Runtime Monitor */}
          <div className="pt-4 border-t">
            <h3 className="text-sm font-semibold text-gray-700 mb-3 flex flex-wrap items-center justify-between gap-2">
              <span className="flex items-center gap-2">
                <Activity size={16} className="text-primary-600" />
                미들웨어 실행 모니터링
              </span>
              <span className="flex flex-wrap items-center gap-2 text-xs font-normal">
                {isLoadingMiddlewareState && <span className="text-primary-500 border border-primary-200 bg-primary-50 px-2 py-0.5 rounded">업데이트 중...</span>}
                {middlewareState && (
                  <>
                    <span className={`px-2 py-0.5 rounded-full font-medium ${middlewareState.sync_status === "SYNCED" ? "bg-green-100 text-green-800" : middlewareState.sync_status === "MIDDLEWARE_NOT_FOUND" ? "bg-gray-100 text-gray-700" : "bg-yellow-100 text-yellow-800"}`}>
                      {middlewareState.sync_status}
                    </span>
                    <span className="text-gray-500">
                      Lot {middlewareState.middleware_lot_status || "-"} / 알람 {middlewareAlarmCount} / 정지예약 {middlewarePendingStopCount}
                    </span>
                  </>
                )}
              </span>
            </h3>

            {isMiddlewareStateError ? (
              <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                <div className="font-semibold flex items-center gap-2">
                  <AlertTriangle size={16} />
                  미들웨어 상태를 조회할 수 없습니다.
                </div>
                <p className="mt-1">{formatMiddlewareError(middlewareStateError)}</p>
              </div>
            ) : middlewareState?.sync_status === "MIDDLEWARE_NOT_FOUND" ? (
              <div className="rounded-md border border-gray-200 bg-gray-50 p-4 text-sm text-gray-600">
                미들웨어에서 이 Lot을 찾지 못했습니다. MES Unit 목록만 표시됩니다.
              </div>
            ) : middlewareUnits.length > 0 ? (
              <div className="overflow-x-auto max-h-72 overflow-y-auto border border-gray-200 rounded-md">
                <table className="table text-sm w-full sticky-header min-w-[980px]">
                  <thead className="bg-gray-50 top-0 sticky">
                    <tr>
                      <th className="py-2">Unit</th>
                      <th className="py-2">MES</th>
                      <th className="py-2">Middleware</th>
                      <th className="py-2">Current Step</th>
                      <th className="py-2">Resources</th>
                      <th className="py-2">Alarm</th>
                      <th className="py-2">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {middlewareUnits.map((unit) => {
                      const hasAcq = !!unit.acq_map && Object.keys(unit.acq_map).length > 0;
                      const isBusy = middlewareCommandMutation.isPending || resumeMiddlewareMutation.isPending;
                      const unitStatus = unit.middleware_status || "-";
                      const runCommand = (action: string, message: string) => {
                        if (!window.confirm(message)) return;
                        middlewareCommandMutation.mutate({ unitNo: unit.unit_no, action });
                      };

                      return (
                        <tr key={unit.unit_no} className={unit.middleware_status === "ALARM" ? "bg-red-50/60" : unit.pending_stop ? "bg-yellow-50/60" : ""}>
                          <td className="font-medium">
                            Unit {unit.unit_no}
                            {unit.recipe_name && <div className="mt-1 text-[11px] text-orange-600 font-mono">{unit.recipe_name}</div>}
                          </td>
                          <td>
                            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusColors[unit.mes_status || ""] || "bg-gray-100 text-gray-700"}`}>
                              {unit.mes_status || "-"}
                            </span>
                          </td>
                          <td>
                            <div className="flex flex-wrap gap-1">
                              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${middlewareStatusClass(unit.middleware_status)}`}>
                                {unitStatus}
                              </span>
                              {unit.pending_stop && <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">정지예약</span>}
                            </div>
                          </td>
                          <td>
                            <div className="font-medium">{unit.current_step_id || "-"}</div>
                            {unit.activity?.label && <div className="text-xs text-gray-500 mt-1">{unit.activity.label}</div>}
                          </td>
                          <td>
                            {hasAcq ? (
                              <div className="flex flex-wrap gap-1">
                                {Object.entries(unit.acq_map || {}).map(([role, asset]) => (
                                  <span key={role} className="px-2 py-0.5 rounded bg-gray-100 text-gray-700 text-xs" title={role}>{String(asset)}</span>
                                ))}
                              </div>
                            ) : (
                              <span className="text-gray-400">-</span>
                            )}
                          </td>
                          <td className="max-w-[220px]">
                            {unit.alarm_message ? (
                              <span className="text-red-600 text-xs" title={unit.alarm_message}>
                                {unit.alarm_step_id ? `[${unit.alarm_step_id}] ` : ""}{unit.alarm_message}
                              </span>
                            ) : (
                              <span className="text-gray-400">-</span>
                            )}
                          </td>
                          <td>
                            <div className="flex flex-wrap gap-1">
                              {unit.middleware_status === "RUNNING" && (
                                <>
                                  {unit.pending_stop ? (
                                    <button
                                      onClick={() => runCommand("cancel-pending-stop", `Unit ${unit.unit_no}의 정지 예약을 취소하시겠습니까?`)}
                                      disabled={isBusy}
                                      className="inline-flex items-center gap-1 px-2 py-1 bg-yellow-100 text-yellow-800 hover:bg-yellow-200 rounded text-xs font-medium disabled:opacity-50"
                                    >
                                      <RotateCcw size={12} />
                                      예약취소
                                    </button>
                                  ) : (
                                    <>
                                      <button
                                        onClick={() => runCommand("stop", `Unit ${unit.unit_no}을(를) 즉시 정지하시겠습니까?`)}
                                        disabled={isBusy}
                                        className="inline-flex items-center gap-1 px-2 py-1 bg-red-100 text-red-700 hover:bg-red-200 rounded text-xs font-medium disabled:opacity-50"
                                      >
                                        <Square size={12} />
                                        정지
                                      </button>
                                      <button
                                        onClick={() => runCommand("stop-after-step", `Unit ${unit.unit_no}을(를) 현재 스텝 완료 후 정지하시겠습니까?`)}
                                        disabled={isBusy}
                                        className="inline-flex items-center gap-1 px-2 py-1 bg-yellow-100 text-yellow-800 hover:bg-yellow-200 rounded text-xs font-medium disabled:opacity-50"
                                      >
                                        <Pause size={12} />
                                        스텝후정지
                                      </button>
                                    </>
                                  )}
                                </>
                              )}
                              {unit.middleware_status === "STOPPED" && (
                                <>
                                  <button
                                    onClick={() => setResumeUnit(unit)}
                                    disabled={isBusy}
                                    className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 hover:bg-green-200 rounded text-xs font-medium disabled:opacity-50"
                                  >
                                    <StepForward size={12} />
                                    Resume
                                  </button>
                                  {hasAcq && (
                                    <button
                                      onClick={() => runCommand("release-resources", `Unit ${unit.unit_no}의 점유 자원을 해제하시겠습니까?`)}
                                      disabled={isBusy}
                                      className="px-2 py-1 bg-purple-100 text-purple-700 hover:bg-purple-200 rounded text-xs font-medium disabled:opacity-50"
                                    >
                                      Release
                                    </button>
                                  )}
                                </>
                              )}
                              {unit.middleware_status === "ALARM" && (
                                <>
                                  <button
                                    onClick={() => runCommand("clear-alarm", `Unit ${unit.unit_no}의 알람을 해제하시겠습니까?`)}
                                    disabled={isBusy}
                                    className="px-2 py-1 bg-gray-700 text-white hover:bg-gray-800 rounded text-xs font-medium disabled:opacity-50"
                                  >
                                    Clear
                                  </button>
                                  {hasAcq && (
                                    <button
                                      onClick={() => runCommand("release-resources", `Unit ${unit.unit_no}의 점유 자원을 해제하시겠습니까?`)}
                                      disabled={isBusy}
                                      className="px-2 py-1 bg-purple-100 text-purple-700 hover:bg-purple-200 rounded text-xs font-medium disabled:opacity-50"
                                    >
                                      Release
                                    </button>
                                  )}
                                </>
                              )}
                              {unit.middleware_status === "WAITING" && (
                                <span className="px-2 py-1 bg-gray-100 text-gray-500 rounded text-xs">직접 제어 없음</span>
                              )}
                              {!unit.middleware_status && (
                                <span className="px-2 py-1 bg-gray-100 text-gray-500 rounded text-xs">미들웨어 없음</span>
                              )}
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-center py-4 bg-gray-50 rounded-lg text-gray-400 text-sm">미들웨어 실행 유닛 정보가 없습니다.</p>
            )}
          </div>

          {/* Results Table */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-3">생산실적 ({orderResults.length}건)</h3>
            {orderResultsError && (
              <div className="mb-3 rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-700">
                생산실적을 불러오는 데 실패했습니다.
              </div>
            )}
            {orderResults.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="table text-sm">
                  <thead>
                    <tr>
                      <th>양품</th>
                      <th>불량</th>
                      <th>수율</th>
                      <th>설비</th>
                      <th>시작</th>
                      <th>종료</th>
                    </tr>
                  </thead>
                  <tbody>
                    {orderResults.map((r: ProdResult) => {
                      const total = r.ok_qty + r.ng_qty;
                      const yld = total > 0 ? (r.ok_qty / total) * 100 : 0;
                      return (
                        <tr key={r.id}>
                          <td className="text-green-600 font-medium">{r.ok_qty}</td>
                          <td className="text-red-600 font-medium">{r.ng_qty}</td>
                          <td>
                            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${yld >= 95 ? "bg-green-100 text-green-800" : yld >= 80 ? "bg-yellow-100 text-yellow-800" : "bg-red-100 text-red-800"}`}>
                              {yld.toFixed(1)}%
                            </span>
                          </td>
                          <td className="text-gray-500">{r.equipment_id ? `EQ-${r.equipment_id}` : "-"}</td>
                          <td className="text-gray-500">{r.start_time ? new Date(r.start_time).toLocaleString() : "-"}</td>
                          <td className="text-gray-500">{r.end_time ? new Date(r.end_time).toLocaleString() : "-"}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-center py-6 text-gray-400 text-sm">등록된 실적이 없습니다.</p>
            )}
          </div>

          {/* Unit Queue Monitor */}
          <div className="pt-4 border-t">
            <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center justify-between">
              <span>단위 생산 유닛 현황 (Unit Tracker)</span>
              {isLoadingUnits && <span className="text-xs text-primary-500 font-normal border border-primary-200 bg-primary-50 px-2 py-0.5 rounded">업데이트 중...</span>}
            </h3>
            {units.length > 0 ? (
              <div className="overflow-x-auto max-h-48 overflow-y-auto border border-gray-200 rounded-md">
                <table className="table text-sm w-full sticky-header">
                  <thead className="bg-gray-50 top-0 sticky">
                    <tr>
                      <th className="py-2">Unit No</th>
                      <th className="py-2">상태</th>
                      <th className="py-2">제어(Action)</th>
                      <th className="py-2">할당 시나리오(YAML)</th>
                      <th className="py-2">등록일시</th>
                      <th className="py-2">시작일시</th>
                      <th className="py-2">완료일시</th>
                    </tr>
                  </thead>
                  <tbody>
                    {units.map((u: ProductionUnit) => (
	                      <tr key={u.id} className="border-t border-gray-100">
	                        <td className="font-medium">Unit {u.unit_no}</td>
	                        <td>
	                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
	                            u.status === "READY" ? "bg-gray-100 text-gray-800" :
	                            u.status === "RUNNING" ? "bg-green-100 text-green-800 shadow-sm" :
	                            u.status === "PAUSED" ? "bg-yellow-100 text-yellow-800 shadow-sm" :
	                            u.status === "SCENARIO_HOLD" ? "bg-yellow-100 text-yellow-800 shadow-sm" :
	                            u.status === "DONE" ? "bg-primary-100 text-primary-800" :
	                            "bg-red-100 text-red-800"
	                          }`}>
	                            {u.status === "SCENARIO_HOLD" ? "SCENARIO HOLD" : u.status}
	                          </span>
                            {u.status === "SCENARIO_HOLD" && u.scenario_hold_by && (
                              <div className="mt-1 text-[11px] text-gray-500">
                                {u.scenario_hold_by}
                              </div>
                            )}
	                        </td>
	                        <td>
                          <div className="flex flex-wrap gap-1">
                            {u.status === "READY" && (
                              <button
                                onClick={() => holdUnitScenarioMutation.mutate(u)}
                                disabled={holdUnitScenarioMutation.isPending}
                                className="inline-flex items-center gap-1 px-2 py-1 bg-yellow-100 text-yellow-800 hover:bg-yellow-200 rounded text-xs font-medium"
                                title="유닛 시나리오 변경"
                              >
                                <FileEdit size={12} />
                                변경
                              </button>
                            )}
                            {u.status === "SCENARIO_HOLD" && (
                              <>
                                <button
                                  onClick={() => setScenarioChangeUnit(u)}
                                  disabled={updateUnitScenarioMutation.isPending || releaseUnitScenarioHoldMutation.isPending}
                                  className="inline-flex items-center gap-1 px-2 py-1 bg-yellow-100 text-yellow-800 hover:bg-yellow-200 rounded text-xs font-medium"
                                  title="유닛 시나리오 변경 계속"
                                >
                                  <FileEdit size={12} />
                                  계속
                                </button>
                                <button
                                  onClick={() => releaseUnitScenarioHoldMutation.mutate(u.id)}
                                  disabled={releaseUnitScenarioHoldMutation.isPending}
                                  className="px-2 py-1 bg-gray-100 text-gray-700 hover:bg-gray-200 rounded text-xs font-medium"
                                  title="시나리오 변경 보류 해제"
                                >
                                  해제
                                </button>
                              </>
                            )}
	                          {u.status === "RUNNING" && (
	                            <button
	                              onClick={() => {
                                  if (!window.confirm(`Unit ${u.unit_no}을(를) 즉시 정지하시겠습니까?`)) return;
                                  middlewareCommandMutation.mutate({ unitNo: String(u.unit_no), action: "stop" });
                                }}
	                              disabled={middlewareCommandMutation.isPending}
	                              className="px-2 py-1 bg-red-100 text-red-700 hover:bg-red-200 rounded text-xs font-medium"
                            >
                              ⏸ 정지
                            </button>
                          )}
                          {u.status === "PAUSED" && (
                            <button
                              onClick={() => {
                                const runtimeUnit = middlewareUnits.find((unit) => unit.unit_no === String(u.unit_no));
                                if (runtimeUnit?.middleware_status === "STOPPED") {
                                  setResumeUnit(runtimeUnit);
                                  return;
                                }
                                alert("미들웨어 Unit이 STOPPED 상태일 때만 재개할 수 있습니다. 위 실행 모니터링 상태를 확인해주세요.");
                              }}
                              disabled={resumeMiddlewareMutation.isPending}
                              className="px-2 py-1 bg-green-100 text-green-700 hover:bg-green-200 rounded text-xs font-medium"
                            >
	                              ▶ 재시작
	                            </button>
	                          )}
                          </div>
	                        </td>
	                        <td>
                          {u.scenario ? (
                            <span className="inline-flex items-center gap-1 bg-yellow-50 text-yellow-800 border border-yellow-200 px-2 py-0.5 rounded text-xs font-mono">
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                              </svg>
                              {u.scenario.file_path.split('/').pop()}
                            </span>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                        <td className="text-gray-500">{new Date(u.created_at).toLocaleString()}</td>
                        <td className="text-gray-500">{u.started_at ? new Date(u.started_at).toLocaleString() : "-"}</td>
                        <td className="text-gray-500">{u.completed_at ? new Date(u.completed_at).toLocaleString() : "-"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-center py-4 bg-gray-50 rounded-lg text-gray-400 text-sm">대기열에 등록된 유닛이 없습니다.</p>
            )}
          </div>

          {/* Actions */}
          <div className="flex justify-between pt-4 border-t">
            <div className="flex gap-2">
              {renderActionButtons(order)}
            </div>
            <button onClick={onClose} className="btn btn-secondary">
              닫기
            </button>
          </div>
        </div>
      </div>
      {scenarioChangeUnit && (
        <UnitScenarioChangeModal
          order={order}
          unit={scenarioChangeUnit}
          isSaving={updateUnitScenarioMutation.isPending}
          isReleasing={releaseUnitScenarioHoldMutation.isPending}
          onConfirm={(scenarioId) =>
            updateUnitScenarioMutation.mutate({ unitId: scenarioChangeUnit.id, scenarioId })
          }
          onRelease={() => releaseUnitScenarioHoldMutation.mutate(scenarioChangeUnit.id)}
          onClose={() => setScenarioChangeUnit(null)}
        />
      )}
      {resumeUnit && (
        <ResumeMiddlewareUnitModal
          unit={resumeUnit}
          isLoading={resumeMiddlewareMutation.isPending}
          onConfirm={(payload) =>
            resumeMiddlewareMutation.mutate({ unitNo: resumeUnit.unit_no, payload })
          }
          onClose={() => setResumeUnit(null)}
        />
      )}
    </div>
  );
}

function OrdersPageContent() {
  const queryClient = useQueryClient();
  const searchParams = useSearchParams();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showStartModal, setShowStartModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showMonitoringModal, setShowMonitoringModal] = useState(false);
  const [showScenarioModal, setShowScenarioModal] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState<WorkOrder | null>(null);
  const [orderToStart, setOrderToStart] = useState<WorkOrder | null>(null);
  const [orderToDelete, setOrderToDelete] = useState<WorkOrder | null>(null);
  const [orderToMonitor, setOrderToMonitor] = useState<WorkOrder | null>(null);
  const [orderToChangeScenario, setOrderToChangeScenario] = useState<WorkOrder | null>(null);

  // Get initial view and highlight from URL parameter
  const initialView = (searchParams.get("view") as "today" | "upcoming" | "active" | "all") || "today";
  const highlightWoId = searchParams.get("highlight");

  const [filters, setFilters] = useState<OrderFilters>({
    view: initialView,
    page: 1,
    limit: 30,
    sortBy: "plan_start",
    sortOrder: "asc",
  });

  // Update filters when URL changes
  useEffect(() => {
    const viewParam = searchParams.get("view") as "today" | "upcoming" | "active" | "all";
    if (viewParam) {
      setFilters((prev) => {
        if (prev.view === viewParam) return prev;
        return { ...prev, view: viewParam, page: 1 };
      });
    }
  }, [searchParams]);

  const [newOrder, setNewOrder] = useState({
    lot_no: "",
    product_id: 0,
    scenario_id: undefined as number | undefined,
    target_qty: 100,
    qty: 1,
    priority: 5,
    due_date: "",
    remarks: "",
  });

  // 선택된 제품에 연결된 시나리오 목록
  const { data: productScenarios } = useQuery({
    queryKey: ["scenarios-for-product", newOrder.product_id],
    queryFn: () => scenarioService.getAll(newOrder.product_id, true),
    enabled: newOrder.product_id > 0,
  });

  const { data: ordersData, isLoading, isError: isOrdersError } = useQuery({
    queryKey: ["orders", filters],
    queryFn: () => productionService.getOrders(filters),
    refetchInterval: POLLING.FAST,
  });

  // 제품 목록 조회 (드롭다운용)
  const { data: products, isError: isProductsError } = useQuery({
    queryKey: ["products-for-order"],
    queryFn: () => productService.getAll(),
  });

  // Fetch results for selected order (detail modal)
  const { data: orderResultsData, isError: isOrderResultsError } = useQuery({
    queryKey: ["order-results", selectedOrder?.id],
    queryFn: () => productionService.getResults({ workOrderId: selectedOrder?.id, limit: 100 }),
    enabled: !!selectedOrder,
  });

  // Build progress map from completed_qty on each WorkOrder (avoids 1000-record results fetch).
  // Falls back to 0 if field is not present.
  const progressMap = useMemo(() => {
    const map: Record<number, { ok: number; ng: number }> = {};
    for (const order of ordersData?.items || []) {
      map[order.id] = { ok: order.completed_qty ?? 0, ng: 0 };
    }
    return map;
  }, [ordersData]);

  const createMutation = useMutation({
    mutationFn: productionService.createOrder,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      setShowCreateModal(false);
      setNewOrder({ lot_no: "", product_id: 0, scenario_id: undefined, target_qty: 100, qty: 1, priority: 5, due_date: "", remarks: "" });
    },
    onError: (error: any) => {
      let message = "작업지시 생성 실패: ";

      if (error.code === "ERR_NETWORK") {
        message += "백엔드 서버에 연결할 수 없습니다. 서버 상태를 확인해주세요.";
      } else if (error.response?.status === 400) {
        const detail = error.response.data?.detail;
        if (detail?.includes("Product not found")) {
          message += "선택한 제품이 존재하지 않습니다.";
        } else if (detail?.includes("lot_no") || detail?.includes("duplicate")) {
          message += "이미 존재하는 작업번호입니다.";
        } else {
          message += detail || "입력 데이터를 확인해주세요.";
        }
      } else if (error.response?.status === 401) {
        message += "로그인이 필요합니다.";
      } else if (error.response?.status === 422) {
        message += "필수 항목이 누락되었습니다. 제품을 선택했는지 확인해주세요.";
      } else {
        message += error.message || "알 수 없는 오류가 발생했습니다.";
      }

      alert(message);
    },
  });

  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      productionService.updateOrderStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      // W1: Invalidate related queries across pages
      queryClient.invalidateQueries({ queryKey: ["results-for-progress"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-orders-stats"] });
      queryClient.invalidateQueries({ queryKey: ["order-results", selectedOrder?.id] });
    },
    onError: (error: any) => {
      alert(`상태 변경 실패: ${error.response?.data?.detail || error.message}`);
    },
  });

  const startMutation = useMutation({
    mutationFn: ({ id }: { id: number }) => productionService.startOrder(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-orders-stats"] });
      queryClient.invalidateQueries({ queryKey: ["order-results", selectedOrder?.id] });
      setShowStartModal(false);
      setOrderToStart(null);
    },
    onError: (error: any) => {
      alert(`시작 실패 (미들웨어 에러 등): ${error.response?.data?.detail || error.message}`);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: ({ id }: { id: number }) => productionService.deleteOrder(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-orders-stats"] });
      setShowDeleteModal(false);
      setOrderToDelete(null);
    },
    onError: (error: any) => {
      const detail = error.response?.data?.detail || error.message;
      alert(`작업지시 삭제 실패:\n${detail}`);
    },
  });

  const updateScenarioMutation = useMutation({
    mutationFn: ({ id, scenarioId }: { id: number; scenarioId: number }) => productionService.updateScenario(id, scenarioId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      queryClient.invalidateQueries({ queryKey: ["order-units"] });
      setShowScenarioModal(false);
      setOrderToChangeScenario(null);
      alert("시나리오 변경 및 대기열 동기화가 완료되었습니다.");
    },
    onError: (error: any) => {
      alert(`시나리오 변경 실패: ${error.response?.data?.detail || error.message}`);
    },
  });

  const handleStatusChange = (order: WorkOrder, newStatus: string) => {
    statusMutation.mutate({ id: order.id, status: newStatus });
  };

  const handleViewChange = (view: "today" | "upcoming" | "active" | "all") => {
    setFilters({ ...filters, view, page: 1 });
  };

  const handlePageChange = (newPage: number) => {
    setFilters({ ...filters, page: newPage });
  };

  const handleStartOrder = (order: WorkOrder) => {
    setOrderToStart(order);
    setShowStartModal(true);
  };

  const handleDeleteOrder = (order: WorkOrder) => {
    setOrderToDelete(order);
    setShowDeleteModal(true);
  };

  const handleSort = (field: string) => {
    if (filters.sortBy === field) {
      // Toggle order if same field
      setFilters({
        ...filters,
        sortOrder: filters.sortOrder === "asc" ? "desc" : "asc",
        page: 1
      });
    } else {
      // New field, default to asc
      setFilters({
        ...filters,
        sortBy: field as OrderFilters["sortBy"],
        sortOrder: "asc",
        page: 1
      });
    }
  };

  const handleViewDetail = (order: WorkOrder) => {
    setSelectedOrder(order);
    setShowDetailModal(true);
  };

  const handleChangeScenario = (order: WorkOrder) => {
    setOrderToChangeScenario(order);
    setShowScenarioModal(true);
  };

  const handleMonitorOrder = (order: WorkOrder) => {
    setOrderToMonitor(order);
    setShowMonitoringModal(true);
  };

  const renderActionButtons = (order: WorkOrder) => {
    switch (order.status) {
      case "READY":
      case "SCHEDULED":
        return (
          <>
            <button
              onClick={() => handleStartOrder(order)}
              className="p-1 text-green-600 hover:bg-green-50 rounded"
              title="작업 시작"
            >
              <Play size={18} />
            </button>
            <button
              onClick={() => handleDeleteOrder(order)}
              className="p-1 text-red-400 hover:bg-red-50 rounded"
              title="삭제"
            >
              <Trash2 size={18} />
            </button>
          </>
        );
      case "RUNNING":
        return (
          <>
            <button
              onClick={() => handleMonitorOrder(order)}
              className="p-1 text-primary-600 hover:bg-primary-50 rounded"
              title="상세 모니터링"
            >
              <Activity size={18} />
            </button>
            <button
              onClick={() => handleStatusChange(order, "PAUSE")}
              className="p-1 text-yellow-600 hover:bg-yellow-50 rounded"
              title="일시정지"
            >
              <Pause size={18} />
            </button>
            <button
              onClick={() => handleStatusChange(order, "DONE")}
              className="p-1 text-primary-600 hover:bg-primary-50 rounded"
              title="완료"
            >
              <CheckCircle size={18} />
            </button>
          </>
        );
      case "PAUSE":
        return (
          <>
            <button
              onClick={() => handleMonitorOrder(order)}
              className="p-1 text-primary-600 hover:bg-primary-50 rounded"
              title="상세 모니터링"
            >
              <Activity size={18} />
            </button>
            <button
              onClick={() => handleChangeScenario(order)}
              className="p-1 text-purple-600 hover:bg-purple-50 rounded bg-purple-50 border border-purple-200"
              title="시나리오 교체"
            >
              <FileEdit size={16} />
            </button>
            <button
              onClick={() => handleStatusChange(order, "RUNNING")}
              className="p-1 text-green-600 hover:bg-green-50 rounded"
              title="재시작"
            >
              <Play size={18} />
            </button>
            <button
              onClick={() => handleStatusChange(order, "DONE")}
              className="p-1 text-primary-600 hover:bg-primary-50 rounded"
              title="완료"
            >
              <CheckCircle size={18} />
            </button>
            <button
              onClick={() => handleDeleteOrder(order)}
              className="p-1 text-red-400 hover:bg-red-50 rounded"
              title="삭제"
            >
              <Trash2 size={18} />
            </button>
          </>
        );
      case "ERROR":
        return (
          <>
            <button
              onClick={() => handleMonitorOrder(order)}
              className="p-1 text-primary-600 hover:bg-primary-50 rounded"
              title="상세 모니터링"
            >
              <Activity size={18} />
            </button>
            <button
              onClick={() => handleStatusChange(order, "RUNNING")}
              className="p-1 text-green-600 hover:bg-green-50 rounded"
              title="재시작"
            >
              <Play size={18} />
            </button>
            <button
              onClick={() => handleDeleteOrder(order)}
              className="p-1 text-red-400 hover:bg-red-50 rounded"
              title="삭제"
            >
              <Trash2 size={18} />
            </button>
          </>
        );
      case "DONE":
        return (
          <>
            <button
              onClick={() => handleMonitorOrder(order)}
              className="p-1 text-primary-600 hover:bg-primary-50 rounded"
              title="결과 이력 모니터링"
            >
              <Activity size={18} />
            </button>
            <button
              onClick={() => handleDeleteOrder(order)}
              className="p-1 text-red-400 hover:bg-red-50 rounded"
              title="삭제"
            >
              <Trash2 size={18} />
            </button>
          </>
        );
      case "CANCEL":
        return (
          <button
            onClick={() => handleDeleteOrder(order)}
            className="p-1 text-red-400 hover:bg-red-50 rounded"
            title="삭제"
          >
            <Trash2 size={18} />
          </button>
        );
      default:
        return null;
    }
  };

  const orders = ordersData?.items || [];
  const totalItems = ordersData?.total || 0;
  const totalPages = ordersData?.pages || 1;
  const currentPage = filters.page || 1;

  // Scroll to highlighted order
  useEffect(() => {
    if (highlightWoId && orders.length > 0) {
      const el = document.getElementById("highlighted-order");
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }
  }, [highlightWoId, orders]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">작업지시</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn btn-primary flex items-center gap-2"
          aria-label="작업지시 생성"
        >
          <Plus size={16} />
          작업지시 생성
        </button>
      </div>

      {/* Error banners */}
      {isOrdersError && (
        <div className="rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-700">
          작업지시 목록을 불러오는 데 실패했습니다. 서버 상태를 확인해주세요.
        </div>
      )}
      {isProductsError && (
        <div className="rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-700">
          제품 목록을 불러오는 데 실패했습니다.
        </div>
      )}

      {/* View Tabs */}
      <div role="group" aria-label="작업 뷰 필터" className="flex gap-1 p-1 bg-gray-100 rounded-lg w-fit">
        {(["today", "upcoming", "active", "all"] as const).map((view) => (
          <button
            key={view}
            onClick={() => handleViewChange(view)}
            aria-label={viewLabels[view]}
            aria-pressed={filters.view === view}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${filters.view === view
              ? "bg-white text-primary-600 shadow-sm"
              : "text-gray-600 hover:text-gray-900"
              }`}
          >
            {viewLabels[view]}
          </button>
        ))}
      </div>

      {/* Orders Table */}
      {isLoading ? (
        <div className="text-center py-8 text-gray-500">로딩 중...</div>
      ) : orders.length > 0 ? (
        <>
          <div className="card overflow-hidden">
            <table className="table" aria-label="작업지시 목록">
              <thead>
                <tr>
                  <th scope="col" className="w-16">ID</th>
                  <th scope="col">Lot No</th>
                  <th scope="col">제품</th>
                  <th scope="col" className="w-24">목표수량</th>
                  <th className="w-20">
                    <SortableHeader
                      label="우선순위"
                      field="priority"
                      currentSort={filters.sortBy || "plan_start"}
                      currentOrder={filters.sortOrder || "asc"}
                      onSort={handleSort}
                    />
                  </th>
                  <th>배정설비</th>
                  <th className="w-20">상태</th>
                  <th>
                    <SortableHeader
                      label="계획시작"
                      field="plan_start"
                      currentSort={filters.sortBy || "plan_start"}
                      currentOrder={filters.sortOrder || "asc"}
                      onSort={handleSort}
                    />
                  </th>
                  <th>
                    <SortableHeader
                      label="납기일"
                      field="due_date"
                      currentSort={filters.sortBy || "plan_start"}
                      currentOrder={filters.sortOrder || "asc"}
                      onSort={handleSort}
                    />
                  </th>
                  <th className="w-28">진척</th>
                  <th className="w-24">액션</th>
                </tr>
              </thead>
              <tbody>
                {orders.map((order) => {
                  const isHighlighted = highlightWoId && order.lot_no === highlightWoId;

                  return (
                    <tr
                      key={order.id}
                      className={isHighlighted ? "bg-yellow-50 ring-2 ring-yellow-400 ring-inset" : ""}
                      id={isHighlighted ? "highlighted-order" : undefined}
                    >
                      <td className="text-gray-500 text-xs font-mono">
                        WO-{order.id}
                      </td>
                      <td className="font-medium">{order.lot_no}</td>
                      <td>
                        {order.product ? (
                          <span title={`ID: ${order.product_id}`}>
                            {order.product.code} - {order.product.name}
                          </span>
                        ) : (
                          <span className="text-gray-400">#{order.product_id}</span>
                        )}
                      </td>
                      <td>{order.target_qty.toLocaleString()}</td>
                      <td>
                        <span
                          className={`px-2 py-1 rounded-full text-xs font-medium ${order.priority <= 3
                            ? "bg-red-100 text-red-800"
                            : order.priority <= 6
                              ? "bg-yellow-100 text-yellow-800"
                              : "bg-gray-100 text-gray-800"
                            }`}
                        >
                          {order.priority}
                        </span>
                      </td>
                      <td className="text-sm">
                        {order.scheduled_equipment_name ? (
                          <span className="text-primary-600 font-medium">{order.scheduled_equipment_name}</span>
                        ) : (
                          <span className="text-gray-400">미배정</span>
                        )}
                      </td>
                      <td>
                        <span
                          className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[order.status] || "bg-gray-100"
                            }`}
                        >
                          {statusLabels[order.status] || order.status}
                        </span>
                      </td>
                      <td className="text-sm">
                        {order.plan_start ? (
                          <span className="text-gray-700">
                            {new Date(order.plan_start).toLocaleString()}
                          </span>
                        ) : (
                          <span className="text-gray-400">미정</span>
                        )}
                      </td>
                      <td className="text-sm">
                        {order.due_date ? (
                          <span className="text-gray-700">{new Date(order.due_date).toLocaleString()}</span>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                      <td>
                        {order.status === "DONE" ? (
                          <div className="flex items-center gap-1 text-green-600">
                            <CheckCircle size={14} />
                            <span className="text-xs font-medium">완료</span>
                          </div>
                        ) : (() => {
                          const progress = progressMap[order.id];
                          const okSum = progress?.ok || 0;
                          const pct = order.target_qty > 0 ? Math.min((okSum / order.target_qty) * 100, 100) : 0;
                          const barColor = pct >= 95 ? "bg-green-500" : pct >= 50 ? "bg-primary-500" : "bg-gray-400";
                          return (
                            <div className="w-full">
                              <div className="flex items-center justify-between text-xs mb-1">
                                <span className="text-gray-600">{okSum}/{order.target_qty}</span>
                                <span className="font-medium">{pct.toFixed(0)}%</span>
                              </div>
                              <div className="w-full bg-gray-200 rounded-full h-2">
                                <div className={`${barColor} h-2 rounded-full transition-all`} style={{ width: `${pct}%` }} />
                              </div>
                            </div>
                          );
                        })()}
                      </td>
                      <td>
                        <div className="flex gap-1">
                          <button
                            onClick={() => handleViewDetail(order)}
                            className="p-1 text-primary-600 hover:bg-primary-50 rounded"
                            title="상세보기"
                          >
                            <Eye size={18} />
                          </button>
                          {renderActionButtons(order)}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-500">
              총 {totalItems}건 중{" "}
              {Math.min((currentPage - 1) * (filters.limit || 30) + 1, totalItems)}-
              {Math.min(currentPage * (filters.limit || 30), totalItems)}건
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage <= 1}
                className="p-2 rounded-md border border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                <ChevronLeft size={16} />
              </button>
              <span className="px-3 py-1 text-sm">
                {currentPage} / {totalPages}
              </span>
              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage >= totalPages}
                className="p-2 rounded-md border border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        </>
      ) : (
        <div className="text-center py-12 bg-white rounded-lg border border-dashed border-gray-300">
          <p className="text-gray-500 mb-4">
            {filters.view === "today" && "오늘 계획된 작업이 없습니다."}
            {filters.view === "upcoming" && "예정된 작업이 없습니다."}
            {filters.view === "active" && "진행중인 작업이 없습니다."}
            {filters.view === "all" && "작업지시가 없습니다."}
          </p>
          <button onClick={() => setShowCreateModal(true)} className="btn btn-primary">
            작업지시 생성
          </button>
        </div>
      )}

      {/* Detail Modal */}
      {showDetailModal && selectedOrder && (
        <OrderDetailModal
          order={selectedOrder}
          progressMap={progressMap}
          orderResults={orderResultsData?.items || []}
          orderResultsError={!!isOrderResultsError}
          onClose={() => { setShowDetailModal(false); setSelectedOrder(null); }}
          renderActionButtons={renderActionButtons}
        />
      )}

      {/* Start Context Modal */}
      {showStartModal && orderToStart && (
        <ConfirmStartModal
          order={orderToStart}
          isLoading={startMutation.isPending}
          onConfirm={() => startMutation.mutate({ id: orderToStart.id })}
          onClose={() => { setShowStartModal(false); setOrderToStart(null); }}
        />
      )}

      {/* Delete Confirm Modal */}
      {showDeleteModal && orderToDelete && (
        <ConfirmDeleteModal
          order={orderToDelete}
          isLoading={deleteMutation.isPending}
          onConfirm={() => deleteMutation.mutate({ id: orderToDelete.id })}
          onClose={() => { setShowDeleteModal(false); setOrderToDelete(null); }}
        />
      )}

      {/* Change Scenario Modal */}
      {showScenarioModal && orderToChangeScenario && (
        <ChangeScenarioModal
          order={orderToChangeScenario}
          isLoading={updateScenarioMutation.isPending}
          onConfirm={(scenarioId) => updateScenarioMutation.mutate({ id: orderToChangeScenario.id, scenarioId })}
          onClose={() => { setShowScenarioModal(false); setOrderToChangeScenario(null); }}
        />
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="text-lg font-semibold">작업지시 생성</h2>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-2 hover:bg-gray-100 rounded"
              >
                <X size={20} />
              </button>
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                // Convert empty strings to undefined for optional fields
                const orderData = {
                  ...newOrder,
                  due_date: newOrder.due_date || undefined,
                  remarks: newOrder.remarks || undefined,
                  scenario_id: newOrder.scenario_id || undefined,
                };
                createMutation.mutate(orderData);
              }}
              className="p-4 space-y-4"
            >
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Lot No
                </label>
                <input
                  type="text"
                  value={newOrder.lot_no}
                  onChange={(e) => setNewOrder({ ...newOrder, lot_no: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md"
                  placeholder="LOT-YYYYMMDD-001"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  제품 선택
                </label>
                <select
                  value={newOrder.product_id || ""}
                  onChange={(e) => {
                    const productId = parseInt(e.target.value) || 0;
                    setNewOrder({ ...newOrder, product_id: productId, scenario_id: undefined });
                  }}
                  className="w-full px-3 py-2 border rounded-md bg-white"
                  required
                >
                  <option value="">제품을 선택하세요...</option>
                  {products?.map((product) => (
                    <option key={product.id} value={product.id}>
                      {product.code} - {product.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* 시나리오 — 제품 선택 후 자동 표시 */}
              {newOrder.product_id > 0 && (() => {
                const scenarios = productScenarios ?? [];
                if (scenarios.length === 0) {
                  return (
                    <div className="text-xs text-gray-400 bg-gray-50 px-3 py-2 rounded-md border border-gray-200">
                      이 제품에 연결된 시나리오가 없습니다.
                    </div>
                  );
                }
                if (scenarios.length === 1) {
                  // 자동 세팅
                  if (newOrder.scenario_id !== scenarios[0].id) {
                    setTimeout(() => setNewOrder((prev) => ({ ...prev, scenario_id: scenarios[0].id })), 0);
                  }
                  return (
                    <div className="text-xs text-primary-700 bg-primary-50 px-3 py-2 rounded-md border border-primary-200">
                      시나리오 자동 선택됨: <strong>{scenarios[0].name}</strong> ({scenarios[0].file_path})
                    </div>
                  );
                }
                return (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      시나리오 선택
                    </label>
                    <select
                      value={newOrder.scenario_id ?? ""}
                      onChange={(e) =>
                        setNewOrder({ ...newOrder, scenario_id: parseInt(e.target.value) || undefined })
                      }
                      className="w-full px-3 py-2 border rounded-md bg-white"
                    >
                      <option value="">시나리오를 선택하세요...</option>
                      {scenarios.map((s: any) => (
                        <option key={s.id} value={s.id}>
                          {s.name} ({s.file_path})
                        </option>
                      ))}
                    </select>
                  </div>
                );
              })()}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  목표 수량
                </label>
                <input
                  type="number"
                  value={newOrder.target_qty}
                  onChange={(e) =>
                    setNewOrder({ ...newOrder, target_qty: parseInt(e.target.value) })
                  }
                  className="w-full px-3 py-2 border rounded-md"
                  min="1"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    주문 수량
                  </label>
                  <input
                    type="number"
                    value={newOrder.qty}
                    onChange={(e) =>
                      setNewOrder({ ...newOrder, qty: parseInt(e.target.value) || 1 })
                    }
                    className="w-full px-3 py-2 border rounded-md"
                    min="1"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    우선순위 (1=높음, 10=낮음)
                  </label>
                  <input
                    type="number"
                    value={newOrder.priority}
                    onChange={(e) =>
                      setNewOrder({ ...newOrder, priority: parseInt(e.target.value) || 5 })
                    }
                    className="w-full px-3 py-2 border rounded-md"
                    min="1"
                    max="10"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  납기일
                </label>
                <input
                  type="datetime-local"
                  value={newOrder.due_date}
                  onChange={(e) =>
                    setNewOrder({ ...newOrder, due_date: e.target.value })
                  }
                  className="w-full px-3 py-2 border rounded-md"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  비고
                </label>
                <textarea
                  value={newOrder.remarks}
                  onChange={(e) =>
                    setNewOrder({ ...newOrder, remarks: e.target.value })
                  }
                  className="w-full px-3 py-2 border rounded-md"
                  rows={2}
                  placeholder="추가 정보..."
                />
              </div>

              <div className="flex justify-end gap-2 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="btn btn-secondary"
                >
                  취소
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="btn btn-primary"
                >
                  {createMutation.isPending ? "생성 중..." : "생성"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Monitoring Modal */}
      {showMonitoringModal && orderToMonitor && (
        <LotMonitoringModal
          order={orderToMonitor}
          onClose={() => {
            setShowMonitoringModal(false);
            setOrderToMonitor(null);
          }}
        />
      )}
    </div>
  );
}

export default function OrdersPage() {
  return (
    <ErrorBoundary>
      <OrdersPageContent />
    </ErrorBoundary>
  );
}
