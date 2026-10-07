"use client";

import { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { downtimeService, downtimeReasonService } from "@/services/downtime";
import { equipmentService } from "@/services/equipment";
import { Downtime, DowntimeReason, Equipment } from "@/types";
import ErrorBoundary from "@/components/ErrorBoundary";
import { SchedulerGanttChart, GanttResource } from "@/components/scheduler";
import { useDowntimeForGantt } from "@/hooks/useScheduler";
import { format } from "date-fns";
import {
  Plus,
  X,
  Clock,
  StopCircle,
  Wrench,
  AlertTriangle,
  Timer,
  Calendar,
  Filter,
  RefreshCw,
} from "lucide-react";
import { POLLING } from "@/config/constants";

const CATEGORY_CONFIG: Record<string, { label: string; color: string; icon: any }> = {
  PLANNED: { label: "계획 정지", color: "bg-primary-100 text-primary-800", icon: Calendar },
  UNPLANNED: { label: "비계획 정지", color: "bg-red-100 text-red-800", icon: AlertTriangle },
  MAINTENANCE: { label: "정비", color: "bg-yellow-100 text-yellow-800", icon: Wrench },
  SETUP: { label: "셋업", color: "bg-purple-100 text-purple-800", icon: Timer },
  OTHER: { label: "기타", color: "bg-gray-100 text-gray-800", icon: Clock },
};

function DowntimePageContent() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<"active" | "completed">("active");
  const [showModal, setShowModal] = useState(false);
  const [endingId, setEndingId] = useState<number | null>(null);
  const [ganttDate, setGanttDate] = useState(format(new Date(), "yyyy-MM-dd"));
  const [formData, setFormData] = useState({
    equipment_id: "",
    reason_id: "",
    start_time: "",
    remarks: "",
  });

  // Queries
  const { data: activeDowntimes, isLoading: activeLoading } = useQuery({
    queryKey: ["downtime", "active"],
    queryFn: downtimeService.getActive,
    refetchInterval: POLLING.FAST,
  });

  const { data: completedDowntimes, isLoading: completedLoading } = useQuery({
    queryKey: ["downtime", "completed"],
    queryFn: () => downtimeService.getAll({ status: "COMPLETED", limit: 100 }),
    enabled: activeTab === "completed",
  });

  const { data: reasons } = useQuery({
    queryKey: ["downtime-reasons"],
    queryFn: () => downtimeReasonService.getAll(true),
  });

  const { data: equipments } = useQuery({
    queryKey: ["equipments"],
    queryFn: () => equipmentService.getAll(),
  });

  const { data: summary } = useQuery({
    queryKey: ["downtime", "summary"],
    queryFn: () => downtimeService.getSummary(),
  });

  // Downtime Gantt
  const { tasks: ganttTasks, isLoading: ganttLoading } = useDowntimeForGantt(ganttDate);

  const ganttResources = useMemo((): GanttResource[] => {
    if (!equipments) return [];
    return equipments.map((eq) => ({
      id: `EQ-${eq.id}`,
      name: eq.eq_code ? `[${eq.eq_code}] ${eq.eq_name}` : eq.eq_name,
      type: eq.equipment_type || undefined,
    }));
  }, [equipments]);

  // Mutations
  const startMutation = useMutation({
    mutationFn: downtimeService.start,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["downtime"] });
      queryClient.invalidateQueries({ queryKey: ["downtime-gantt"] });
      closeModal();
    },
    onError: (error: any) => {
      alert(`다운타임 시작 실패: ${error.response?.data?.detail || error.message}`);
    },
  });

  const endMutation = useMutation({
    mutationFn: (id: number) => downtimeService.end(id),
    onSuccess: () => {
      setEndingId(null);
      queryClient.invalidateQueries({ queryKey: ["downtime"] });
      queryClient.invalidateQueries({ queryKey: ["downtime-gantt"] });
      // W1+W5: Invalidate equipment status and ensure completed tab refreshes
      queryClient.invalidateQueries({ queryKey: ["equipments"] });
    },
    onError: (error: any) => {
      setEndingId(null);
      alert(`다운타임 종료 실패: ${error.response?.data?.detail || error.message}`);
    },
  });

  const closeModal = () => {
    setShowModal(false);
    setFormData({ equipment_id: "", reason_id: "", start_time: "", remarks: "" });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    startMutation.mutate({
      equipment_id: parseInt(formData.equipment_id),
      reason_id: parseInt(formData.reason_id),
      start_time: formData.start_time || undefined,
      remarks: formData.remarks || undefined,
    });
  };

  const getEquipmentName = (equipmentId: number) => {
    const eq = equipments?.find((e) => e.id === equipmentId);
    return eq ? `${eq.eq_code || ""} ${eq.eq_name}`.trim() : `설비 #${equipmentId}`;
  };

  const getReasonInfo = (reasonId: number) => {
    return reasons?.find((r) => r.id === reasonId);
  };

  const formatDuration = (startTime: string, endTime?: string | null) => {
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const diffMs = end.getTime() - start.getTime();
    if (diffMs <= 0) return "-";
    const mins = Math.floor(diffMs / 60000);
    if (mins < 60) return `${mins}분`;
    const hours = Math.floor(mins / 60);
    const remainMins = mins % 60;
    return `${hours}시간 ${remainMins}분`;
  };

  const formatDurationSec = (seconds: number) => {
    if (seconds < 60) return `${seconds}초`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}분`;
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    return `${hours}시간 ${mins}분`;
  };

  const filteredReasons = useMemo(() => {
    if (!reasons || !formData.equipment_id) return reasons;
    // 설비 선택 시 해당 설비와 관련된 사유만 필터링 (필요시)
    return reasons;
  }, [reasons, formData.equipment_id]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">다운타임 관리</h1>
          <p className="text-sm text-gray-500">설비 정지 시간을 기록하고 분석합니다.</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="btn btn-primary flex items-center gap-2"
        >
          <Plus size={16} />
          다운타임 기록
        </button>
      </div>

      {/* Summary Cards */}
      {summary && summary.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {Object.entries(CATEGORY_CONFIG).map(([category, config]) => {
            const data = summary.find((s) => s.category === category);
            const IconComponent = config.icon;
            return (
              <div key={category} className="card p-4">
                <div className="flex items-center gap-2 mb-2">
                  <IconComponent size={16} className="text-gray-500" />
                  <span className="text-sm font-medium text-gray-600">{config.label}</span>
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-bold">{data?.count || 0}</span>
                  <span className="text-xs text-gray-500">건</span>
                </div>
                {data?.total_duration_sec && (
                  <p className="text-xs text-gray-400 mt-1">
                    총 {formatDurationSec(data.total_duration_sec)}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Gantt Timeline */}
      <div className="space-y-3">
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-semibold text-gray-700">다운타임 타임라인</h2>
          <input
            type="date"
            value={ganttDate}
            onChange={(e) => setGanttDate(e.target.value)}
            className="px-3 py-1.5 border rounded-md text-sm"
          />
          <button
            onClick={() => setGanttDate(format(new Date(), "yyyy-MM-dd"))}
            className="btn btn-secondary text-sm"
          >
            오늘
          </button>
        </div>
        {ganttLoading ? (
          <div className="card text-center py-8">
            <RefreshCw className="animate-spin mx-auto mb-2 text-gray-400" size={24} />
            <p className="text-gray-500">로딩 중...</p>
          </div>
        ) : ganttResources.length > 0 ? (
          <SchedulerGanttChart
            title={`${ganttDate} 다운타임 타임라인`}
            tasks={ganttTasks}
            resources={ganttResources}
            horizonStart={`${ganttDate}T00:00:00`}
            horizonEnd={`${ganttDate}T23:59:59`}
          />
        ) : null}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b">
        <button
          onClick={() => setActiveTab("active")}
          className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
            activeTab === "active"
              ? "border-primary-600 text-primary-600"
              : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          진행 중 {activeDowntimes && `(${activeDowntimes.length})`}
        </button>
        <button
          onClick={() => setActiveTab("completed")}
          className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
            activeTab === "completed"
              ? "border-primary-600 text-primary-600"
              : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          완료됨
        </button>
      </div>

      {/* Active Downtimes */}
      {activeTab === "active" && (
        <div>
          {activeLoading ? (
            <div className="text-center py-8 text-gray-500">로딩 중...</div>
          ) : activeDowntimes && activeDowntimes.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {activeDowntimes.map((dt) => {
                const reason = getReasonInfo(dt.reason_id);
                const categoryConfig = reason
                  ? CATEGORY_CONFIG[reason.category] || CATEGORY_CONFIG.OTHER
                  : CATEGORY_CONFIG.OTHER;

                return (
                  <div key={dt.id} className="card p-4 border-l-4 border-l-red-500">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="font-semibold">{getEquipmentName(dt.equipment_id)}</h3>
                        <span className={`inline-block mt-1 px-2 py-0.5 rounded text-xs font-medium ${categoryConfig.color}`}>
                          {reason?.name || "알 수 없음"}
                        </span>
                      </div>
                      <div className="text-right">
                        <div className="flex items-center gap-1 text-red-600 font-mono font-bold">
                          <Clock size={14} className="animate-pulse" />
                          {formatDuration(dt.start_time)}
                        </div>
                      </div>
                    </div>

                    <div className="mt-3 text-sm text-gray-500">
                      <p>시작: {new Date(dt.start_time).toLocaleString()}</p>
                      {dt.remarks && <p className="mt-1 italic">"{dt.remarks}"</p>}
                    </div>

                    <div className="mt-4">
                      <button
                        onClick={() => {
                          if (confirm("다운타임을 종료하시겠습니까?")) {
                            setEndingId(dt.id);
                            endMutation.mutate(dt.id);
                          }
                        }}
                        disabled={endingId === dt.id}
                        className="btn btn-success w-full flex items-center justify-center gap-2"
                      >
                        <StopCircle size={16} />
                        {endingId === dt.id ? "종료 중..." : "종료"}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-12 bg-white rounded-lg border border-dashed border-gray-300">
              <Clock size={48} className="mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500">현재 진행 중인 다운타임이 없습니다.</p>
            </div>
          )}
        </div>
      )}

      {/* Completed Downtimes */}
      {activeTab === "completed" && (
        <div>
          {completedLoading ? (
            <div className="text-center py-8 text-gray-500">로딩 중...</div>
          ) : completedDowntimes && completedDowntimes.length > 0 ? (
            <div className="card overflow-hidden">
              <table className="table">
                <thead>
                  <tr>
                    <th>설비</th>
                    <th>사유</th>
                    <th>시작시간</th>
                    <th>종료시간</th>
                    <th>소요시간</th>
                    <th>비고</th>
                  </tr>
                </thead>
                <tbody>
                  {completedDowntimes.map((dt) => {
                    const reason = getReasonInfo(dt.reason_id);
                    const categoryConfig = reason
                      ? CATEGORY_CONFIG[reason.category] || CATEGORY_CONFIG.OTHER
                      : CATEGORY_CONFIG.OTHER;

                    return (
                      <tr key={dt.id}>
                        <td className="font-medium">{getEquipmentName(dt.equipment_id)}</td>
                        <td>
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${categoryConfig.color}`}>
                            {reason?.name || "알 수 없음"}
                          </span>
                        </td>
                        <td className="text-sm text-gray-500">
                          {new Date(dt.start_time).toLocaleString()}
                        </td>
                        <td className="text-sm text-gray-500">
                          {dt.end_time ? new Date(dt.end_time).toLocaleString() : "-"}
                        </td>
                        <td className="font-mono text-sm">
                          {dt.duration_sec
                            ? formatDurationSec(dt.duration_sec)
                            : dt.end_time
                              ? formatDuration(dt.start_time, dt.end_time)
                              : "-"}
                        </td>
                        <td className="text-sm text-gray-500 max-w-xs truncate">
                          {dt.remarks || "-"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-12 bg-white rounded-lg border border-dashed border-gray-300">
              <p className="text-gray-500">완료된 다운타임 기록이 없습니다.</p>
            </div>
          )}
        </div>
      )}

      {/* Create Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="text-lg font-semibold">다운타임 기록</h2>
              <button onClick={closeModal} className="p-2 hover:bg-gray-100 rounded">
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  설비 선택 <span className="text-red-500">*</span>
                </label>
                <select
                  value={formData.equipment_id}
                  onChange={(e) => setFormData({ ...formData, equipment_id: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md"
                  required
                >
                  <option value="">설비를 선택하세요</option>
                  {equipments?.map((eq) => (
                    <option key={eq.id} value={eq.id}>
                      {eq.eq_code ? `[${eq.eq_code}] ` : ""}{eq.eq_name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  정지 사유 <span className="text-red-500">*</span>
                </label>
                <select
                  value={formData.reason_id}
                  onChange={(e) => setFormData({ ...formData, reason_id: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md"
                  required
                >
                  <option value="">사유를 선택하세요</option>
                  {Object.entries(CATEGORY_CONFIG).map(([category, config]) => {
                    const categoryReasons = filteredReasons?.filter((r) => r.category === category);
                    if (!categoryReasons?.length) return null;
                    return (
                      <optgroup key={category} label={config.label}>
                        {categoryReasons.map((r) => (
                          <option key={r.id} value={r.id}>
                            {r.name}
                          </option>
                        ))}
                      </optgroup>
                    );
                  })}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  시작 시간 (선택)
                </label>
                <input
                  type="datetime-local"
                  value={formData.start_time}
                  onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md"
                />
                <p className="mt-1 text-xs text-gray-500">비워두면 현재 시간으로 기록됩니다.</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  비고
                </label>
                <textarea
                  value={formData.remarks}
                  onChange={(e) => setFormData({ ...formData, remarks: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md"
                  rows={2}
                  placeholder="추가 설명..."
                />
              </div>

              <div className="flex justify-end gap-2 pt-4">
                <button type="button" onClick={closeModal} className="btn btn-secondary">
                  취소
                </button>
                <button
                  type="submit"
                  disabled={startMutation.isPending}
                  className="btn btn-primary"
                >
                  {startMutation.isPending ? "기록 중..." : "기록 시작"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default function DowntimePage() {
  return (
    <ErrorBoundary>
      <DowntimePageContent />
    </ErrorBoundary>
  );
}
