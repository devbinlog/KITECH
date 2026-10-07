"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import clsx from "clsx";
import { equipmentService } from "@/services/equipment";
import { EquipmentCard } from "@/components/equipment/EquipmentCard";
import { Equipment } from "@/types";
import { EquipmentSourceFilter, getEquipmentSourceLabel, isVirtualEquipment } from "@/utils/equipment";
import { RefreshCw, Plus, Trash2, X, Wifi, WifiOff, AlertCircle, MapPin, Hash, Clock, History } from "lucide-react";
import { JsonView, darkStyles } from "react-json-view-lite";
import "react-json-view-lite/dist/index.css";
import { POLLING } from "@/config/constants";

interface StatusHistory {
  id: number;
  equipment_id: number;
  status: string;
  changed_at: string;
  duration_sec: number | null;
  remarks: string | null;
}

interface VirtualCopyForm {
  count: number;
  name_prefix: string;
  machineType: string;
  setupChangeTimeMin: string;
  loadingType: string;
  amrTransportQty: string;
  exchangeTimeSec: string;
  loadUnloadTimeSec: string;
}

export default function EquipmentsPage() {
  const queryClient = useQueryClient();
  const [selectedEquipment, setSelectedEquipment] = useState<Equipment | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [activeTab, setActiveTab] = useState<"info" | "spec" | "data" | "history">("info");
  const [statusHistory, setStatusHistory] = useState<StatusHistory[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [sourceFilter, setSourceFilter] = useState<EquipmentSourceFilter>("all");
  const [showVirtualCopyModal, setShowVirtualCopyModal] = useState(false);
  const [virtualCopyForm, setVirtualCopyForm] = useState<VirtualCopyForm>({
    count: 1,
    name_prefix: "",
    machineType: "",
    setupChangeTimeMin: "",
    loadingType: "",
    amrTransportQty: "",
    exchangeTimeSec: "",
    loadUnloadTimeSec: "",
  });

  const { data: equipments, isLoading, refetch } = useQuery({
    queryKey: ["equipments"],
    queryFn: () => equipmentService.getAll(),
    refetchInterval: POLLING.FAST,
  });

  // Middleware health check
  const { data: middlewareHealth, isLoading: healthLoading } = useQuery({
    queryKey: ["middleware-health"],
    queryFn: () => equipmentService.checkMiddlewareHealth(),
    refetchInterval: POLLING.NORMAL,
    retry: false,
  });

  const syncMutation = useMutation({
    mutationFn: (deleteOrphans: boolean) => equipmentService.sync(deleteOrphans),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["equipments"] });
      let msg = `동기화 완료: ${result.synced_count}대 (신규: ${result.created.length}, 업데이트: ${result.updated.length})`;
      if (result.deleted && result.deleted.length > 0) {
        msg += `\n삭제됨: ${result.deleted.length}대 (${result.deleted.join(", ")})`;
      }
      if (result.errors && result.errors.length > 0) {
        msg += `\n오류: ${result.errors.length}건`;
      }
      alert(msg);
    },
    onError: (error: any) => {
      alert(`동기화 실패: ${error.response?.data?.detail || error.message}`);
    },
  });

  const handleSync = () => {
    const proceed = confirm("미들웨어(AAS)에서 설비 정보를 동기화합니다.\n계속하시겠습니까?");
    if (!proceed) return;
    const deleteOrphans = confirm(
      "미들웨어에 없는 기존 설비(시드 데이터 등)를 삭제하시겠습니까?\n\n[확인] 삭제\n[취소] 유지"
    );
    syncMutation.mutate(deleteOrphans);
  };

  const deleteMutation = useMutation({
    mutationFn: equipmentService.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["equipments"] });
      setShowModal(false);
      setSelectedEquipment(null);
    },
    onError: (error: any) => {
      alert(error?.response?.data?.detail || "삭제에 실패했습니다.");
    },
  });

  const virtualCopyMutation = useMutation({
    mutationFn: async () => {
      if (!selectedEquipment) throw new Error("선택된 설비가 없습니다.");
      const machineTypeParams: Record<string, any> = {};
      if (virtualCopyForm.loadingType) machineTypeParams.loadingType = virtualCopyForm.loadingType;
      if (virtualCopyForm.amrTransportQty) machineTypeParams.amrTransportQty = Number(virtualCopyForm.amrTransportQty);
      if (virtualCopyForm.exchangeTimeSec) machineTypeParams.exchangeTimeSec = Number(virtualCopyForm.exchangeTimeSec);
      if (virtualCopyForm.loadUnloadTimeSec) machineTypeParams.loadUnloadTimeSec = Number(virtualCopyForm.loadUnloadTimeSec);

      const overrides: Record<string, any> = {};
      if (virtualCopyForm.setupChangeTimeMin) {
        overrides.setupChangeTimeMin = Number(virtualCopyForm.setupChangeTimeMin);
      }
      if (Object.keys(machineTypeParams).length > 0) {
        overrides.machineTypeParams = machineTypeParams;
      }

      return equipmentService.createVirtualCopies(selectedEquipment.id, {
        count: virtualCopyForm.count,
        name_prefix: virtualCopyForm.name_prefix || undefined,
        machineType: virtualCopyForm.machineType || undefined,
        overrides,
      });
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["equipments"] });
      setSourceFilter("virtual");
      setShowVirtualCopyModal(false);
      alert(`가상장비 ${result.created_count}대가 생성되었습니다.`);
    },
    onError: (error: any) => {
      alert(`가상장비 생성 실패: ${error.response?.data?.detail || error.message}`);
    },
  });

  const handleEquipmentClick = async (equipment: Equipment) => {
    setSelectedEquipment(equipment);
    setActiveTab("info");
    setShowModal(true);
    setStatusHistory([]);
  };

  const openVirtualCopyModal = (equipment: Equipment) => {
    const spec = equipment.spec_data || {};
    const params = spec.machineTypeParams || {};
    setVirtualCopyForm({
      count: 1,
      name_prefix: `${equipment.eq_name}_MES_VIRTUAL`,
      machineType: spec.machineType || "",
      setupChangeTimeMin: spec.setupChangeTimeMin != null ? String(spec.setupChangeTimeMin) : "",
      loadingType: params.loadingType || "",
      amrTransportQty: params.amrTransportQty != null ? String(params.amrTransportQty) : "",
      exchangeTimeSec: params.exchangeTimeSec != null ? String(params.exchangeTimeSec) : "",
      loadUnloadTimeSec: params.loadUnloadTimeSec != null ? String(params.loadUnloadTimeSec) : "",
    });
    setShowVirtualCopyModal(true);
  };

  const updateVirtualCopyForm = <K extends keyof VirtualCopyForm>(
    key: K,
    value: VirtualCopyForm[K],
  ) => {
    setVirtualCopyForm((prev) => ({ ...prev, [key]: value }));
  };

  const loadStatusHistory = async (equipmentId: number) => {
    setHistoryLoading(true);
    try {
      const history = await equipmentService.getStatusHistory(equipmentId);
      setStatusHistory(history);
    } catch (error) {
      console.error("Failed to load status history:", error);
      setStatusHistory([]);
    } finally {
      setHistoryLoading(false);
    }
  };

  const handleTabChange = (tab: "info" | "spec" | "data" | "history") => {
    setActiveTab(tab);
    if (tab === "history" && selectedEquipment) {
      loadStatusHistory(selectedEquipment.id);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "RUN":
        return "bg-green-100 text-green-800";
      case "STOP":
        return "bg-gray-100 text-gray-800";
      case "ERROR":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case "RUN":
        return "가동 중";
      case "STOP":
        return "정지";
      case "ERROR":
        return "오류";
      default:
        return status;
    }
  };

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return "-";
    if (seconds < 60) return `${seconds}초`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}분`;
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    return `${hours}시간 ${mins}분`;
  };

  const filteredEquipments = (equipments || []).filter((equipment) => {
    if (sourceFilter === "all") return true;
    const isVirtual = isVirtualEquipment(equipment);
    return sourceFilter === "virtual" ? isVirtual : !isVirtual;
  });
  const physicalCount = (equipments || []).filter((equipment) => !isVirtualEquipment(equipment)).length;
  const virtualCount = (equipments || []).filter(isVirtualEquipment).length;

  const filterOptions: Array<{ value: EquipmentSourceFilter; label: string; count: number }> = [
    { value: "all", label: "전체", count: equipments?.length || 0 },
    { value: "physical", label: "실장비", count: physicalCount },
    { value: "virtual", label: "가상장비", count: virtualCount },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">설비 관리</h1>
          {/* Middleware Status */}
          <div className="flex items-center gap-2 mt-1">
            {healthLoading ? (
              <span className="text-sm text-gray-500">미들웨어 상태 확인 중...</span>
            ) : middlewareHealth?.status === "connected" ? (
              <span className="flex items-center gap-1 text-sm text-green-600">
                <Wifi size={14} />
                미들웨어 연결됨
              </span>
            ) : middlewareHealth?.status === "disconnected" ? (
              <span className="flex items-center gap-1 text-sm text-yellow-600">
                <WifiOff size={14} />
                미들웨어 연결 안됨
              </span>
            ) : (
              <span className="flex items-center gap-1 text-sm text-red-600" title={middlewareHealth?.error}>
                <AlertCircle size={14} />
                미들웨어 오류
              </span>
            )}
            {middlewareHealth?.url && (
              <span className="text-xs text-gray-400 font-mono">{middlewareHealth.url}</span>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => refetch()}
            className="btn btn-secondary flex items-center gap-2"
          >
            <RefreshCw size={16} />
            새로고침
          </button>
          <button
            onClick={handleSync}
            disabled={syncMutation.isPending || middlewareHealth?.status !== "connected"}
            className="btn btn-primary flex items-center gap-2"
            title={middlewareHealth?.status !== "connected" ? "미들웨어 연결 필요" : "AAS 서버에서 장비 정보 동기화"}
          >
            <RefreshCw size={16} className={syncMutation.isPending ? "animate-spin" : ""} />
            AAS 장비 동기화
          </button>
        </div>
      </div>

      {/* Equipment Filters */}
      {!isLoading && equipments && equipments.length > 0 && (
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="inline-flex rounded-lg border border-gray-200 bg-white p-1 shadow-sm">
            {filterOptions.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => setSourceFilter(option.value)}
                className={clsx(
                  "min-w-[88px] rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                  sourceFilter === option.value
                    ? "bg-primary-600 text-white shadow-sm"
                    : "text-gray-600 hover:bg-gray-50"
                )}
                aria-pressed={sourceFilter === option.value}
              >
                {option.label}
                <span className={clsx(
                  "ml-1 text-xs",
                  sourceFilter === option.value ? "text-white/80" : "text-gray-400"
                )}>
                  {option.count}
                </span>
              </button>
            ))}
          </div>
          <div className="text-sm text-gray-500">
            표시 {filteredEquipments.length}대
          </div>
        </div>
      )}

      {/* Equipment Grid */}
      {isLoading ? (
        <div className="text-center py-8 text-gray-500">로딩 중...</div>
      ) : equipments && equipments.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filteredEquipments.map((equipment) => (
            <EquipmentCard
              key={equipment.id}
              equipment={equipment}
              onClick={() => handleEquipmentClick(equipment)}
            />
          ))}
          {filteredEquipments.length === 0 && (
            <div className="col-span-full text-center py-12 bg-white rounded-lg border border-dashed border-gray-300 text-gray-500">
              조건에 맞는 설비가 없습니다.
            </div>
          )}
        </div>
      ) : (
        <div className="text-center py-12 bg-white rounded-lg border border-dashed border-gray-300">
          <p className="text-gray-500 mb-4">등록된 설비가 없습니다.</p>
          <button
            onClick={handleSync}
            disabled={syncMutation.isPending}
            className="btn btn-primary"
          >
            AAS 장비 동기화 실행
          </button>
        </div>
      )}

      {/* Equipment Detail Modal */}
      {showModal && selectedEquipment && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-4 border-b flex-shrink-0">
              <div>
                <h2 className="text-lg font-semibold">{selectedEquipment.eq_name}</h2>
                <div className="flex items-center gap-3 text-sm text-gray-500 mt-1">
                  {selectedEquipment.eq_code && (
                    <span className="flex items-center gap-1">
                      <Hash size={14} />
                      {selectedEquipment.eq_code}
                    </span>
                  )}
                  {selectedEquipment.aas_id && (
                    <span className="font-mono text-xs">{selectedEquipment.aas_id}</span>
                  )}
                </div>
              </div>
              <button
                onClick={() => setShowModal(false)}
                className="p-2 hover:bg-gray-100 rounded"
              >
                <X size={20} />
              </button>
            </div>

            {/* Tabs */}
            <div className="flex border-b flex-shrink-0">
              <button
                onClick={() => handleTabChange("info")}
                className={`px-4 py-2 font-medium text-sm ${activeTab === "info"
                  ? "text-primary-600 border-b-2 border-primary-600"
                  : "text-gray-500"
                  }`}
              >
                기본 정보
              </button>
              <button
                onClick={() => handleTabChange("spec")}
                className={`px-4 py-2 font-medium text-sm ${activeTab === "spec"
                  ? "text-primary-600 border-b-2 border-primary-600"
                  : "text-gray-500"
                  }`}
              >
                Spec Data
              </button>
              <button
                onClick={() => handleTabChange("data")}
                className={`px-4 py-2 font-medium text-sm ${activeTab === "data"
                  ? "text-primary-600 border-b-2 border-primary-600"
                  : "text-gray-500"
                  }`}
              >
                Last Data
              </button>
              <button
                onClick={() => handleTabChange("history")}
                className={`px-4 py-2 font-medium text-sm flex items-center gap-1 ${activeTab === "history"
                  ? "text-primary-600 border-b-2 border-primary-600"
                  : "text-gray-500"
                  }`}
              >
                <History size={14} />
                상태 이력
              </button>
            </div>

            {/* Content */}
            <div className="p-4 overflow-auto flex-1">
              {activeTab === "info" && (
                <div className="space-y-4">
                  {/* Status & Type */}
                  <div className="flex items-center gap-3">
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(selectedEquipment.current_status)}`}>
                      {getStatusLabel(selectedEquipment.current_status)}
                    </span>
                    <span className="px-2 py-1 rounded bg-gray-100 text-gray-700 text-sm">
                      {selectedEquipment.equipment_type}
                    </span>
                    <span className={clsx(
                      "px-2 py-1 rounded text-sm font-medium border",
                      isVirtualEquipment(selectedEquipment)
                        ? "bg-indigo-50 text-indigo-700 border-indigo-100"
                        : "bg-gray-50 text-gray-600 border-gray-200"
                    )}>
                      {getEquipmentSourceLabel(selectedEquipment)}
                    </span>
                  </div>

                  {/* Info Grid */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-gray-50 rounded-lg p-3">
                      <p className="text-xs text-gray-500 mb-1">설비 코드</p>
                      <p className="font-mono font-medium">{selectedEquipment.eq_code || "-"}</p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <p className="text-xs text-gray-500 mb-1">모델명</p>
                      <p className="font-medium">{selectedEquipment.model_name || "-"}</p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <p className="text-xs text-gray-500 mb-1 flex items-center gap-1">
                        <MapPin size={12} /> 위치
                      </p>
                      <p className="font-medium">{selectedEquipment.location || "-"}</p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <p className="text-xs text-gray-500 mb-1">셀 ID</p>
                      <p className="font-mono font-medium">{selectedEquipment.cell_id || "-"}</p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <p className="text-xs text-gray-500 mb-1">스케줄러 타입</p>
                      <p className="font-medium">{selectedEquipment.spec_data?.machineType || "-"}</p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <p className="text-xs text-gray-500 mb-1">장비 출처</p>
                      <p className="font-medium">{selectedEquipment.spec_data?.equipmentSource || "PHYSICAL"}</p>
                    </div>
                  </div>

                  {isVirtualEquipment(selectedEquipment) && (
                    <div className="bg-indigo-50 rounded-lg p-3 border border-indigo-100">
                      <p className="text-xs text-indigo-600 mb-1">대응 실장비</p>
                      <p className="font-mono text-sm text-indigo-900 break-all">
                        {selectedEquipment.spec_data?.physicalAssetRef || "-"}
                      </p>
                    </div>
                  )}

                  {/* Connection Info */}
                  <div className="bg-gray-50 rounded-lg p-3">
                    <p className="text-xs text-gray-500 mb-2 flex items-center gap-1">
                      <Clock size={12} /> 마지막 연결
                    </p>
                    <p className="text-sm">
                      {selectedEquipment.last_connected_at
                        ? new Date(selectedEquipment.last_connected_at).toLocaleString()
                        : "연결 기록 없음"}
                    </p>
                  </div>
                </div>
              )}

              {activeTab === "spec" && (
                selectedEquipment.spec_data && Object.keys(selectedEquipment.spec_data).length > 0 ? (
                  <JsonView
                    data={selectedEquipment.spec_data}
                    style={darkStyles}
                  />
                ) : (
                  <div className="text-center py-8 text-gray-500">Spec 데이터가 없습니다.</div>
                )
              )}

              {activeTab === "data" && (
                selectedEquipment.last_data && Object.keys(selectedEquipment.last_data).length > 0 ? (
                  <JsonView
                    data={selectedEquipment.last_data}
                    style={darkStyles}
                  />
                ) : (
                  <div className="text-center py-8 text-gray-500">Last 데이터가 없습니다.</div>
                )
              )}

              {activeTab === "history" && (
                <div>
                  {historyLoading ? (
                    <div className="text-center py-8 text-gray-500">로딩 중...</div>
                  ) : statusHistory.length > 0 ? (
                    <div className="space-y-2">
                      {statusHistory.map((record) => (
                        <div
                          key={record.id}
                          className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                        >
                          <div className="flex items-center gap-3">
                            <span className={`px-2 py-0.5 rounded text-xs font-medium ${getStatusColor(record.status)}`}>
                              {getStatusLabel(record.status)}
                            </span>
                            <span className="text-sm text-gray-600">
                              {new Date(record.changed_at).toLocaleString()}
                            </span>
                          </div>
                          <div className="text-right">
                            <span className="text-sm font-mono text-gray-500">
                              {formatDuration(record.duration_sec)}
                            </span>
                            {record.remarks && (
                              <p className="text-xs text-gray-400 mt-0.5">{record.remarks}</p>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-gray-500">
                      상태 이력이 없습니다.
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="flex justify-between p-4 border-t bg-gray-50 flex-shrink-0">
              <button
                onClick={() => {
                  if (confirm("정말 삭제하시겠습니까?")) {
                    deleteMutation.mutate(selectedEquipment.id);
                  }
                }}
                className="btn btn-danger flex items-center gap-2"
              >
                <Trash2 size={16} />
                삭제
              </button>
              <div className="flex gap-2">
                {!isVirtualEquipment(selectedEquipment) && (
                  <button
                    onClick={() => openVirtualCopyModal(selectedEquipment)}
                    className="btn btn-primary flex items-center gap-2"
                  >
                    <Plus size={16} />
                    가상장비 복사
                  </button>
                )}
                <button onClick={() => setShowModal(false)} className="btn btn-secondary">
                  닫기
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Virtual Copy Modal */}
      {showVirtualCopyModal && selectedEquipment && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60]">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg max-h-[85vh] overflow-hidden flex flex-col">
            <div className="flex items-center justify-between p-4 border-b">
              <div>
                <h2 className="text-lg font-semibold">가상장비 복사</h2>
                <p className="text-sm text-gray-500 mt-1">{selectedEquipment.eq_name}</p>
              </div>
              <button
                onClick={() => setShowVirtualCopyModal(false)}
                className="p-2 hover:bg-gray-100 rounded"
                aria-label="가상장비 복사 닫기"
              >
                <X size={20} />
              </button>
            </div>

            <div className="p-4 overflow-auto space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <label className="block">
                  <span className="text-xs text-gray-500">생성 수량</span>
                  <input
                    type="number"
                    min={1}
                    max={20}
                    value={virtualCopyForm.count}
                    onChange={(event) => updateVirtualCopyForm("count", Number(event.target.value))}
                    className="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-sm"
                  />
                </label>
                <label className="block">
                  <span className="text-xs text-gray-500">Scheduler Machine Type</span>
                  <input
                    value={virtualCopyForm.machineType}
                    onChange={(event) => updateVirtualCopyForm("machineType", event.target.value)}
                    className="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-sm"
                  />
                </label>
              </div>

              <label className="block">
                <span className="text-xs text-gray-500">이름 Prefix</span>
                <input
                  value={virtualCopyForm.name_prefix}
                  onChange={(event) => updateVirtualCopyForm("name_prefix", event.target.value)}
                  className="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-sm"
                />
              </label>

              <div className="grid grid-cols-2 gap-4">
                <label className="block">
                  <span className="text-xs text-gray-500">setupChangeTimeMin</span>
                  <input
                    type="number"
                    value={virtualCopyForm.setupChangeTimeMin}
                    onChange={(event) => updateVirtualCopyForm("setupChangeTimeMin", event.target.value)}
                    className="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-sm"
                  />
                </label>
                <label className="block">
                  <span className="text-xs text-gray-500">loadingType</span>
                  <input
                    value={virtualCopyForm.loadingType}
                    onChange={(event) => updateVirtualCopyForm("loadingType", event.target.value)}
                    className="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-sm"
                  />
                </label>
                <label className="block">
                  <span className="text-xs text-gray-500">amrTransportQty</span>
                  <input
                    type="number"
                    value={virtualCopyForm.amrTransportQty}
                    onChange={(event) => updateVirtualCopyForm("amrTransportQty", event.target.value)}
                    className="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-sm"
                  />
                </label>
                <label className="block">
                  <span className="text-xs text-gray-500">exchangeTimeSec</span>
                  <input
                    type="number"
                    value={virtualCopyForm.exchangeTimeSec}
                    onChange={(event) => updateVirtualCopyForm("exchangeTimeSec", event.target.value)}
                    className="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-sm"
                  />
                </label>
                <label className="block col-span-2">
                  <span className="text-xs text-gray-500">loadUnloadTimeSec</span>
                  <input
                    type="number"
                    value={virtualCopyForm.loadUnloadTimeSec}
                    onChange={(event) => updateVirtualCopyForm("loadUnloadTimeSec", event.target.value)}
                    className="mt-1 w-full rounded border border-gray-300 px-3 py-2 text-sm"
                  />
                </label>
              </div>
            </div>

            <div className="flex justify-end gap-2 p-4 border-t bg-gray-50">
              <button
                onClick={() => setShowVirtualCopyModal(false)}
                className="btn btn-secondary"
              >
                취소
              </button>
              <button
                onClick={() => virtualCopyMutation.mutate()}
                disabled={virtualCopyMutation.isPending || virtualCopyForm.count < 1 || virtualCopyForm.count > 20}
                className="btn btn-primary flex items-center gap-2"
              >
                <Plus size={16} />
                {virtualCopyMutation.isPending ? "생성 중..." : "생성"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
