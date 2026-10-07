"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { analyticsService } from "@/services/analytics";
import { LotTrace, AnalyticsFilters } from "@/types";
import { POLLING } from "@/config/constants";
import {
  Search,
  Eye,
  X, 
  ChevronLeft, 
  ChevronRight,
  Package,
  Clock,
  CheckCircle,
  AlertTriangle,
  Pause,
  Play,
  MapPin,
  Route,
  Activity
} from "lucide-react";

const statusColors: Record<string, string> = {
  IN_PROGRESS: "bg-primary-100 text-primary-800",
  RUNNING: "bg-primary-100 text-primary-800",
  COMPLETED: "bg-green-100 text-green-800",
  DONE: "bg-green-100 text-green-800",
  ON_HOLD: "bg-yellow-100 text-yellow-800",
  WAITING: "bg-gray-100 text-gray-800",
  READY: "bg-cyan-100 text-cyan-800",
  SCHEDULED: "bg-primary-100 text-primary-800",
  CANCEL: "bg-gray-100 text-gray-800",
  CANCELLED: "bg-gray-100 text-gray-800",
  ERROR: "bg-red-100 text-red-800",
  PAUSE: "bg-yellow-100 text-yellow-800",
};

const statusLabels: Record<string, string> = {
  IN_PROGRESS: "진행중",
  RUNNING: "진행중",
  COMPLETED: "완료",
  DONE: "완료",
  ON_HOLD: "대기",
  WAITING: "대기",
  READY: "준비",
  SCHEDULED: "스케줄됨",
  CANCEL: "취소",
  CANCELLED: "취소",
  ERROR: "오류",
  PAUSE: "일시정지",
};

const statusIcons: Record<string, typeof Play> = {
  IN_PROGRESS: Play,
  RUNNING: Play,
  COMPLETED: CheckCircle,
  DONE: CheckCircle,
  ON_HOLD: Pause,
  WAITING: Clock,
  READY: Activity,
  SCHEDULED: Activity,
  CANCEL: AlertTriangle,
  CANCELLED: AlertTriangle,
  ERROR: AlertTriangle,
  PAUSE: Pause,
};

const processStatusColors = {
  COMPLETED: "bg-green-100 text-green-800",
  IN_PROGRESS: "bg-primary-100 text-primary-800", 
  ERROR: "bg-red-100 text-red-800",
};

const processStatusLabels = {
  COMPLETED: "완료",
  IN_PROGRESS: "진행중",
  ERROR: "오류",
};

