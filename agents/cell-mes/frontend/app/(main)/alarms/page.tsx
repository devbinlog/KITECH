"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { alarmService } from "@/services/alarm";
import { equipmentService } from "@/services/equipment";
import { Alarm } from "@/types";
import ErrorBoundary from "@/components/ErrorBoundary";
import {
  Bell,
  BellOff,
  Check,
  X,
  AlertTriangle,
  AlertCircle,
  Info,
  Filter,
  RefreshCw,
} from "lucide-react";
import { POLLING } from "@/config/constants";

const SEVERITY_CONFIG: Record<string, { label: string; color: string; bgColor: string; borderColor: string; icon: any }> = {
  EMERGENCY: { label: "긴급", color: "text-red-700", bgColor: "bg-red-100", borderColor: "#dc2626", icon: AlertTriangle },
  CRITICAL: { label: "심각", color: "text-red-700", bgColor: "bg-red-100", borderColor: "#dc2626", icon: AlertTriangle },
  MAJOR: { label: "중요", color: "text-orange-700", bgColor: "bg-orange-100", borderColor: "#ea580c", icon: AlertCircle },
  WARNING: { label: "경고", color: "text-yellow-700", bgColor: "bg-yellow-100", borderColor: "#ca8a04", icon: AlertCircle },
  MINOR: { label: "경미", color: "text-yellow-700", bgColor: "bg-yellow-100", borderColor: "#ca8a04", icon: AlertCircle },
  INFO: { label: "정보", color: "text-primary-700", bgColor: "bg-primary-100", borderColor: "#2563eb", icon: Info },
};

