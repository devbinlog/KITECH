"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { qualityService } from "@/services/quality";
import { productionService } from "@/services/production";
import { NCR, QualityFilters, WorkOrder } from "@/types";
import { 
  Plus, 
  Eye, 
  Edit, 
  X, 
  ChevronLeft, 
  ChevronRight, 
  AlertTriangle,
  FileText,
  Clock,
  CheckCircle,
  User,
  Calendar
} from "lucide-react";

const defectTypeLabels = {
  DIMENSION: "치수불량",
  SURFACE: "표면불량",
  MATERIAL: "재료불량",
  PROCESS: "공정불량",
  OTHER: "기타",
};

const severityLabels = {
  CRITICAL: "심각",
  MAJOR: "주요",
  MINOR: "경미",
};

const statusLabels: Record<string, string> = {
  OPEN: "접수",
  IN_PROGRESS: "진행중",
  INVESTIGATING: "조사중",
  CORRECTIVE_ACTION: "시정조치",
  CLOSED: "완료",
  CANCELLED: "취소",
};

const defectTypeColors = {
  DIMENSION: "bg-red-100 text-red-800",
  SURFACE: "bg-orange-100 text-orange-800",
  MATERIAL: "bg-purple-100 text-purple-800",
  PROCESS: "bg-primary-100 text-primary-800",
  OTHER: "bg-gray-100 text-gray-800",
};

const severityColors = {
  CRITICAL: "bg-red-100 text-red-800",
  MAJOR: "bg-yellow-100 text-yellow-800",
  MINOR: "bg-green-100 text-green-800",
};

const statusColors: Record<string, string> = {
  OPEN: "bg-red-100 text-red-800",
  IN_PROGRESS: "bg-yellow-100 text-yellow-800",
  INVESTIGATING: "bg-yellow-100 text-yellow-800",
  CORRECTIVE_ACTION: "bg-orange-100 text-orange-800",
  CLOSED: "bg-green-100 text-green-800",
  CANCELLED: "bg-gray-100 text-gray-800",
};