export default function LotTracePage() {
  const [filters, setFilters] = useState<AnalyticsFilters>({
    page: 1,
    limit: 20,
    date_from: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    date_to: new Date().toISOString().split('T')[0],
  });

  const [searchLot, setSearchLot] = useState("");
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [selectedLot, setSelectedLot] = useState<string | null>(null);

  const { data: lotsData, isLoading } = useQuery({
    queryKey: ["lot-traces", filters],
    queryFn: () => analyticsService.getLotTraces(filters),
    refetchInterval: POLLING.LOT_TRACE,
  });

  const { data: lotDetail, isLoading: lotDetailLoading } = useQuery({
    queryKey: ["lot-detail", selectedLot],
    queryFn: () => selectedLot ? analyticsService.getLotTraceByLotNo(selectedLot) : Promise.resolve(null),
    enabled: !!selectedLot,
  });

  const { data: lotHistory } = useQuery({
    queryKey: ["lot-history", selectedLot],
    queryFn: () => selectedLot ? analyticsService.getLotTraceHistory(selectedLot) : Promise.resolve(null),
    enabled: !!selectedLot && showDetailModal,
  });

  const handleSearch = () => {
    if (searchLot.trim()) {
      setSelectedLot(searchLot.trim());
      setShowDetailModal(true);
    }
  };

  const handleViewDetail = (lot: LotTrace) => {
    setSelectedLot(lot.lot_no);
    setShowDetailModal(true);
  };

  const handlePageChange = (newPage: number) => {
    setFilters({ ...filters, page: newPage });
  };

  const calculateProgress = (lot: LotTrace) => {
    if (lot.status === "COMPLETED") return 100;
    if (!lot.process_history || lot.process_history.length === 0) return 0;
    
    const completedSteps = lot.process_history.filter(step => step.status === "COMPLETED").length;
    return Math.round((completedSteps / lot.process_history.length) * 100);
  };

  const getProcessDuration = (start: string, end: string | null) => {
    if (!end) return "진행중";
    const duration = new Date(end).getTime() - new Date(start).getTime();
    if (duration <= 0) return "-";
    const hours = Math.floor(duration / (1000 * 60 * 60));
    const minutes = Math.floor((duration % (1000 * 60 * 60)) / (1000 * 60));
    return `${hours}h ${minutes}m`;
  };

  const lots = lotsData?.items || [];
  const totalItems = lotsData?.total || 0;
  const totalPages = lotsData?.pages || 1;
  const currentPage = filters.page || 1;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Lot 추적</h1>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={searchLot}
              onChange={(e) => setSearchLot(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              placeholder="Lot No 검색..."
              className="px-3 py-2 border rounded-md"
            />
            <button
              onClick={handleSearch}
              className="btn btn-primary flex items-center gap-2"
            >
              <Search size={16} />
              검색
            </button>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">기간:</label>
            <input
              type="date"
              value={filters.date_from || ""}
              onChange={(e) => setFilters({ ...filters, date_from: e.target.value, page: 1 })}
              className="px-3 py-1 border rounded text-sm"
            />
            <span className="text-gray-500">~</span>
            <input
              type="date"
              value={filters.date_to || ""}
              onChange={(e) => setFilters({ ...filters, date_to: e.target.value, page: 1 })}
              className="px-3 py-1 border rounded text-sm"
            />
          </div>
        </div>
      </div>

      {/* Lot List */}
      {isLoading ? (
        <div className="text-center py-8 text-gray-500">로딩 중...</div>
      ) : lots.length > 0 ? (
        <>
          <div className="card overflow-hidden">
            <table className="table">
              <thead>
                <tr>
                  <th>Lot No</th>
                  <th>제품명</th>
                  <th>시작시간</th>
                  <th>현재공정</th>
                  <th>현재설비</th>
                  <th>진행률</th>
                  <th>상태</th>
                  <th>액션</th>
                </tr>
              </thead>
              <tbody>
                {lots.map((lot) => {
                  const StatusIcon = statusIcons[lot.status] || Activity;
                  const progress = calculateProgress(lot);
                  
                  return (
                    <tr key={lot.lot_no}>
                      <td className="font-medium">{lot.lot_no}</td>
                      <td>
                        {lot.product ? (
                          <div>
                            <div className="font-medium">{lot.product.name}</div>
                            <div className="text-sm text-gray-500">{lot.product.code}</div>
                          </div>
                        ) : (lot as any).product_name && (lot as any).product_name !== "Unknown" ? (
                          <div>
                            <div className="font-medium">{(lot as any).product_name}</div>
                            {(lot as any).product_code && (
                              <div className="text-sm text-gray-500">{(lot as any).product_code}</div>
                            )}
                          </div>
                        ) : (
                          <span className="text-gray-400">제품 정보 없음</span>
                        )}
                      </td>
                      <td className="text-sm text-gray-500">
                        {new Date(lot.start_time).toLocaleString()}
                      </td>
                      <td>{lot.current_process || "-"}</td>
                      <td>{lot.current_equipment || "-"}</td>
                      <td>
                        <div className="flex items-center gap-2">
                          <div className="flex-1 bg-gray-200 rounded-full h-2">
                            <div 
                              className={`h-2 rounded-full ${
                                progress === 100 ? "bg-green-500" : 
                                progress > 50 ? "bg-primary-500" : "bg-yellow-500"
                              }`}
                              style={{ width: `${progress}%` }}
                            />
                          </div>
                          <span className="text-sm font-medium">{progress}%</span>
                        </div>
                      </td>
                      <td>
                        <div className="flex items-center gap-2">
                          <StatusIcon size={16} className={`${
                            lot.status === "COMPLETED" ? "text-green-600" : 
                            lot.status === "IN_PROGRESS" ? "text-primary-600" : "text-yellow-600"
                          }`} />
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[lot.status]}`}>
                            {statusLabels[lot.status]}
                          </span>
                        </div>
                      </td>
                      <td>
                        <button
                          onClick={() => handleViewDetail(lot)}
                          className="p-1 text-primary-600 hover:bg-primary-50 rounded"
                          title="상세보기"
                        >
                          <Eye size={18} />
                        </button>
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
              {Math.min((currentPage - 1) * (filters.limit || 20) + 1, totalItems)}-
              {Math.min(currentPage * (filters.limit || 20), totalItems)}건
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
          <Package className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <p className="text-gray-500 mb-4">Lot 데이터가 없습니다.</p>
          <p className="text-sm text-gray-400">검색어를 입력하거나 날짜 범위를 조정해주세요.</p>
        </div>
      )}

      {/* Detail Modal */}
      {showDetailModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="text-lg font-semibold">Lot 추적 상세 {lotDetail ? `- ${lotDetail.lot_no}` : ""}</h2>
              <button
                onClick={() => setShowDetailModal(false)}
                className="p-2 hover:bg-gray-100 rounded"
              >
                <X size={20} />
              </button>
            </div>

            {lotDetailLoading ? (
              <div className="flex items-center justify-center p-12 text-gray-500">
                <Activity className="animate-spin mr-2" size={20} />
                로딩 중...
              </div>
            ) : !lotDetail ? (
              <div className="p-12 text-center text-gray-500">Lot 정보를 찾을 수 없습니다.</div>
            ) : (

            <div className="p-6 space-y-6">
              {/* Header Info */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6 p-4 bg-gray-50 rounded-lg">
                <div>
                  <label className="text-sm text-gray-600">Lot No</label>
                  <p className="font-bold text-lg">{lotDetail.lot_no}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-600">제품명</label>
                  <p className="font-medium">{lotDetail.product?.name || "정보 없음"}</p>
                  <p className="text-sm text-gray-500">{lotDetail.product?.code}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-600">현재 상태</label>
                  <div className="flex items-center gap-2">
                    {(() => {
                      const StatusIcon = statusIcons[lotDetail.status] || Activity;
                      return <StatusIcon size={20} className={`${
                        lotDetail.status === "COMPLETED" ? "text-green-600" : 
                        lotDetail.status === "IN_PROGRESS" ? "text-primary-600" : "text-yellow-600"
                      }`} />;
                    })()}
                    <span className={`px-2 py-1 rounded-full text-sm font-medium ${statusColors[lotDetail.status]}`}>
                      {statusLabels[lotDetail.status]}
                    </span>
                  </div>
                </div>
                <div>
                  <label className="text-sm text-gray-600">진행률</label>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-gray-200 rounded-full h-3">
                      <div 
                        className={`h-3 rounded-full ${
                          calculateProgress(lotDetail) === 100 ? "bg-green-500" : 
                          calculateProgress(lotDetail) > 50 ? "bg-primary-500" : "bg-yellow-500"
                        }`}
                        style={{ width: `${calculateProgress(lotDetail)}%` }}
                      />
                    </div>
                    <span className="font-bold">{calculateProgress(lotDetail)}%</span>
                  </div>
                </div>
              </div>

              {/* Current Location */}
              {lotDetail.current_process && (
                <div className="card bg-primary-50 border-primary-200">
                  <div className="flex items-center gap-4">
                    <MapPin className="h-8 w-8 text-primary-600" />
                    <div>
                      <h3 className="font-semibold text-primary-900">현재 위치</h3>
                      <p className="text-primary-800">{lotDetail.current_process}</p>
                      <p className="text-sm text-primary-600">{lotDetail.current_equipment}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Process Flow */}
              {lotHistory?.process_flow && (
                <div>
                  <div className="flex items-center gap-2 mb-4">
                    <Route className="h-5 w-5 text-gray-400" />
                    <h3 className="text-lg font-semibold">공정 흐름</h3>
                  </div>
                  
                  <div className="space-y-4">
                    {lotHistory.process_flow.map((step, index) => (
                      <div key={index} className="flex items-start gap-4">
                        {/* Timeline */}
                        <div className="flex flex-col items-center">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                            step.status === "COMPLETED" ? "bg-green-500" :
                            step.status === "IN_PROGRESS" ? "bg-primary-500" : "bg-red-500"
                          }`}>
                            <span className="text-white text-sm font-bold">{index + 1}</span>
                          </div>
                          {index < lotHistory.process_flow.length - 1 && (
                            <div className="w-0.5 h-16 bg-gray-300 mt-2" />
                          )}
                        </div>

                        {/* Process Info */}
                        <div className="flex-1 pb-6">
                          <div className="card">
                            <div className="flex items-center justify-between mb-3">
                              <div>
                                <h4 className="font-semibold">{step.process_name}</h4>
                                <p className="text-sm text-gray-600">{step.equipment_name}</p>
                              </div>
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${processStatusColors[step.status as keyof typeof processStatusColors] || 'bg-gray-100 text-gray-800'}`}>
                                {processStatusLabels[step.status as keyof typeof processStatusLabels] || step.status}
                              </span>
                            </div>

                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                              <div>
                                <label className="text-gray-600">시작시간</label>
                                <p className="font-medium">
                                  {new Date(step.start_time).toLocaleString()}
                                </p>
                              </div>
                              <div>
                                <label className="text-gray-600">종료시간</label>
                                <p className="font-medium">
                                  {step.end_time ? new Date(step.end_time).toLocaleString() : "진행중"}
                                </p>
                              </div>
                              <div>
                                <label className="text-gray-600">소요시간</label>
                                <p className="font-medium">
                                  {getProcessDuration(step.start_time, step.end_time)}
                                </p>
                              </div>
                              <div>
                                <label className="text-gray-600">사이클타임</label>
                                <p className="font-medium">
                                  {step.parameters?.cycle_time ? `${step.parameters.cycle_time}분` : "-"}
                                </p>
                              </div>
                            </div>

                            {/* Process Parameters */}
                            {step.parameters && Object.keys(step.parameters).length > 0 && (
                              <div className="mt-3 p-3 bg-gray-50 rounded">
                                <h5 className="font-medium mb-2">공정 파라미터</h5>
                                <div className="grid grid-cols-2 gap-2 text-sm">
                                  {Object.entries(step.parameters).map(([key, value]) => (
                                    <div key={key} className="flex justify-between">
                                      <span className="text-gray-600">{key}:</span>
                                      <span className="font-medium">{String(value)}</span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {step.parameters?.remarks && (
                              <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded">
                                <p className="text-sm text-yellow-800">{step.parameters.remarks}</p>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Quality Checkpoints */}
              {lotHistory?.quality_checkpoints && lotHistory.quality_checkpoints.length > 0 && (
                <div>
                  <div className="flex items-center gap-2 mb-4">
                    <CheckCircle className="h-5 w-5 text-gray-400" />
                    <h3 className="text-lg font-semibold">품질 검사 이력</h3>
                  </div>
                  
                  <div className="space-y-4">
                    {lotHistory.quality_checkpoints.map((checkpoint, index) => (
                      <div key={index} className="card">
                        <div className="flex items-center justify-between mb-3">
                          <div>
                            <h4 className="font-semibold">{checkpoint.inspection_type}</h4>
                            <p className="text-sm text-gray-600">
                              {new Date(checkpoint.inspection_date).toLocaleString()}
                            </p>
                          </div>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            checkpoint.judgment === "OK" ? "bg-green-100 text-green-800" :
                            checkpoint.judgment === "NG" ? "bg-red-100 text-red-800" :
                            "bg-yellow-100 text-yellow-800"
                          }`}>
                            {checkpoint.judgment}
                          </span>
                        </div>

                        {checkpoint.defects && checkpoint.defects.length > 0 && (
                          <div className="overflow-x-auto">
                            <table className="table text-sm">
                              <thead>
                                <tr>
                                  <th>검사항목</th>
                                  <th>측정값</th>
                                  <th>규격</th>
                                  <th>판정</th>
                                </tr>
                              </thead>
                              <tbody>
                                {checkpoint.defects.map((defect, defectIndex) => (
                                  <tr key={defectIndex}>
                                    <td className="font-medium">{defect.item_name}</td>
                                    <td>{defect.measured_value}</td>
                                    <td>{defect.specification}</td>
                                    <td>
                                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                        defect.judgment === "OK" ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                                      }`}>
                                        {defect.judgment}
                                      </span>
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}