"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { analyticsService } from "@/services/analytics";
import { equipmentService } from "@/services/equipment";
import { EquipmentUtilization, Equipment, AnalyticsFilters } from "@/types";
import { 
  Activity, 
  Cpu, 
  AlertTriangle, 
  Clock,
  TrendingUp,
  TrendingDown,
  Wrench,
  Play,
  Pause,
  Square,
  BarChart3,
  PieChart
} from "lucide-react";
import { POLLING } from "@/config/constants";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  PieChart as RePieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  ComposedChart,
  Area
} from "recharts";

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4'];

const statusColors = {
  RUN: "bg-green-100 text-green-800",
  STOP: "bg-gray-100 text-gray-800", 
  ERROR: "bg-red-100 text-red-800",
};

const statusLabels = {
  RUN: "가동중",
  STOP: "정지", 
  ERROR: "오류",
};

const statusIcons = {
  RUN: Play,
  STOP: Square,
  ERROR: AlertTriangle,
};

export default function EquipmentAnalyticsPage() {
  const [filters, setFilters] = useState<AnalyticsFilters>({
    date_from: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    date_to: new Date().toISOString().split('T')[0],
    period: "daily",
  });

  const [selectedEquipment, setSelectedEquipment] = useState<number | null>(null);

  const { data: equipment } = useQuery({
    queryKey: ["equipment-list"],
    queryFn: () => equipmentService.getAll(),
  });

  const { data: utilization, isLoading: utilizationLoading } = useQuery({
    queryKey: ["equipment-utilization", filters],
    queryFn: () => analyticsService.getEquipmentUtilization(filters),
    refetchInterval: POLLING.NORMAL,
  });

  const { data: efficiency } = useQuery({
    queryKey: ["equipment-efficiency", selectedEquipment, filters],
    queryFn: () => selectedEquipment 
      ? analyticsService.getEquipmentEfficiency(selectedEquipment, filters.date_from, filters.date_to)
      : Promise.resolve(null),
    enabled: !!selectedEquipment,
  });

  const getUtilizationColor = (rate: number) => {
    if (rate >= 85) return "text-green-600";
    if (rate >= 70) return "text-yellow-600";
    return "text-red-600";
  };

  const getUtilizationLevel = (rate: number) => {
    if (rate >= 85) return "우수";
    if (rate >= 70) return "보통";
    return "미흡";
  };

  const utilizationStats = utilization && utilization.length > 0 ? {
    avgUtilization: utilization.reduce((sum, eq) => sum + (eq.utilization_rate || 0), 0) / utilization.length,
    maxUtilization: Math.max(...utilization.map(eq => eq.utilization_rate || 0)),
    minUtilization: Math.min(...utilization.map(eq => eq.utilization_rate || 0)),
    highPerformers: utilization.filter(eq => (eq.utilization_rate || 0) >= 85).length,
    needsAttention: utilization.filter(eq => (eq.utilization_rate || 0) < 70).length,
  } : null;

  const downtimeData = efficiency?.downtime_breakdown?.map((item, index) => ({
    ...item,
    color: COLORS[index % COLORS.length],
    percentage: efficiency.planned_time > 0 ? (item.duration / efficiency.planned_time) * 100 : 0,
  })) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">설비 가동률 분석</h1>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">기간:</label>
            <input
              type="date"
              value={filters.date_from || ""}
              onChange={(e) => setFilters({ ...filters, date_from: e.target.value })}
              className="px-3 py-1 border rounded text-sm"
            />
            <span className="text-gray-500">~</span>
            <input
              type="date"
              value={filters.date_to || ""}
              onChange={(e) => setFilters({ ...filters, date_to: e.target.value })}
              className="px-3 py-1 border rounded text-sm"
            />
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">주기:</label>
            <select
              value={filters.period || "daily"}
              onChange={(e) => setFilters({ ...filters, period: e.target.value as "daily" | "weekly" | "monthly" })}
              className="px-3 py-1 border rounded text-sm"
            >
              <option value="daily">일별</option>
              <option value="weekly">주별</option>
              <option value="monthly">월별</option>
            </select>
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      {utilizationStats && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">평균 가동률</p>
                <p className={`text-2xl font-bold ${getUtilizationColor(utilizationStats.avgUtilization)}`}>
                  {utilizationStats.avgUtilization.toFixed(1)}%
                </p>
              </div>
              <div className="p-3 rounded-full bg-primary-100">
                <Activity className="h-6 w-6 text-primary-600" />
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">최고 가동률</p>
                <p className="text-2xl font-bold text-green-600">
                  {utilizationStats.maxUtilization.toFixed(1)}%
                </p>
              </div>
              <div className="p-3 rounded-full bg-green-100">
                <TrendingUp className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">최저 가동률</p>
                <p className="text-2xl font-bold text-red-600">
                  {utilizationStats.minUtilization.toFixed(1)}%
                </p>
              </div>
              <div className="p-3 rounded-full bg-red-100">
                <TrendingDown className="h-6 w-6 text-red-600" />
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">우수 설비</p>
                <p className="text-2xl font-bold text-green-600">{utilizationStats.highPerformers}</p>
                <p className="text-xs text-gray-500">≥85% 가동률</p>
              </div>
              <div className="p-3 rounded-full bg-green-100">
                <Cpu className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">관심 설비</p>
                <p className="text-2xl font-bold text-red-600">{utilizationStats.needsAttention}</p>
                <p className="text-xs text-gray-500">&lt;70% 가동률</p>
              </div>
              <div className="p-3 rounded-full bg-red-100">
                <AlertTriangle className="h-6 w-6 text-red-600" />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Equipment Selection */}
      <div className="card">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">설비 선택:</label>
            <select
              value={selectedEquipment || ""}
              onChange={(e) => setSelectedEquipment(e.target.value ? parseInt(e.target.value) : null)}
              className="px-3 py-2 border rounded-md min-w-64"
            >
              <option value="">전체 설비 현황</option>
              {equipment?.map((eq) => (
                <option key={eq.id} value={eq.id}>
                  {eq.eq_name} ({eq.equipment_type})
                </option>
              ))}
            </select>
          </div>
          {selectedEquipment && (
            <div className="flex items-center gap-4 ml-auto">
              {(() => {
                const eq = equipment?.find(e => e.id === selectedEquipment);
                if (!eq) return null;
                const StatusIcon = statusIcons[eq.current_status as keyof typeof statusIcons];
                return (
                  <div className="flex items-center gap-2">
                    <StatusIcon size={20} className={`${
                      eq.current_status === "RUN" ? "text-green-600" : 
                      eq.current_status === "ERROR" ? "text-red-600" : "text-gray-600"
                    }`} />
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[eq.current_status as keyof typeof statusColors]}`}>
                      {statusLabels[eq.current_status as keyof typeof statusLabels]}
                    </span>
                  </div>
                );
              })()}
            </div>
          )}
        </div>
      </div>

      {!selectedEquipment ? (
        /* Overall Equipment Utilization */
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Utilization Chart */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">설비별 가동률</h2>
              <BarChart3 className="h-5 w-5 text-gray-400" />
            </div>
            {utilizationLoading ? (
              <div className="h-80 flex items-center justify-center text-gray-500">
                로딩 중...
              </div>
            ) : (
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={utilization?.slice(0, 10)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="equipment_name" 
                      angle={-45} 
                      textAnchor="end" 
                      height={80}
                      interval={0}
                    />
                    <YAxis domain={[0, 100]} />
                    <Tooltip 
                      formatter={(value: any) => [`${Number(value || 0).toFixed(1)}%`, "가동률"]}
                      labelFormatter={(label) => `설비: ${label}`}
                    />
                    <Bar
                      dataKey="utilization_rate"
                      fill="#3B82F6"
                      shape={(props: any) => {
                        const { x, y, width, height, payload } = props;
                        const color = (payload?.utilization_rate ?? 0) >= 85 ? "#10B981" :
                                     (payload?.utilization_rate ?? 0) >= 70 ? "#F59E0B" : "#EF4444";
                        return <rect x={x} y={y} width={width} height={height} fill={color} rx={2} />;
                      }}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          {/* Equipment List */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">설비 현황</h2>
              <Cpu className="h-5 w-5 text-gray-400" />
            </div>
            <div className="space-y-3 max-h-80 overflow-y-auto">
              {utilization?.map((eq) => {
                const StatusIcon = statusIcons[eq.equipment?.current_status as keyof typeof statusIcons] || Activity;
                return (
                  <div key={eq.equipment_id} className="p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <StatusIcon size={20} className={`${
                          eq.equipment?.current_status === "RUN" ? "text-green-600" : 
                          eq.equipment?.current_status === "ERROR" ? "text-red-600" : "text-gray-600"
                        }`} />
                        <div>
                          <p className="font-medium">{eq.equipment_name}</p>
                          <p className="text-sm text-gray-600">{eq.equipment_type}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className={`font-bold ${getUtilizationColor(eq.utilization_rate)}`}>
                          {(eq.utilization_rate || 0).toFixed(1)}%
                        </p>
                        <p className="text-sm text-gray-600">
                          {getUtilizationLevel(eq.utilization_rate)}
                        </p>
                      </div>
                    </div>
                    <div className="mt-2 grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <p className="text-gray-600">가동시간</p>
                        <p className="font-medium">{(eq.running_time || 0).toFixed(1)}h</p>
                      </div>
                      <div>
                        <p className="text-gray-600">대기시간</p>
                        <p className="font-medium">{(eq.idle_time || 0).toFixed(1)}h</p>
                      </div>
                      <div>
                        <p className="text-gray-600">오류시간</p>
                        <p className="font-medium text-red-600">{(eq.error_time || 0).toFixed(1)}h</p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      ) : (
        /* Individual Equipment Analysis */
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Equipment Info */}
          {efficiency && (
            <div className="card">
              <h2 className="text-lg font-semibold mb-4">{efficiency.equipment_name} 상세 분석</h2>
              
              {/* Basic Stats */}
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="p-3 bg-primary-50 rounded-lg">
                  <p className="text-sm text-primary-600">계획시간</p>
                  <p className="text-xl font-bold text-primary-900">{(efficiency.planned_time || 0).toFixed(1)}h</p>
                </div>
                <div className="p-3 bg-green-50 rounded-lg">
                  <p className="text-sm text-green-600">실제가동</p>
                  <p className="text-xl font-bold text-green-900">{(efficiency.actual_time || 0).toFixed(1)}h</p>
                </div>
              </div>

              {/* Efficiency Trend */}
              <div className="h-64">
                <h3 className="text-sm font-medium mb-2">효율성 추이</h3>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={efficiency.efficiency_trend.map(item => ({
                    ...item,
                    date: new Date(item.date).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' }),
                  }))}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis domain={[0, 100]} />
                    <Tooltip formatter={(value: any) => [`${Number(value || 0).toFixed(1)}%`]} />
                    <Line
                      type="monotone"
                      dataKey="efficiency"
                      stroke="#3B82F6"
                      strokeWidth={2}
                      name="효율성"
                    />
                    <Line 
                      type="monotone" 
                      dataKey="utilization" 
                      stroke="#10B981" 
                      strokeWidth={2}
                      name="가동률"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Downtime Analysis */}
          {downtimeData.length > 0 && (
            <div className="card">
              <h2 className="text-lg font-semibold mb-4">다운타임 분석</h2>
              
              <div className="grid grid-cols-1 gap-4">
                {/* Downtime Pie Chart */}
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <RePieChart>
                      <Pie
                        data={downtimeData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ reason, percentage }) =>
                          (percentage || 0) > 5 ? `${reason} (${Number(percentage || 0).toFixed(1)}%)` : ''
                        }
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="duration"
                      >
                        {downtimeData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip 
                        formatter={(value: any, name: string, props: any) => [
                          `${Number(value || 0).toFixed(1)}시간 (${Number(props.payload.percentage || 0).toFixed(1)}%)`,
                          props.payload.reason
                        ]}
                      />
                    </RePieChart>
                  </ResponsiveContainer>
                </div>

                {/* Downtime Details */}
                <div className="space-y-2">
                  {downtimeData.map((item, index) => (
                    <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                      <div className="flex items-center gap-2">
                        <div 
                          className="w-4 h-4 rounded" 
                          style={{ backgroundColor: item.color }}
                        />
                        <span className="text-sm font-medium">{item.reason}</span>
                      </div>
                      <div className="text-right text-sm">
                        <p className="font-medium">{(item.duration || 0).toFixed(1)}h</p>
                        <p className="text-gray-600">{item.count}회</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Maintenance Schedule */}
          {efficiency?.maintenance_schedule && efficiency.maintenance_schedule.length > 0 && (
            <div className="card lg:col-span-2">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">정비 계획</h2>
                <Wrench className="h-5 w-5 text-gray-400" />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {efficiency.maintenance_schedule.map((schedule, index) => (
                  <div key={index} className="p-4 border rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <Wrench size={16} className="text-primary-600" />
                      <span className="font-medium">{schedule.maintenance_type}</span>
                    </div>
                    <p className="text-sm text-gray-600 mb-1">
                      예정일: {new Date(schedule.scheduled_date).toLocaleDateString()}
                    </p>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      schedule.status === "완료" ? "bg-green-100 text-green-800" :
                      schedule.status === "진행중" ? "bg-yellow-100 text-yellow-800" :
                      "bg-gray-100 text-gray-800"
                    }`}>
                      {schedule.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}