export default function NCRPage() {
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [selectedNCR, setSelectedNCR] = useState<NCR | null>(null);
  
  const [filters, setFilters] = useState<QualityFilters>({
    page: 1,
    limit: 20,
    date_from: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    date_to: new Date().toISOString().split('T')[0],
  });

  const [newNCR, setNewNCR] = useState({
    ncr_no: "",
    work_order_id: undefined as number | undefined,
    inspection_result_id: undefined as number | undefined,
    defect_type: "OTHER" as "DIMENSION" | "SURFACE" | "MATERIAL" | "PROCESS" | "OTHER",
    defect_description: "",
    severity: "MINOR" as "CRITICAL" | "MAJOR" | "MINOR",
    root_cause: "",
    corrective_action: "",
    preventive_action: "",
    created_by: "",
    assigned_to: "",
  });

  const { data: ncrData, isLoading } = useQuery({
    queryKey: ["ncr", filters],
    queryFn: () => qualityService.getNCRs(filters),
  });

  const { data: orders } = useQuery({
    queryKey: ["orders-for-ncr"],
    queryFn: () => productionService.getOrders({ limit: 100, view: "all" }),
  });

  const createMutation = useMutation({
    mutationFn: qualityService.createNCR,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ncr"] });
      setShowCreateModal(false);
      resetNewNCR();
    },
    onError: (error: any) => {
      alert(`NCR 생성 실패: ${error.response?.data?.detail || error.message}`);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<NCR> }) =>
      qualityService.updateNCR(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ncr"] });
      setShowDetailModal(false);
      setSelectedNCR(null);
    },
    onError: (error: any) => {
      alert(`NCR 수정 실패: ${error.response?.data?.detail || error.message}`);
    },
  });

  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      qualityService.updateNCRStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ncr"] });
      queryClient.invalidateQueries({ queryKey: ["quality-dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["inspection-results"] });
    },
    onError: (error: any) => {
      alert(`상태 변경 실패: ${error.response?.data?.detail || error.message}`);
    },
  });

  const resetNewNCR = () => {
    setNewNCR({
      ncr_no: "",
      work_order_id: undefined,
      inspection_result_id: undefined,
      defect_type: "OTHER",
      defect_description: "",
      severity: "MINOR",
      root_cause: "",
      corrective_action: "",
      preventive_action: "",
      created_by: "",
      assigned_to: "",
    });
  };

  const generateNCRNo = () => {
    const now = new Date();
    const year = now.getFullYear();
    const month = (now.getMonth() + 1).toString().padStart(2, '0');
    const day = now.getDate().toString().padStart(2, '0');
    const random = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
    return `NCR-${year}${month}${day}-${random}`;
  };

  const handleStatusChange = (ncr: NCR, newStatus: string) => {
    if (confirm(`NCR ${ncr.ncr_no}의 상태를 ${statusLabels[newStatus as keyof typeof statusLabels]}(으)로 변경하시겠습니까?`)) {
      statusMutation.mutate({ id: ncr.id, status: newStatus });
    }
  };

  const handleViewDetail = (ncr: NCR) => {
    setSelectedNCR(ncr);
    setShowDetailModal(true);
  };

  const handlePageChange = (newPage: number) => {
    setFilters({ ...filters, page: newPage });
  };

  const renderStatusActions = (ncr: NCR) => {
    const actions = [];
    
    switch (ncr.status) {
      case "OPEN":
        actions.push(
          <button
            key="investigate"
            onClick={() => handleStatusChange(ncr, "INVESTIGATING")}
            className="px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded hover:bg-yellow-200"
          >
            조사시작
          </button>
        );
        actions.push(
          <button
            key="cancel"
            onClick={() => handleStatusChange(ncr, "CANCELLED")}
            className="px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded hover:bg-gray-200"
          >
            취소
          </button>
        );
        break;
      case "INVESTIGATING":
        actions.push(
          <button
            key="corrective"
            onClick={() => handleStatusChange(ncr, "CORRECTIVE_ACTION")}
            className="px-2 py-1 text-xs bg-orange-100 text-orange-800 rounded hover:bg-orange-200"
          >
            시정조치
          </button>
        );
        break;
      case "CORRECTIVE_ACTION":
        actions.push(
          <button
            key="close"
            onClick={() => handleStatusChange(ncr, "CLOSED")}
            className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded hover:bg-green-200"
          >
            완료
          </button>
        );
        break;
    }
    
    return <div className="flex gap-1">{actions}</div>;
  };

  const ncrResponse = Array.isArray(ncrData) ? { items: ncrData, total: ncrData.length, pages: 1 } : ncrData as any;
  const ncrs = ncrResponse?.items || [];
  const totalItems = ncrResponse?.total || ncrs.length;
  const totalPages = ncrResponse?.pages || 1;
  const currentPage = filters.page || 1;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">부적합 관리 (NCR)</h1>
        <button
          onClick={() => {
            setNewNCR({ ...newNCR, ncr_no: generateNCRNo() });
            setShowCreateModal(true);
          }}
          className="btn btn-primary flex items-center gap-2"
        >
          <Plus size={16} />
          NCR 생성
        </button>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">상태:</label>
            <select
              value={filters.status || ""}
              onChange={(e) => setFilters({ ...filters, status: e.target.value || undefined, page: 1 })}
              className="px-3 py-1 border rounded text-sm"
            >
              <option value="">전체</option>
              <option value="OPEN">접수</option>
              <option value="INVESTIGATING">조사중</option>
              <option value="CORRECTIVE_ACTION">시정조치</option>
              <option value="CLOSED">완료</option>
              <option value="CANCELLED">취소</option>
            </select>
          </div>
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

      {/* NCR Table */}
      {isLoading ? (
        <div className="text-center py-8 text-gray-500">로딩 중...</div>
      ) : ncrs.length > 0 ? (
        <>
          <div className="card overflow-hidden">
            <table className="table">
              <thead>
                <tr>
                  <th>NCR No</th>
                  <th>불량유형</th>
                  <th>심각도</th>
                  <th>불량내용</th>
                  <th>상태</th>
                  <th>생성자</th>
                  <th>담당자</th>
                  <th>생성일</th>
                  <th>액션</th>
                </tr>
              </thead>
              <tbody>
                {ncrs.map((ncr: any) => (
                  <tr key={ncr.id}>
                    <td className="font-medium">{ncr.ncr_no}</td>
                    <td>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${defectTypeColors[ncr.defect_type as keyof typeof defectTypeColors]}`}>
                        {defectTypeLabels[ncr.defect_type as keyof typeof defectTypeLabels]}
                      </span>
                    </td>
                    <td>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${severityColors[ncr.severity as keyof typeof severityColors]}`}>
                        {severityLabels[ncr.severity as keyof typeof severityLabels]}
                      </span>
                    </td>
                    <td className="max-w-xs truncate" title={ncr.defect_description}>
                      {ncr.defect_description}
                    </td>
                    <td>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[ncr.status as keyof typeof statusColors] || 'bg-gray-100 text-gray-800'}`}>
                        {statusLabels[ncr.status as keyof typeof statusLabels] || ncr.status}
                      </span>
                    </td>
                    <td>{ncr.created_by}</td>
                    <td>{ncr.assigned_to || "-"}</td>
                    <td className="text-sm text-gray-500">
                      {new Date(ncr.created_at).toLocaleDateString()}
                    </td>
                    <td>
                      <div className="flex gap-1">
                        <button
                          onClick={() => handleViewDetail(ncr)}
                          className="p-1 text-primary-600 hover:bg-primary-50 rounded"
                          title="상세보기"
                        >
                          <Eye size={18} />
                        </button>
                        {renderStatusActions(ncr)}
                      </div>
                    </td>
                  </tr>
                ))}
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
          <FileText className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <p className="text-gray-500 mb-4">부적합 사항이 없습니다.</p>
          <button 
            onClick={() => {
              setNewNCR({ ...newNCR, ncr_no: generateNCRNo() });
              setShowCreateModal(true);
            }} 
            className="btn btn-primary"
          >
            NCR 생성
          </button>
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="text-lg font-semibold">NCR 생성</h2>
              <button
                onClick={() => { resetNewNCR(); setShowCreateModal(false); }}
                className="p-2 hover:bg-gray-100 rounded"
              >
                <X size={20} />
              </button>
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                createMutation.mutate(newNCR);
              }}
              className="p-6 space-y-6"
            >
              {/* Basic Info */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    NCR No *
                  </label>
                  <input
                    type="text"
                    value={newNCR.ncr_no}
                    onChange={(e) => setNewNCR({ ...newNCR, ncr_no: e.target.value })}
                    className="w-full px-3 py-2 border rounded-md bg-gray-50"
                    readOnly
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    작업지시 선택
                  </label>
                  <select
                    value={newNCR.work_order_id || ""}
                    onChange={(e) => setNewNCR({ ...newNCR, work_order_id: e.target.value ? parseInt(e.target.value) : undefined })}
                    className="w-full px-3 py-2 border rounded-md"
                  >
                    <option value="">선택 안함</option>
                    {orders?.items.map((order) => (
                      <option key={order.id} value={order.id}>
                        {order.lot_no} - {order.product?.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    불량유형 *
                  </label>
                  <select
                    value={newNCR.defect_type}
                    onChange={(e) => setNewNCR({ ...newNCR, defect_type: e.target.value as any })}
                    className="w-full px-3 py-2 border rounded-md"
                    required
                  >
                    <option value="DIMENSION">치수불량</option>
                    <option value="SURFACE">표면불량</option>
                    <option value="MATERIAL">재료불량</option>
                    <option value="PROCESS">공정불량</option>
                    <option value="OTHER">기타</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    심각도 *
                  </label>
                  <select
                    value={newNCR.severity}
                    onChange={(e) => setNewNCR({ ...newNCR, severity: e.target.value as any })}
                    className="w-full px-3 py-2 border rounded-md"
                    required
                  >
                    <option value="MINOR">경미</option>
                    <option value="MAJOR">주요</option>
                    <option value="CRITICAL">심각</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    생성자 *
                  </label>
                  <input
                    type="text"
                    value={newNCR.created_by}
                    onChange={(e) => setNewNCR({ ...newNCR, created_by: e.target.value })}
                    className="w-full px-3 py-2 border rounded-md"
                    placeholder="생성자 이름"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    담당자 지정
                  </label>
                  <input
                    type="text"
                    value={newNCR.assigned_to}
                    onChange={(e) => setNewNCR({ ...newNCR, assigned_to: e.target.value })}
                    className="w-full px-3 py-2 border rounded-md"
                    placeholder="담당자 이름"
                  />
                </div>
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  불량 내용 *
                </label>
                <textarea
                  value={newNCR.defect_description}
                  onChange={(e) => setNewNCR({ ...newNCR, defect_description: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md"
                  rows={4}
                  placeholder="불량 상황에 대한 상세 설명을 입력하세요..."
                  required
                />
              </div>

              {/* Root Cause */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  근본 원인
                </label>
                <textarea
                  value={newNCR.root_cause}
                  onChange={(e) => setNewNCR({ ...newNCR, root_cause: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md"
                  rows={3}
                  placeholder="불량의 근본 원인 분석..."
                />
              </div>

              {/* Actions */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    시정조치
                  </label>
                  <textarea
                    value={newNCR.corrective_action}
                    onChange={(e) => setNewNCR({ ...newNCR, corrective_action: e.target.value })}
                    className="w-full px-3 py-2 border rounded-md"
                    rows={3}
                    placeholder="즉시 시정조치 내용..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    예방조치
                  </label>
                  <textarea
                    value={newNCR.preventive_action}
                    onChange={(e) => setNewNCR({ ...newNCR, preventive_action: e.target.value })}
                    className="w-full px-3 py-2 border rounded-md"
                    rows={3}
                    placeholder="재발 방지를 위한 예방조치..."
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-4 border-t">
                <button
                  type="button"
                  onClick={() => { resetNewNCR(); setShowCreateModal(false); }}
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

      {/* Detail Modal */}
      {showDetailModal && selectedNCR && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="text-lg font-semibold">NCR 상세 - {selectedNCR.ncr_no}</h2>
              <button
                onClick={() => { setSelectedNCR(null); setShowDetailModal(false); }}
                className="p-2 hover:bg-gray-100 rounded"
              >
                <X size={20} />
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Header Info */}
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-4">
                  <AlertTriangle className="h-8 w-8 text-red-600" />
                  <div>
                    <h3 className="text-lg font-semibold">{selectedNCR.ncr_no}</h3>
                    <p className="text-sm text-gray-600">
                      {defectTypeLabels[selectedNCR.defect_type]} · {severityLabels[selectedNCR.severity || "MINOR"]}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${statusColors[selectedNCR.status]}`}>
                    {statusLabels[selectedNCR.status]}
                  </span>
                  <p className="text-sm text-gray-500 mt-1">
                    생성일: {new Date(selectedNCR.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>

              {/* Basic Info */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-semibold mb-3 flex items-center gap-2">
                    <User className="h-4 w-4" />
                    담당자 정보
                  </h4>
                  <div className="space-y-2">
                    <div>
                      <label className="text-sm text-gray-600">생성자</label>
                      <p className="font-medium">{selectedNCR.created_by}</p>
                    </div>
                    <div>
                      <label className="text-sm text-gray-600">담당자</label>
                      <p className="font-medium">{selectedNCR.assigned_to || "미지정"}</p>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold mb-3 flex items-center gap-2">
                    <Calendar className="h-4 w-4" />
                    일정 정보
                  </h4>
                  <div className="space-y-2">
                    <div>
                      <label className="text-sm text-gray-600">생성일</label>
                      <p className="font-medium">{new Date(selectedNCR.created_at).toLocaleString()}</p>
                    </div>
                    {selectedNCR.closed_at && (
                      <div>
                        <label className="text-sm text-gray-600">완료일</label>
                        <p className="font-medium">{new Date(selectedNCR.closed_at).toLocaleString()}</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Related Info */}
              {(selectedNCR.work_order || selectedNCR.inspection_result) && (
                <div>
                  <h4 className="font-semibold mb-3">연관 정보</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {selectedNCR.work_order && (
                      <div className="p-3 bg-primary-50 rounded-lg">
                        <label className="text-sm text-primary-600">작업지시</label>
                        <p className="font-medium">{selectedNCR.work_order.lot_no}</p>
                        <p className="text-sm text-gray-600">{selectedNCR.work_order.product?.name}</p>
                      </div>
                    )}
                    {selectedNCR.inspection_result && (
                      <div className="p-3 bg-green-50 rounded-lg">
                        <label className="text-sm text-green-600">검사결과</label>
                        <p className="font-medium">{selectedNCR.inspection_result.lot_no}</p>
                        <p className="text-sm text-gray-600">
                          {selectedNCR.inspection_result.inspection_date ? 
                            new Date(selectedNCR.inspection_result.inspection_date).toLocaleString() : 
                            "날짜 정보 없음"
                          }
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Description */}
              <div>
                <h4 className="font-semibold mb-3">불량 내용</h4>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="whitespace-pre-wrap">{selectedNCR.defect_description}</p>
                </div>
              </div>

              {/* Analysis & Actions */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <h4 className="font-semibold mb-3">근본 원인</h4>
                  <div className="p-4 bg-yellow-50 rounded-lg min-h-24">
                    <p className="whitespace-pre-wrap text-sm">
                      {selectedNCR.root_cause || "분석 중..."}
                    </p>
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold mb-3">시정조치</h4>
                  <div className="p-4 bg-primary-50 rounded-lg min-h-24">
                    <p className="whitespace-pre-wrap text-sm">
                      {selectedNCR.corrective_action || "계획 중..."}
                    </p>
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold mb-3">예방조치</h4>
                  <div className="p-4 bg-green-50 rounded-lg min-h-24">
                    <p className="whitespace-pre-wrap text-sm">
                      {selectedNCR.preventive_action || "검토 중..."}
                    </p>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex justify-between pt-4 border-t">
                <div className="flex gap-2">
                  {renderStatusActions(selectedNCR)}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setShowDetailModal(false)}
                    className="btn btn-secondary"
                  >
                    닫기
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