function AlarmsPageContent() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<"active" | "history">("active");
  const [selectedSeverity, setSelectedSeverity] = useState<string>("");
  const [pendingAckId, setPendingAckId] = useState<number | null>(null);
  const [pendingClearId, setPendingClearId] = useState<number | null>(null);

  // Queries
  const { data: activeAlarms, isLoading: activeLoading, refetch } = useQuery({
    queryKey: ["alarms", "active"],
    queryFn: alarmService.getActive,
    refetchInterval: POLLING.FAST,
  });

  const { data: alarmHistory, isLoading: historyLoading, isError: isHistoryError } = useQuery({
    queryKey: ["alarms", "history", selectedSeverity],
    queryFn: () => alarmService.getAll({
      status: "RESOLVED",
      severity: selectedSeverity || undefined,
      limit: 100,
    }),
    enabled: activeTab === "history",
  });

  const { data: equipments } = useQuery({
    queryKey: ["equipments"],
    queryFn: () => equipmentService.getAll(),
  });

  const { data: summary } = useQuery({
    queryKey: ["alarms", "summary"],
    queryFn: () => alarmService.getSummary(),
  });

  // Mutations
  const acknowledgeMutation = useMutation({
    mutationFn: (id: number) => alarmService.acknowledge(id),
    onMutate: (id: number) => { setPendingAckId(id); },
    onSettled: () => { setPendingAckId(null); },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alarms"] });
    },
    onError: (error: any) => {
      alert(`알람 확인 실패: ${error.response?.data?.detail || error.message}`);
    },
  });

  const clearMutation = useMutation({
    mutationFn: (id: number) => alarmService.clear(id),
    onMutate: (id: number) => { setPendingClearId(id); },
    onSettled: () => { setPendingClearId(null); },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alarms"] });
    },
    onError: (error: any) => {
      alert(`알람 해제 실패: ${error.response?.data?.detail || error.message}`);
    },
  });

  const getEquipmentName = (equipmentId: number) => {
    const eq = equipments?.find((e) => e.id === equipmentId);
    return eq ? `${eq.eq_code || ""} ${eq.eq_name}`.trim() : `설비 #${equipmentId}`;
  };

  const getSeverityConfig = (severity: string) => {
    return SEVERITY_CONFIG[severity] || SEVERITY_CONFIG.INFO;
  };

  // Group active alarms by severity (from nested definition)
  const groupedActiveAlarms = activeAlarms?.reduce((acc, alarm) => {
    const severity = alarm.definition?.severity || "INFO";
    if (!acc[severity]) acc[severity] = [];
    acc[severity].push(alarm);
    return acc;
  }, {} as Record<string, Alarm[]>);

  // Count by severity for summary
  const severityCounts = activeAlarms?.reduce((acc, alarm) => {
    const severity = alarm.definition?.severity || "INFO";
    acc[severity] = (acc[severity] || 0) + 1;
    return acc;
  }, {} as Record<string, number>) || {};

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">알람 관리</h1>
          <p className="text-sm text-gray-500">설비 알람을 모니터링하고 관리합니다.</p>
        </div>
        <button
          onClick={() => refetch()}
          className="btn btn-secondary flex items-center gap-2"
        >
          <RefreshCw size={16} />
          새로고침
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {Object.entries(SEVERITY_CONFIG).map(([severity, config]) => {
          const count = severityCounts[severity] || 0;
          const IconComponent = config.icon;
          const isActive = count > 0;
          return (
            <div
              key={severity}
              className={`card p-4 transition-all ${
                isActive ? `border-l-4 ${config.bgColor}` : ""
              }`}
              style={{ borderLeftColor: isActive ? undefined : "transparent" }}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <IconComponent size={20} className={isActive ? config.color : "text-gray-400"} />
                  <span className="text-sm font-medium text-gray-600">{config.label}</span>
                </div>
                <span className={`text-2xl font-bold ${isActive ? config.color : "text-gray-400"}`}>
                  {count}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b">
        <button
          onClick={() => setActiveTab("active")}
          className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === "active"
              ? "border-primary-600 text-primary-600"
              : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          <Bell size={16} />
          활성 알람 {activeAlarms && `(${activeAlarms.length})`}
        </button>
        <button
          onClick={() => setActiveTab("history")}
          className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === "history"
              ? "border-primary-600 text-primary-600"
              : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          <BellOff size={16} />
          알람 이력
        </button>
      </div>

      {/* Active Alarms */}
      {activeTab === "active" && (
        <div>
          {activeLoading ? (
            <div className="text-center py-8 text-gray-500">로딩 중...</div>
          ) : activeAlarms && activeAlarms.length > 0 ? (
            <div className="space-y-6">
              {["EMERGENCY", "CRITICAL", "MAJOR", "WARNING", "MINOR", "INFO"].map((severity) => {
                const alarms = groupedActiveAlarms?.[severity];
                if (!alarms?.length) return null;
                const config = getSeverityConfig(severity);
                const IconComponent = config.icon;

                return (
                  <div key={severity}>
                    <h3 className={`text-sm font-semibold mb-3 flex items-center gap-2 ${config.color}`}>
                      <IconComponent size={16} />
                      {config.label} ({alarms.length})
                    </h3>
                    <div className="space-y-2">
                      {alarms.map((alarm) => (
                        <div
                          key={alarm.id}
                          className={`card p-4 border-l-4 ${config.bgColor}`}
                          style={{ borderLeftColor: config.borderColor }}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="font-semibold">{getEquipmentName(alarm.equipment_id)}</span>
                                <code className="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-mono">
                                  {alarm.definition?.code || "-"}
                                </code>
                              </div>
                              <p className="text-sm text-gray-700">{alarm.message}</p>
                              <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                                <span>발생: {new Date(alarm.occurred_at).toLocaleString()}</span>
                                {alarm.acknowledged_at && (
                                  <span className="text-green-600">
                                    ✓ 확인됨 ({alarm.acknowledged_by})
                                  </span>
                                )}
                              </div>
                            </div>
                            <div className="flex items-center gap-2 ml-4">
                              {!alarm.acknowledged_at && (
                                <button
                                  onClick={() => acknowledgeMutation.mutate(alarm.id)}
                                  disabled={pendingAckId === alarm.id}
                                  className="btn btn-secondary btn-sm flex items-center gap-1"
                                  title="확인"
                                >
                                  <Check size={14} />
                                  확인
                                </button>
                              )}
                              <button
                                onClick={() => {
                                  if (confirm("알람을 해제하시겠습니까?")) {
                                    clearMutation.mutate(alarm.id);
                                  }
                                }}
                                disabled={pendingClearId === alarm.id}
                                className="btn btn-success btn-sm flex items-center gap-1"
                                title="해제"
                              >
                                <X size={14} />
                                해제
                              </button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-12 bg-white rounded-lg border border-dashed border-gray-300">
              <Bell size={48} className="mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500">활성화된 알람이 없습니다.</p>
            </div>
          )}
        </div>
      )}

      {/* Alarm History */}
      {activeTab === "history" && (
        <div>
          {/* Filter */}
          <div className="flex items-center gap-4 mb-4">
            <div className="flex items-center gap-2">
              <Filter size={16} className="text-gray-500" />
              <select
                value={selectedSeverity}
                onChange={(e) => setSelectedSeverity(e.target.value)}
                className="px-3 py-1.5 border rounded-md text-sm"
              >
                <option value="">전체 심각도</option>
                {Object.entries(SEVERITY_CONFIG).map(([value, config]) => (
                  <option key={value} value={value}>
                    {config.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {isHistoryError && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 mb-4">
              알람 이력을 불러오는 중 오류가 발생했습니다.
            </div>
          )}
          {historyLoading ? (
            <div className="text-center py-8 text-gray-500">로딩 중...</div>
          ) : alarmHistory && alarmHistory.length > 0 ? (
            <div className="card overflow-hidden">
              <table className="table">
                <thead>
                  <tr>
                    <th>심각도</th>
                    <th>설비</th>
                    <th>알람 코드</th>
                    <th>메시지</th>
                    <th>발생 시간</th>
                    <th>해제 시간</th>
                    <th>처리자</th>
                  </tr>
                </thead>
                <tbody>
                  {alarmHistory.map((alarm) => {
                    const config = getSeverityConfig(alarm.definition?.severity || "INFO");
                    return (
                      <tr key={alarm.id}>
                        <td>
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${config.bgColor} ${config.color}`}>
                            {config.label}
                          </span>
                        </td>
                        <td className="font-medium">{getEquipmentName(alarm.equipment_id)}</td>
                        <td>
                          <code className="px-1.5 py-0.5 bg-gray-100 rounded text-xs font-mono">
                            {alarm.definition?.code || "-"}
                          </code>
                        </td>
                        <td className="text-sm text-gray-600 max-w-xs truncate">
                          {alarm.message}
                        </td>
                        <td className="text-sm text-gray-500">
                          {new Date(alarm.occurred_at).toLocaleString()}
                        </td>
                        <td className="text-sm text-gray-500">
                          {alarm.resolved_at ? new Date(alarm.resolved_at).toLocaleString() : "-"}
                        </td>
                        <td className="text-sm text-gray-500">
                          {alarm.resolved_by || "-"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-12 bg-white rounded-lg border border-dashed border-gray-300">
              <p className="text-gray-500">알람 이력이 없습니다.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function AlarmsPage() {
  return (
    <ErrorBoundary>
      <AlarmsPageContent />
    </ErrorBoundary>
  );
}
