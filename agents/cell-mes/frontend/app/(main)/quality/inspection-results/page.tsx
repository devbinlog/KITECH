"use client";

import { useState, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { qualityService } from "@/services/quality";
import { productService } from "@/services/master";
import { productionService } from "@/services/production";
import { InspectionResult, Product, WorkOrder, QualityFilters, InspectionPlan } from "@/types";
import {
  Plus,
  Eye,
  X,
  ChevronLeft,
  ChevronRight,
  CircleCheck,
  CircleX,
  TriangleAlert,
  FileText,
} from "lucide-react";

const judgmentLabels = {
  OK: "합격",
  NG: "불합격",
  REWORK: "재작업",
};

const judgmentColors = {
  OK: "bg-green-100 text-green-800",
  NG: "bg-red-100 text-red-800",
  REWORK: "bg-yellow-100 text-yellow-800",
};

const judgmentIcons = {
  OK: CircleCheck,
  NG: CircleX,
  REWORK: TriangleAlert,
};

export default function InspectionResultsPage() {
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [selectedResult, setSelectedResult] = useState<InspectionResult | null>(null);
  
  const [filters, setFilters] = useState<QualityFilters>({
    page: 1,
    limit: 20,
    date_from: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    date_to: new Date().toISOString().split('T')[0],
  });

  const [newResult, setNewResult] = useState({
    inspection_plan_id: 0,
    work_order_id: undefined as number | undefined,
    lot_no: "",
    measured_values: [] as Array<{
      inspection_item_id: number;
      measured_value: number;
      judgment: "OK" | "NG";
    }>,
    inspector: "",
    inspection_date: new Date().toISOString().slice(0, 16),
    judgment: "OK" as "OK" | "NG" | "REWORK",
    remarks: "",
  });

  const [selectedPlan, setSelectedPlan] = useState<InspectionPlan | null>(null);

  const { data: resultsData, isLoading } = useQuery({
    queryKey: ["inspection-results", filters],
    queryFn: () => qualityService.getInspectionResults({
      ...filters,
      offset: ((filters.page || 1) - 1) * (filters.limit || 20),
    }),
  });

  const { data: products } = useQuery({
    queryKey: ["products-for-results"],
    queryFn: () => productService.getAll(),
  });

  const { data: orders } = useQuery({
    queryKey: ["orders-for-inspection"],
    queryFn: () => productionService.getOrders({ limit: 100, view: "all" }),
  });

  const { data: plans } = useQuery({
    queryKey: ["inspection-plans-for-results"],
    queryFn: () => qualityService.getInspectionPlans({ limit: 100 }),
  });

  const createMutation = useMutation({
    mutationFn: qualityService.createInspectionResult,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inspection-results"] });
      setShowCreateModal(false);
      resetNewResult();
    },
    onError: (error: any) => {
      alert(`측정결과 등록 실패: ${error.response?.data?.detail || error.message}`);
    },
  });

  const resetNewResult = () => {
    setNewResult({
      inspection_plan_id: 0,
      work_order_id: undefined,
      lot_no: "",
      measured_values: [],
      inspector: "",
      inspection_date: new Date().toISOString().slice(0, 16),
      judgment: "OK",
      remarks: "",
    });
    setSelectedPlan(null);
  };

  const handlePlanSelection = useCallback((planId: number) => {
    const plan = plans?.items.find(p => p.id === planId);
    if (plan) {
      setSelectedPlan(plan);
      const measuredValues = plan.inspection_items?.map(item => ({
        inspection_item_id: item.id,
        measured_value: 0,
        judgment: "OK" as "OK" | "NG",
      })) || [];

      setNewResult(prev => ({
        ...prev,
        inspection_plan_id: planId,
        measured_values: measuredValues,
      }));
    }
  }, [plans]);

  const updateMeasuredValue = (index: number, field: string, value: any) => {
    const values = newResult.measured_values.map((item, i) =>
      i === index ? { ...item, [field]: value } : item
    );
    setNewResult({ ...newResult, measured_values: values });
  };

  const calculateOverallJudgment = () => {
    if (newResult.measured_values.some(v => v.judgment === "NG")) {
      return "NG";
    }
    return "OK";
  };

  const handleViewDetail = (result: InspectionResult) => {
    setSelectedResult(result);
    setShowDetailModal(true);
  };

  const handlePageChange = (newPage: number) => {
    setFilters({ ...filters, page: newPage });
  };

  const resultsResponse = Array.isArray(resultsData) ? { items: resultsData, total: resultsData.length, pages: 1 } : resultsData as any;
  const results = resultsResponse?.items || [];
  const totalItems = resultsResponse?.total || results.length;
  const totalPages = resultsResponse?.pages || 1;
  const currentPage = filters.page || 1;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">측정결과 관리</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn btn-primary flex items-center gap-2"
        >
          <Plus size={16} />
          측정결과 등록
        </button>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex items-center gap-4 flex-wrap">
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

      {/* Results Table */}
      {isLoading ? (
        <div className="text-center py-8 text-gray-500">로딩 중...</div>
      ) : results.length > 0 ? (
        <>
          <div className="card overflow-hidden">
            <table className="table">
              <thead>
                <tr>
                  <th>Lot No</th>
                  <th>제품명</th>
                  <th>검사계획</th>
                  <th>검사일시</th>
                  <th>검사자</th>
                  <th>판정</th>
                  <th>액션</th>
                </tr>
              </thead>
              <tbody>
                {results.map((result: any) => {
                  const judgment = result.judgment as keyof typeof judgmentIcons | null;
                  const JudgmentIcon = (judgment && judgmentIcons[judgment]) || FileText;
                  const judgmentColor = (judgment && judgmentColors[judgment]) || "bg-gray-100 text-gray-800";
                  const judgmentLabel = (judgment && judgmentLabels[judgment]) || "미판정";
                  const judgmentIconColor = judgment === "OK" ? "text-green-600" :
                    judgment === "NG" ? "text-red-600" :
                    judgment === "REWORK" ? "text-yellow-600" : "text-gray-400";
                  return (
                    <tr key={result.id}>
                      <td className="font-medium">{result.lot_no}</td>
                      <td>
                        {result.work_order?.product ? (
                          <div>
                            <div className="font-medium">{result.work_order.product.name}</div>
                            <div className="text-sm text-gray-500">{result.work_order.product.code}</div>
                          </div>
                        ) : (
                          <span className="text-gray-400">정보 없음</span>
                        )}
                      </td>
                      <td>
                        {result.inspection_plan ? (
                          <div>
                            <div className="text-sm">{result.inspection_plan.product?.name}</div>
                            <div className="text-xs text-gray-500">
                              {result.inspection_plan.inspection_items?.length}개 항목
                            </div>
                          </div>
                        ) : (
                          <span className="text-gray-400">계획 없음</span>
                        )}
                      </td>
                      <td className="text-sm text-gray-500">
                        {result.inspection_date ? new Date(result.inspection_date).toLocaleString() : result.measured_at ? new Date(result.measured_at).toLocaleString() : "-"}
                      </td>
                      <td>{result.inspector || "-"}</td>
                      <td>
                        <div className="flex items-center gap-2">
                          <JudgmentIcon size={16} className={judgmentIconColor} />
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${judgmentColor}`}>
                            {judgmentLabel}
                          </span>
                        </div>
                      </td>
                      <td>
                        <div className="flex gap-1">
                          <button
                            onClick={() => handleViewDetail(result)}
                            className="p-1 text-primary-600 hover:bg-primary-50 rounded"
                            title="상세보기"
                          >
                            <Eye size={18} />
                          </button>
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
          <p className="text-gray-500 mb-4">측정결과가 없습니다.</p>
          <button onClick={() => setShowCreateModal(true)} className="btn btn-primary">
            측정결과 등록
          </button>
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="text-lg font-semibold">측정결과 등록</h2>
              <button
                onClick={() => { resetNewResult(); setShowCreateModal(false); }}
                className="p-2 hover:bg-gray-100 rounded"
              >
                <X size={20} />
              </button>
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (!newResult.work_order_id) {
                  alert("작업지시를 선택해주세요.");
                  return;
                }
                const finalJudgment = newResult.measured_values.length > 0
                  ? calculateOverallJudgment()
                  : newResult.judgment;
                createMutation.mutate({
                  ...newResult,
                  work_order_id: newResult.work_order_id,
                  judgment: finalJudgment,
                });
              }}
              className="p-6 space-y-6"
            >
              {/* Basic Info */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    검사계획 선택 *
                  </label>
                  <select
                    value={newResult.inspection_plan_id}
                    onChange={(e) => handlePlanSelection(parseInt(e.target.value) || 0)}
                    className="w-full px-3 py-2 border rounded-md"
                    required
                  >
                    <option value={0}>검사계획을 선택하세요...</option>
                    {plans?.items.map((plan) => (
                      <option key={plan.id} value={plan.id}>
                        {plan.product?.name} - {plan.inspection_type}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    작업지시 선택 *
                  </label>
                  <select
                    value={newResult.work_order_id ?? ""}
                    onChange={(e) => {
                      const orderId = e.target.value ? parseInt(e.target.value) : undefined;
                      const order = orderId ? orders?.items.find(o => o.id === orderId) : undefined;
                      setNewResult(prev => ({
                        ...prev,
                        work_order_id: orderId,
                        lot_no: order?.lot_no || ""
                      }));
                    }}
                    className="w-full px-3 py-2 border rounded-md"
                    required
                  >
                    <option value="">작업지시를 선택하세요...</option>
                    {orders?.items.map((order) => (
                      <option key={order.id} value={order.id}>
                        {order.lot_no} - {order.product?.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Lot No
                  </label>
                  <input
                    type="text"
                    value={newResult.lot_no}
                    onChange={(e) => setNewResult({ ...newResult, lot_no: e.target.value })}
                    className="w-full px-3 py-2 border rounded-md bg-gray-50"
                    readOnly
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    검사자 *
                  </label>
                  <input
                    type="text"
                    value={newResult.inspector}
                    onChange={(e) => setNewResult({ ...newResult, inspector: e.target.value })}
                    className="w-full px-3 py-2 border rounded-md"
                    placeholder="검사자 이름"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    검사일시 *
                  </label>
                  <input
                    type="datetime-local"
                    value={newResult.inspection_date}
                    onChange={(e) => setNewResult({ ...newResult, inspection_date: e.target.value })}
                    className="w-full px-3 py-2 border rounded-md"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    비고
                  </label>
                  <input
                    type="text"
                    value={newResult.remarks}
                    onChange={(e) => setNewResult({ ...newResult, remarks: e.target.value })}
                    className="w-full px-3 py-2 border rounded-md"
                    placeholder="추가 정보..."
                  />
                </div>
              </div>

              {/* Measurement Values */}
              {selectedPlan && (
                <div>
                  <h3 className="text-lg font-semibold mb-4">측정값 입력</h3>
                  <div className="overflow-x-auto">
                    <table className="table">
                      <thead>
                        <tr>
                          <th>검사항목</th>
                          <th>규격</th>
                          <th>상한값</th>
                          <th>하한값</th>
                          <th>목표값</th>
                          <th>측정값 *</th>
                          <th>판정</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedPlan.inspection_items?.map((item, index) => {
                          const measuredValue = newResult.measured_values[index];
                          const isInRange = measuredValue && 
                            (item.usl === null || measuredValue.measured_value <= item.usl) &&
                            (item.lsl === null || measuredValue.measured_value >= item.lsl);
                          
                          return (
                            <tr key={item.id}>
                              <td className="font-medium">{item.item_name}</td>
                              <td className="text-sm">{item.specification}</td>
                              <td className="text-sm">{item.usl || "-"}</td>
                              <td className="text-sm">{item.lsl || "-"}</td>
                              <td className="text-sm">{item.target || "-"}</td>
                              <td>
                                <input
                                  type="number"
                                  step="0.001"
                                  value={measuredValue?.measured_value || ""}
                                  onChange={(e) => {
                                    const raw = e.target.value;
                                    // Allow blank field — only evaluate judgment when a numeric value is present
                                    const value = raw === "" ? 0 : parseFloat(raw);
                                    const hasValue = raw !== "" && !isNaN(value);
                                    const newIsInRange = !hasValue ||
                                      ((item.usl === null || value <= item.usl) &&
                                      (item.lsl === null || value >= item.lsl));
                                    const judgment: "OK" | "NG" = newIsInRange ? "OK" : "NG";
                                    const values = newResult.measured_values.map((mv, i) =>
                                      i === index ? { ...mv, measured_value: value, judgment } : mv
                                    );
                                    setNewResult(prev => ({ ...prev, measured_values: values }));
                                  }}
                                  className="w-24 px-2 py-1 border rounded text-sm"
                                  required
                                />
                              </td>
                              <td>
                                <select
                                  value={measuredValue?.judgment || "OK"}
                                  onChange={(e) => updateMeasuredValue(index, "judgment", e.target.value)}
                                  className="px-2 py-1 border rounded text-sm"
                                >
                                  <option value="OK">OK</option>
                                  <option value="NG">NG</option>
                                </select>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              <div className="flex justify-end gap-2 pt-4 border-t">
                <button
                  type="button"
                  onClick={() => { resetNewResult(); setShowCreateModal(false); }}
                  className="btn btn-secondary"
                >
                  취소
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending || !selectedPlan}
                  className="btn btn-primary"
                >
                  {createMutation.isPending ? "등록 중..." : "등록"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Detail Modal */}
      {showDetailModal && selectedResult && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="text-lg font-semibold">측정결과 상세</h2>
              <button
                onClick={() => setShowDetailModal(false)}
                className="p-2 hover:bg-gray-100 rounded"
              >
                <X size={20} />
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Basic Info */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                <div>
                  <label className="text-sm text-gray-600">Lot No</label>
                  <p className="font-medium">{selectedResult.lot_no}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-600">제품명</label>
                  <p className="font-medium">{selectedResult.work_order?.product?.name || "정보 없음"}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-600">검사자</label>
                  <p className="font-medium">{selectedResult.inspector || "-"}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-600">검사일시</label>
                  <p className="font-medium">{selectedResult.inspection_date ? new Date(selectedResult.inspection_date).toLocaleString() : selectedResult.measured_at ? new Date(selectedResult.measured_at).toLocaleString() : "-"}</p>
                </div>
              </div>

              {/* Overall Judgment */}
              <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600">최종 판정:</span>
                  {(() => {
                    const j = selectedResult.judgment as keyof typeof judgmentIcons | null;
                    const JIcon = (j && judgmentIcons[j]) || FileText;
                    const jColor = (j && judgmentColors[j]) || "bg-gray-100 text-gray-800";
                    const jLabel = (j && judgmentLabels[j]) || "미판정";
                    const jIconColor = j === "OK" ? "text-green-600" :
                      j === "NG" ? "text-red-600" :
                      j === "REWORK" ? "text-yellow-600" : "text-gray-400";
                    return (
                      <div className="flex items-center gap-2">
                        <JIcon size={20} className={jIconColor} />
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${jColor}`}>
                          {jLabel}
                        </span>
                      </div>
                    );
                  })()}
                </div>
                {selectedResult.measurement_metadata?.notes && (
                  <div className="flex-1">
                    <span className="text-sm text-gray-600">비고:</span>
                    <span className="ml-2">{selectedResult.measurement_metadata.notes}</span>
                  </div>
                )}
              </div>

              {/* Measurement Data */}
              <div>
                <h3 className="text-lg font-semibold mb-4">측정 데이터</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 bg-gray-50 rounded-lg p-4">
                  <div>
                    <label className="text-sm text-gray-600">측정값</label>
                    <p className="font-medium text-lg">{selectedResult.measured_value}</p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-600">편차</label>
                    <p className="font-medium">{selectedResult.deviation != null ? selectedResult.deviation.toFixed(4) : "-"}</p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-600">측정 소스</label>
                    <p className="font-medium">{selectedResult.source || "-"}</p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-600">적합 여부</label>
                    <p className={`font-medium ${selectedResult.is_conforming ? "text-green-600" : "text-red-600"}`}>
                      {selectedResult.is_conforming ? "적합" : "부적합"}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}