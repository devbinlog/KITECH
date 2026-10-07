"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { productionService } from "@/services/production";
import { equipmentService } from "@/services/equipment";
import { ProdResult, WorkOrder, ResultFilters } from "@/types";
import { Clock, CheckCircle, XCircle, Activity, ChevronLeft, ChevronRight, Plus, X } from "lucide-react";
import { format } from "date-fns";

export default function ResultsPage() {
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState<ResultFilters>({
    page: 1,
    limit: 30,
  });
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newResult, setNewResult] = useState({
    work_order_id: 0,
    equipment_id: undefined as number | undefined,
    ok_qty: 0,
    ng_qty: 0,
    start_time: "",
    end_time: "",
  });

  const { data: resultsData, isLoading: loadingResults, isError: isResultsError } = useQuery({
    queryKey: ["results", filters],
    queryFn: () => productionService.getResults(filters),
  });

  const { data: ordersData } = useQuery({
    queryKey: ["orders-for-results"],
    queryFn: () => productionService.getOrders({ limit: 100, view: "all" }),
    staleTime: 30000,
  });

  const { data: equipmentList } = useQuery({
    queryKey: ["equipment-for-results"],
    queryFn: () => equipmentService.getAll(),
  });

  const createMutation = useMutation({
    mutationFn: productionService.createResult,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["results"] });
      setShowCreateModal(false);
      resetNewResult();
    },
    onError: (error: any) => {
      alert(`실적 등록 실패: ${error.response?.data?.detail || error.message}`);
    },
  });

  const resetNewResult = () => {
    setNewResult({
      work_order_id: 0,
      equipment_id: undefined,
      ok_qty: 0,
      ng_qty: 0,
      start_time: "",
      end_time: "",
    });
  };

  const results = resultsData?.items || [];
  const totalItems = resultsData?.total || 0;
  const totalPages = resultsData?.pages || 1;
  const currentPage = filters.page || 1;
  const orders = ordersData?.items || [];

  // Calculate summary stats
  const stats = {
    totalResults: totalItems,
    totalOk: results.reduce((sum, r) => sum + r.ok_qty, 0),
    totalNg: results.reduce((sum, r) => sum + r.ng_qty, 0),
    yieldRate: 0,
  };

  if (stats.totalOk + stats.totalNg > 0) {
    stats.yieldRate = (stats.totalOk / (stats.totalOk + stats.totalNg)) * 100;
  }

  const getOrderLotNo = (workOrderId: number) => {
    return orders.find((o) => o.id === workOrderId)?.lot_no || `WO-${workOrderId}`;
  };

  const getEquipmentName = (equipmentId: number | null) => {
    if (!equipmentId) return "-";
    return equipmentList?.find((eq) => eq.id === equipmentId)?.eq_name || `EQ-${equipmentId}`;
  };

  const formatDateTime = (dateStr: string | null) => {
    if (!dateStr) return "-";
    return format(new Date(dateStr), "MM/dd HH:mm");
  };

  const calculateDuration = (start: string | null, end: string | null) => {
    if (!start || !end) return "-";
    const diff = new Date(end).getTime() - new Date(start).getTime();
    if (diff <= 0) return "-";
    const totalMinutes = Math.floor(diff / 60000);
    const hours = Math.floor(totalMinutes / 60);
    const mins = totalMinutes % 60;
    return hours > 0 ? `${hours}시간 ${mins}분` : `${mins}분`;
  };

  const handlePageChange = (newPage: number) => {
    setFilters({ ...filters, page: newPage });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">생산 실적</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn btn-primary flex items-center gap-2"
        >
          <Plus size={16} />
          실적 등록
        </button>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">작업지시:</label>
            <select
              value={filters.workOrderId || ""}
              onChange={(e) => setFilters({ ...filters, workOrderId: e.target.value ? parseInt(e.target.value) : undefined, page: 1 })}
              className="px-3 py-1 border rounded text-sm min-w-[200px]"
            >
              <option value="">전체</option>
              {orders.map((order) => (
                <option key={order.id} value={order.id}>
                  {order.lot_no} - {order.product?.name || `제품#${order.product_id}`}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-primary-100 rounded-lg">
              <Activity className="text-primary-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-500">총 실적 건수</p>
              <p className="text-2xl font-bold">{stats.totalResults}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-green-100 rounded-lg">
              <CheckCircle className="text-green-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-500">양품 합계 (이 페이지)</p>
              <p className="text-2xl font-bold text-green-600">
                {stats.totalOk.toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-red-100 rounded-lg">
              <XCircle className="text-red-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-500">불량 합계 (이 페이지)</p>
              <p className="text-2xl font-bold text-red-600">{stats.totalNg.toLocaleString()}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-purple-100 rounded-lg">
              <Activity className="text-purple-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-500">수율 (이 페이지)</p>
              <p className="text-2xl font-bold text-purple-600">{stats.yieldRate.toFixed(1)}%</p>
            </div>
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {isResultsError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          실적 데이터를 불러오는 중 오류가 발생했습니다.
        </div>
      )}

      {/* Results Table */}
      {loadingResults ? (
        <div className="text-center py-8 text-gray-500">로딩 중...</div>
      ) : results.length > 0 ? (
        <>
          <div className="card overflow-hidden">
            <table className="table">
              <thead>
                <tr>
                  <th>Lot No</th>
                  <th>공정</th>
                  <th>설비</th>
                  <th>양품</th>
                  <th>불량</th>
                  <th>수율</th>
                  <th>시작</th>
                  <th>종료</th>
                  <th>소요시간</th>
                </tr>
              </thead>
              <tbody>
                {results.map((result) => {
                  const total = result.ok_qty + result.ng_qty;
                  const yieldRate = total > 0 ? (result.ok_qty / total) * 100 : 0;

                  return (
                    <tr key={result.id}>
                      <td className="font-medium">{getOrderLotNo(result.work_order_id)}</td>
                      <td>{result.process_routing_id ? `공정-${result.process_routing_id}` : "-"}</td>
                      <td>{getEquipmentName(result.equipment_id)}</td>
                      <td className="text-green-600 font-medium">{result.ok_qty}</td>
                      <td className="text-red-600 font-medium">{result.ng_qty}</td>
                      <td>
                        <span
                          className={`px-2 py-1 rounded-full text-xs font-medium ${
                            yieldRate >= 95
                              ? "bg-green-100 text-green-800"
                              : yieldRate >= 80
                              ? "bg-yellow-100 text-yellow-800"
                              : "bg-red-100 text-red-800"
                          }`}
                        >
                          {yieldRate.toFixed(1)}%
                        </span>
                      </td>
                      <td className="text-gray-500 text-sm">{formatDateTime(result.start_time)}</td>
                      <td className="text-gray-500 text-sm">{formatDateTime(result.end_time)}</td>
                      <td className="text-gray-500 text-sm">
                        {calculateDuration(result.start_time, result.end_time)}
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
          <p className="text-gray-500">생산 실적이 없습니다.</p>
          <p className="text-sm text-gray-400 mt-1">작업지시를 실행하면 실적이 기록됩니다.</p>
          <button onClick={() => setShowCreateModal(true)} className="btn btn-primary mt-4">
            실적 등록
          </button>
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="text-lg font-semibold">생산 실적 등록</h2>
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
                createMutation.mutate({
                  work_order_id: newResult.work_order_id,
                  equipment_id: newResult.equipment_id,
                  ok_qty: newResult.ok_qty,
                  ng_qty: newResult.ng_qty,
                });
              }}
              className="p-4 space-y-4"
            >
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  작업지시 선택 *
                </label>
                <select
                  value={newResult.work_order_id || ""}
                  onChange={(e) =>
                    setNewResult({ ...newResult, work_order_id: parseInt(e.target.value) || 0 })
                  }
                  className="w-full px-3 py-2 border rounded-md bg-white"
                  required
                >
                  <option value="">작업지시를 선택하세요...</option>
                  {orders
                    .filter((o) => o.status === "RUNNING" || o.status === "PAUSE")
                    .map((order) => (
                      <option key={order.id} value={order.id}>
                        {order.lot_no} - {order.product?.name || `제품#${order.product_id}`}
                      </option>
                    ))}
                </select>
                <p className="text-xs text-gray-500 mt-1">진행중(RUNNING) 또는 일시정지(PAUSE) 상태의 작업만 선택 가능</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  설비 선택
                </label>
                <select
                  value={newResult.equipment_id || ""}
                  onChange={(e) =>
                    setNewResult({ 
                      ...newResult, 
                      equipment_id: e.target.value ? parseInt(e.target.value) : undefined 
                    })
                  }
                  className="w-full px-3 py-2 border rounded-md bg-white"
                >
                  <option value="">설비 선택 (선택사항)</option>
                  {equipmentList?.map((eq) => (
                    <option key={eq.id} value={eq.id}>
                      {eq.eq_name} ({eq.equipment_type})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    양품 수량 *
                  </label>
                  <input
                    type="number"
                    value={newResult.ok_qty}
                    onChange={(e) =>
                      setNewResult({ ...newResult, ok_qty: parseInt(e.target.value) || 0 })
                    }
                    className="w-full px-3 py-2 border rounded-md"
                    min="0"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    불량 수량 *
                  </label>
                  <input
                    type="number"
                    value={newResult.ng_qty}
                    onChange={(e) =>
                      setNewResult({ ...newResult, ng_qty: parseInt(e.target.value) || 0 })
                    }
                    className="w-full px-3 py-2 border rounded-md"
                    min="0"
                    required
                  />
                </div>
              </div>

              {/* Preview Yield */}
              {(newResult.ok_qty > 0 || newResult.ng_qty > 0) && (
                <div className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">예상 수율</span>
                    <span
                      className={`text-lg font-bold ${
                        (newResult.ok_qty + newResult.ng_qty) === 0 ? "text-gray-600"
                          : newResult.ok_qty / (newResult.ok_qty + newResult.ng_qty) >= 0.95
                          ? "text-green-600"
                          : newResult.ok_qty / (newResult.ok_qty + newResult.ng_qty) >= 0.8
                          ? "text-yellow-600"
                          : "text-red-600"
                      }`}
                    >
                      {(newResult.ok_qty + newResult.ng_qty) === 0 ? "0.0" : ((newResult.ok_qty / (newResult.ok_qty + newResult.ng_qty)) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-sm text-gray-600">총 생산량</span>
                    <span className="font-medium">{newResult.ok_qty + newResult.ng_qty}개</span>
                  </div>
                </div>
              )}

              <div className="flex justify-end gap-2 pt-4">
                <button
                  type="button"
                  onClick={() => { resetNewResult(); setShowCreateModal(false); }}
                  className="btn btn-secondary"
                >
                  취소
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending || newResult.work_order_id === 0}
                  className="btn btn-primary"
                >
                  {createMutation.isPending ? "등록 중..." : "등록"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
