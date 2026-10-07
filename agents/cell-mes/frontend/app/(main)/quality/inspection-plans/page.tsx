"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { qualityService } from "@/services/quality";
import { productService } from "@/services/master";
import { InspectionPlan, QualityFilters } from "@/types";
import {
  Plus,
  Trash2,
  Eye,
  X,
  ChevronLeft,
  ChevronRight,
  FileText,
} from "lucide-react";

const inspectionTypeLabels = {
  INCOMING: "입고검사",
  IN_PROCESS: "공정검사",
  FINAL: "최종검사",
};

const inspectionTypeColors = {
  INCOMING: "bg-primary-100 text-primary-800",
  IN_PROCESS: "bg-yellow-100 text-yellow-800",
  FINAL: "bg-green-100 text-green-800",
};

export default function InspectionPlansPage() {
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<InspectionPlan | null>(null);
  
  const [filters, setFilters] = useState<QualityFilters>({
    page: 1,
    limit: 20,
  });

  const [newPlan, setNewPlan] = useState({
    product_id: 0,
    inspection_type: "IN_PROCESS" as "INCOMING" | "IN_PROCESS" | "FINAL",
    characteristic: "",
    nominal: undefined as number | undefined,
    usl: undefined as number | undefined,
    lsl: undefined as number | undefined,
    unit: "mm",
  });

  const { data: plansData, isLoading } = useQuery({
    queryKey: ["inspection-plans", filters],
    queryFn: () => qualityService.getInspectionPlans(filters),
  });

  const { data: products } = useQuery({
    queryKey: ["products-for-inspection"],
    queryFn: () => productService.getAll(),
  });

  const createMutation = useMutation({
    mutationFn: qualityService.createInspectionPlan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inspection-plans"] });
      setShowCreateModal(false);
      resetNewPlan();
    },
    onError: (error: any) => {
      alert(`검사계획 생성 실패: ${error.response?.data?.detail || error.message}`);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: qualityService.deleteInspectionPlan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inspection-plans"] });
    },
    onError: (error: any) => {
      alert(`삭제 실패: ${error.response?.data?.detail || error.message}`);
    },
  });

  const resetNewPlan = () => {
    setNewPlan({
      product_id: 0,
      inspection_type: "IN_PROCESS",
      characteristic: "",
      nominal: undefined,
      usl: undefined,
      lsl: undefined,
      unit: "mm",
    });
  };

  const handleDelete = (plan: InspectionPlan) => {
    if (confirm(`"${plan.product?.name}" 제품의 검사계획을 삭제하시겠습니까?`)) {
      deleteMutation.mutate(plan.id);
    }
  };

  const handleViewDetail = (plan: InspectionPlan) => {
    setSelectedPlan(plan);
    setShowDetailModal(true);
  };

  const handlePageChange = (newPage: number) => {
    setFilters({ ...filters, page: newPage });
  };

  const plans = plansData?.items || [];
  const totalItems = plansData?.total || 0;
  const totalPages = plansData?.pages || 1;
  const currentPage = filters.page || 1;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">검사계획 관리</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn btn-primary flex items-center gap-2"
        >
          <Plus size={16} />
          검사계획 생성
        </button>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">검사유형:</label>
            <select
              value={filters.inspection_type || ""}
              onChange={(e) => setFilters({ ...filters, inspection_type: e.target.value || undefined, page: 1 })}
              className="px-3 py-1 border rounded text-sm"
            >
              <option value="">전체</option>
              <option value="INCOMING">입고검사</option>
              <option value="IN_PROCESS">공정검사</option>
              <option value="FINAL">최종검사</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">제품:</label>
            <select
              value={filters.product_id || ""}
              onChange={(e) => setFilters({ ...filters, product_id: e.target.value ? parseInt(e.target.value) : undefined, page: 1 })}
              className="px-3 py-1 border rounded text-sm"
            >
              <option value="">전체</option>
              {products?.map((product) => (
                <option key={product.id} value={product.id}>
                  {product.code} - {product.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Plans Table */}
      {isLoading ? (
        <div className="text-center py-8 text-gray-500">로딩 중...</div>
      ) : plans.length > 0 ? (
        <>
          <div className="card overflow-hidden">
            <table className="table">
              <thead>
                <tr>
                  <th>제품</th>
                  <th>검사유형</th>
                  <th>검사 특성</th>
                  <th>상태</th>
                  <th>생성일</th>
                  <th>액션</th>
                </tr>
              </thead>
              <tbody>
                {plans.map((plan) => (
                  <tr key={plan.id}>
                    <td>
                      {plan.product ? (
                        <div>
                          <div className="font-medium">{plan.product.name}</div>
                          <div className="text-sm text-gray-500">{plan.product.code}</div>
                        </div>
                      ) : (
                        <span className="text-gray-400">제품 정보 없음</span>
                      )}
                    </td>
                    <td>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${inspectionTypeColors[plan.inspection_type]}`}>
                        {inspectionTypeLabels[plan.inspection_type]}
                      </span>
                    </td>
                    <td>{plan.characteristic || (plan.inspection_items?.length ? `${plan.inspection_items.length}개` : "-")}</td>
                    <td>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        plan.is_active 
                          ? "bg-green-100 text-green-800" 
                          : "bg-gray-100 text-gray-800"
                      }`}>
                        {plan.is_active ? "활성" : "비활성"}
                      </span>
                    </td>
                    <td className="text-sm text-gray-500">
                      {new Date(plan.created_at).toLocaleDateString()}
                    </td>
                    <td>
                      <div className="flex gap-1">
                        <button
                          onClick={() => handleViewDetail(plan)}
                          className="p-1 text-primary-600 hover:bg-primary-50 rounded"
                          title="상세보기"
                        >
                          <Eye size={18} />
                        </button>
                        <button
                          onClick={() => handleDelete(plan)}
                          className="p-1 text-red-600 hover:bg-red-50 rounded"
                          title="삭제"
                        >
                          <Trash2 size={18} />
                        </button>
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
          <p className="text-gray-500 mb-4">검사계획이 없습니다.</p>
          <button onClick={() => setShowCreateModal(true)} className="btn btn-primary">
            검사계획 생성
          </button>
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="text-lg font-semibold">검사계획 생성</h2>
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
                if (!newPlan.product_id || newPlan.product_id === 0) {
                  alert("제품을 선택해주세요.");
                  return;
                }
                createMutation.mutate(newPlan);
              }}
              className="p-4 space-y-6"
            >
              {/* Basic Info */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    제품 선택 *
                  </label>
                  <select
                    value={newPlan.product_id}
                    onChange={(e) => setNewPlan({ ...newPlan, product_id: parseInt(e.target.value) || 0 })}
                    className="w-full px-3 py-2 border rounded-md"
                    required
                  >
                    <option value={0}>제품을 선택하세요...</option>
                    {products?.map((product) => (
                      <option key={product.id} value={product.id}>
                        {product.code} - {product.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    검사유형 *
                  </label>
                  <select
                    value={newPlan.inspection_type}
                    onChange={(e) => setNewPlan({ ...newPlan, inspection_type: e.target.value as any })}
                    className="w-full px-3 py-2 border rounded-md"
                    required
                  >
                    <option value="INCOMING">입고검사</option>
                    <option value="IN_PROCESS">공정검사</option>
                    <option value="FINAL">최종검사</option>
                  </select>
                </div>
              </div>

              {/* Inspection Characteristic (flat fields matching backend) */}
              <div>
                <h3 className="text-lg font-semibold mb-4">검사 항목</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      검사 특성 *
                    </label>
                    <input
                      type="text"
                      value={newPlan.characteristic}
                      onChange={(e) => setNewPlan({ ...newPlan, characteristic: e.target.value })}
                      className="w-full px-3 py-2 border rounded-md"
                      placeholder="예: 외경, 깊이, 위치도"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      단위
                    </label>
                    <input
                      type="text"
                      value={newPlan.unit}
                      onChange={(e) => setNewPlan({ ...newPlan, unit: e.target.value })}
                      className="w-full px-3 py-2 border rounded-md"
                      placeholder="mm"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      기준값 (Nominal)
                    </label>
                    <input
                      type="number"
                      step="0.001"
                      value={newPlan.nominal ?? ""}
                      onChange={(e) => setNewPlan({ ...newPlan, nominal: e.target.value ? parseFloat(e.target.value) : undefined })}
                      className="w-full px-3 py-2 border rounded-md"
                      placeholder="50.0"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      상한값 (USL)
                    </label>
                    <input
                      type="number"
                      step="0.001"
                      value={newPlan.usl ?? ""}
                      onChange={(e) => setNewPlan({ ...newPlan, usl: e.target.value ? parseFloat(e.target.value) : undefined })}
                      className="w-full px-3 py-2 border rounded-md"
                      placeholder="50.1"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      하한값 (LSL)
                    </label>
                    <input
                      type="number"
                      step="0.001"
                      value={newPlan.lsl ?? ""}
                      onChange={(e) => setNewPlan({ ...newPlan, lsl: e.target.value ? parseFloat(e.target.value) : undefined })}
                      className="w-full px-3 py-2 border rounded-md"
                      placeholder="49.9"
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-4 border-t">
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

      {/* Detail Modal */}
      {showDetailModal && selectedPlan && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="text-lg font-semibold">검사계획 상세</h2>
              <button
                onClick={() => setShowDetailModal(false)}
                className="p-2 hover:bg-gray-100 rounded"
              >
                <X size={20} />
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="text-sm text-gray-600">제품</label>
                  <p className="font-medium">{selectedPlan.product?.name || "정보 없음"}</p>
                  <p className="text-sm text-gray-500">{selectedPlan.product?.code}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-600">검사유형</label>
                  <p className="font-medium">{inspectionTypeLabels[selectedPlan.inspection_type]}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-600">상태</label>
                  <p className="font-medium">{selectedPlan.is_active ? "활성" : "비활성"}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-600">생성일</label>
                  <p className="font-medium">{new Date(selectedPlan.created_at).toLocaleString()}</p>
                </div>
              </div>

              {/* Inspection Items / Characteristic */}
              <div>
                <h3 className="text-lg font-semibold mb-4">검사 항목</h3>
                {selectedPlan.characteristic ? (
                  <div className="overflow-x-auto">
                    <table className="table">
                      <thead>
                        <tr>
                          <th>검사 특성</th>
                          <th>기준값</th>
                          <th>상한값 (USL)</th>
                          <th>하한값 (LSL)</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td className="font-medium">{selectedPlan.characteristic}</td>
                          <td>{selectedPlan.nominal ?? "-"}</td>
                          <td>{selectedPlan.usl ?? "-"}</td>
                          <td>{selectedPlan.lsl ?? "-"}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                ) : selectedPlan.inspection_items?.length ? (
                  <div className="overflow-x-auto">
                    <table className="table">
                      <thead>
                        <tr>
                          <th>항목명</th>
                          <th>규격</th>
                          <th>상한값</th>
                          <th>하한값</th>
                          <th>목표값</th>
                          <th>측정방법</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedPlan.inspection_items.map((item) => (
                          <tr key={item.id}>
                            <td className="font-medium">{item.item_name}</td>
                            <td>{item.specification}</td>
                            <td>{item.usl ?? "-"}</td>
                            <td>{item.lsl ?? "-"}</td>
                            <td>{item.target ?? "-"}</td>
                            <td>{item.measurement_method}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-gray-400 text-sm">검사 항목 정보가 없습니다.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}