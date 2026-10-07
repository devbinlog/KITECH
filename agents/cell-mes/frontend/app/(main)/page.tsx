"use client";

import { useQuery } from "@tanstack/react-query";
import { equipmentService } from "@/services/equipment";
import { productionService } from "@/services/production";
import { EquipmentCard } from "@/components/equipment/EquipmentCard";
import { AISummaryWidget } from "@/components/dashboard/AISummaryWidget";
import { RefreshCw, Package, Cpu, ClipboardList, CheckCircle } from "lucide-react";
import { POLLING, PAGE_SIZE } from "@/config/constants";

export default function DashboardPage() {
  const { data: equipments, isLoading: loadingEquipments } = useQuery({
    queryKey: ["equipments"],
    queryFn: () => equipmentService.getAll(),
    refetchInterval: POLLING.FAST,
  });

  // Fetch ALL orders for accurate stats calculation
  const { data: allOrdersData, isLoading: loadingAllOrders } = useQuery({
    queryKey: ["dashboard-orders-stats"],
    queryFn: () => productionService.getOrders({ limit: PAGE_SIZE.ALL_ORDERS, view: "all" }),
    refetchInterval: POLLING.FAST,
  });

  // Fetch limited orders for display
  const { data: displayOrdersData, isLoading: loadingDisplayOrders } = useQuery({
    queryKey: ["dashboard-orders-display"],
    queryFn: () => productionService.getOrders({ limit: 5, view: "all" }),
    refetchInterval: POLLING.FAST,
  });

  const allOrders = allOrdersData?.items || [];
  const displayOrders = displayOrdersData?.items || [];
  const isLoadingOrders = loadingAllOrders || loadingDisplayOrders;

  // Calculate stats from ALL orders
  const stats = {
    totalEquipments: equipments?.length || 0,
    runningEquipments: equipments?.filter((e) => e.current_status === "RUN").length || 0,
    errorEquipments: equipments?.filter((e) => e.current_status === "ERROR").length || 0,
    activeOrders: allOrders.filter((o) => o.status === "RUNNING").length,
    completedOrders: allOrders.filter((o) => o.status === "DONE").length,
  };

  const isRefreshing = loadingEquipments || isLoadingOrders;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">대시보드</h1>
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <RefreshCw size={16} className={isRefreshing ? "animate-spin" : ""} />
          <span>5초마다 자동 갱신</span>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-primary-100 rounded-lg">
              <Cpu className="text-primary-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-500">전체 설비</p>
              <p className="text-2xl font-bold">{stats.totalEquipments}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-green-100 rounded-lg">
              <Cpu className="text-green-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-500">가동중 설비</p>
              <p className="text-2xl font-bold text-green-600">{stats.runningEquipments}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-yellow-100 rounded-lg">
              <ClipboardList className="text-yellow-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-500">진행중 작업</p>
              <p className="text-2xl font-bold text-yellow-600">{stats.activeOrders}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-purple-100 rounded-lg">
              <CheckCircle className="text-purple-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-500">완료 작업</p>
              <p className="text-2xl font-bold text-purple-600">{stats.completedOrders}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Equipment Grid */}
      <div>
        <h2 className="text-lg font-semibold text-gray-800 mb-4">설비 현황</h2>
        {loadingEquipments ? (
          <div className="text-center py-8 text-gray-500">로딩 중...</div>
        ) : equipments && equipments.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {equipments.map((equipment) => (
              <EquipmentCard key={equipment.id} equipment={equipment} />
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            등록된 설비가 없습니다. 설비 관리에서 AAS 동기화를 실행해주세요.
          </div>
        )}
      </div>

      {/* Recent Orders */}
      <div>
        <h2 className="text-lg font-semibold text-gray-800 mb-4">
          최근 작업지시
          <span className="ml-2 text-sm text-gray-500">
            (전체 {allOrdersData?.total || 0}건 중 최신 5건)
          </span>
        </h2>
        {isLoadingOrders ? (
          <div className="text-center py-8 text-gray-500">로딩 중...</div>
        ) : displayOrders && displayOrders.length > 0 ? (
          <div className="card overflow-hidden">
            <table className="table">
              <thead>
                <tr>
                  <th>Lot No</th>
                  <th>상태</th>
                  <th>목표수량</th>
                  <th>생성일</th>
                </tr>
              </thead>
              <tbody>
                {displayOrders.map((order) => (
                  <tr key={order.id}>
                    <td className="font-medium">{order.lot_no}</td>
                    <td>
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-medium ${
                          order.status === "RUNNING"
                            ? "bg-green-100 text-green-800"
                            : order.status === "DONE"
                            ? "bg-primary-100 text-primary-800"
                            : order.status === "ERROR"
                            ? "bg-red-100 text-red-800"
                            : "bg-gray-100 text-gray-800"
                        }`}
                      >
                        {order.status}
                      </span>
                    </td>
                    <td>{order.target_qty}</td>
                    <td className="text-gray-500">
                      {new Date(order.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">작업지시가 없습니다.</div>
        )}
      </div>

      {/* AI Summary Widget */}
      <div>
        <h2 className="text-lg font-semibold text-gray-800 mb-4">AI 인사이트</h2>
        <AISummaryWidget />
      </div>
    </div>
  );
}
