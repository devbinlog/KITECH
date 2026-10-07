"use client";

import React, { useState, useMemo, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { analyticsService } from "@/services/analytics";
import ErrorBoundary from "@/components/ErrorBoundary";
import { createErrorHandler } from "@/lib/errorHandler";
import { 
  TrendingUp, 
  TrendingDown, 
  BarChart3, 
  Activity, 
  Gauge,
  Clock,
  Target,
  AlertTriangle
} from "lucide-react";
import Link from "next/link";
import { POLLING } from "@/config/constants";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  ComposedChart,
  Area,
  AreaChart
} from "recharts";

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4'];

const kpiColorMap: Record<string, { bg: string; text: string }> = {
  blue:   { bg: 'bg-primary-100',   text: 'text-primary-600' },
  green:  { bg: 'bg-green-100',  text: 'text-green-600' },
  yellow: { bg: 'bg-yellow-100', text: 'text-yellow-600' },
  purple: { bg: 'bg-purple-100', text: 'text-purple-600' },
  indigo: { bg: 'bg-primary-100', text: 'text-primary-600' },
  red:    { bg: 'bg-red-100',    text: 'text-red-600' },
};

export default function AnalyticsDashboard() {
  const [dateRange, setDateRange] = useState({
    date_from: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    date_to: new Date().toISOString().split('T')[0],
  });

  // Memoized date change handlers
  const handleDateFromChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setDateRange(prev => ({ ...prev, date_from: e.target.value }));
  }, []);

  const handleDateToChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setDateRange(prev => ({ ...prev, date_to: e.target.value }));
  }, []);

  const { data: kpiSummary, isLoading: kpiLoading, error } = useQuery({
    queryKey: ["kpi-summary", dateRange],
    queryFn: () => analyticsService.getKPISummary(dateRange.date_from, dateRange.date_to),
    refetchInterval: POLLING.NORMAL,
  });

  // 에러 처리
  React.useEffect(() => {
    if (error) {
      createErrorHandler()(error);
    }
  }, [error]);

  const { data: productionTrends, isLoading: trendsLoading } = useQuery({
    queryKey: ["production-trends", dateRange],
    queryFn: () => analyticsService.getProductionTrends(dateRange.date_from, dateRange.date_to, "daily"),
    refetchInterval: POLLING.NORMAL,
  });

  const { data: resourceUtilization } = useQuery({
    queryKey: ["resource-utilization", dateRange],
    queryFn: () => analyticsService.getResourceUtilization(dateRange.date_from, dateRange.date_to),
    refetchInterval: POLLING.SLOW,
  });

  if (kpiLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-800">분석 대시보드</h1>
        <div className="text-center py-8 text-gray-500">로딩 중...</div>
      </div>
    );
  }

  const kpiCards = [
    {
      title: "전체 OEE",
      value: `${(kpiSummary?.overall_oee || 0).toFixed(1)}%`,
      icon: Gauge,
      color: "blue",
      change: kpiSummary?.overall_oee && kpiSummary.overall_oee > 75 ? "up" : "down",
      target: 85,
    },
    {
      title: "가용성",
      value: `${(kpiSummary?.availability || 0).toFixed(1)}%`,
      icon: Activity,
      color: "green",
      change: kpiSummary?.availability && kpiSummary.availability > 90 ? "up" : "down",
      target: 95,
    },
    {
      title: "성능효율",
      value: `${(kpiSummary?.performance || 0).toFixed(1)}%`,
      icon: TrendingUp,
      color: "yellow",
      change: kpiSummary?.performance && kpiSummary.performance > 85 ? "up" : "down",
      target: 90,
    },
    {
      title: "품질지수",
      value: `${(kpiSummary?.quality || 0).toFixed(1)}%`,
      icon: Target,
      color: "purple",
      change: kpiSummary?.quality && kpiSummary.quality > 95 ? "up" : "down",
      target: 99,
    },
    {
      title: "총 생산량",
      value: (kpiSummary?.total_production || 0).toLocaleString(),
      icon: BarChart3,
      color: "indigo",
      change: null,
      unit: "개",
    },
    {
      title: "불량률",
      value: `${(kpiSummary?.defect_rate || 0).toFixed(2)}%`,
      icon: AlertTriangle,
      color: "red",
      change: kpiSummary?.defect_rate && kpiSummary.defect_rate < 2 ? "down" : "up",
      target: 1,
    },
  ];

  const oeeData = kpiSummary?.trend_data?.map(item => ({
    ...item,
    date: new Date(item.date).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' }),
  })) || [];

  const productionChartData = productionTrends?.production_volume?.map(item => ({
    ...item,
    date: new Date(item.date).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' }),
    efficiency_percent: item.efficiency * 100,
  })) || [];

  return (
    <ErrorBoundary>
      <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">분석 대시보드</h1>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">기간:</label>
            <input
              type="date"
              value={dateRange.date_from}
              onChange={handleDateFromChange}
              className="px-3 py-1 border rounded text-sm"
            />
            <span className="text-gray-500">~</span>
            <input
              type="date"
              value={dateRange.date_to}
              onChange={handleDateToChange}
              className="px-3 py-1 border rounded text-sm"
            />
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-6">
        {kpiCards.map((card, index) => {
          const Icon = card.icon;
          const currentValue = parseFloat(card.value.replace('%', '').replace(/,/g, ''));
          const isGood = card.target ? 
            (card.title === "불량률" ? currentValue <= card.target : currentValue >= card.target) :
            card.change === "up";

          return (
            <div key={index} className="card">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">{card.title}</p>
                  <p className="text-xl font-bold text-gray-900">
                    {card.value}{card.unit && <span className="text-sm text-gray-500 ml-1">{card.unit}</span>}
                  </p>
                  {card.target && (
                    <p className="text-xs text-gray-500">목표: {card.target}{card.value.includes('%') ? '%' : card.unit || ''}</p>
                  )}
                </div>
                <div className={`p-3 rounded-full ${kpiColorMap[card.color]?.bg || 'bg-gray-100'}`}>
                  <Icon className={`h-6 w-6 ${kpiColorMap[card.color]?.text || 'text-gray-600'}`} />
                </div>
              </div>
              {card.change && (
                <div className="mt-2 flex items-center">
                  {isGood ? (
                    <TrendingUp className="h-4 w-4 text-green-600 mr-1" />
                  ) : (
                    <TrendingDown className="h-4 w-4 text-red-600 mr-1" />
                  )}
                  <span className={`text-sm ${isGood ? "text-green-600" : "text-red-600"}`}>
                    {isGood ? "목표 달성" : "개선 필요"}
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* OEE Trend Chart */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">OEE 트렌드</h2>
            <Gauge className="h-5 w-5 text-gray-400" />
          </div>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={oeeData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis domain={[0, 100]} />
                <Tooltip formatter={(value: any, name: string) => [`${Number(value || 0).toFixed(1)}%`, name]} />
                
                {/* Target Line */}
                <Line 
                  type="monotone" 
                  dataKey={() => 85}
                  stroke="#E5E7EB" 
                  strokeDasharray="5 5" 
                  dot={false}
                  name="목표 OEE"
                />
                
                <Area
                  dataKey="oee"
                  fill="#3B82F6"
                  fillOpacity={0.1}
                  stroke="none"
                  legendType="none"
                />
                <Line 
                  type="monotone" 
                  dataKey="oee" 
                  stroke="#3B82F6" 
                  strokeWidth={3}
                  name="OEE"
                />
                <Line 
                  type="monotone" 
                  dataKey="availability" 
                  stroke="#10B981" 
                  strokeWidth={2}
                  name="가용성"
                />
                <Line 
                  type="monotone" 
                  dataKey="performance" 
                  stroke="#F59E0B" 
                  strokeWidth={2}
                  name="성능효율"
                />
                <Line 
                  type="monotone" 
                  dataKey="quality" 
                  stroke="#8B5CF6" 
                  strokeWidth={2}
                  name="품질지수"
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Production Volume Chart */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">생산량 실적</h2>
            <BarChart3 className="h-5 w-5 text-gray-400" />
          </div>
          {trendsLoading ? (
            <div className="h-80 flex items-center justify-center text-gray-500">
              로딩 중...
            </div>
          ) : (
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={productionChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis yAxisId="left" orientation="left" />
                  <YAxis yAxisId="right" orientation="right" domain={[0, 120]} />
                  <Tooltip 
                    formatter={(value: any, name: string) => {
                      if (name === "efficiency_percent") return [`${Number(value || 0).toFixed(1)}%`, "달성률"];
                      return [Number(value || 0).toLocaleString(), name];
                    }}
                  />
                  
                  <Bar yAxisId="left" dataKey="planned" fill="#E5E7EB" name="계획량" />
                  <Bar yAxisId="left" dataKey="actual" fill="#3B82F6" name="실제량" />
                  <Line 
                    yAxisId="right" 
                    type="monotone" 
                    dataKey="efficiency_percent" 
                    stroke="#10B981" 
                    strokeWidth={3}
                    name="달성률"
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>

      {/* Resource Utilization */}
      {resourceUtilization && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Equipment Utilization */}
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">설비 가동률</h2>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={resourceUtilization.equipment_utilization?.slice(0, 8)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="equipment_name" angle={-45} textAnchor="end" height={80} />
                  <YAxis domain={[0, 100]} />
                  <Tooltip formatter={(value: any) => [`${Number(value || 0).toFixed(1)}%`, "가동률"]} />
                  <Bar dataKey="utilization_rate" fill="#3B82F6" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Workforce Utilization */}
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">인력 가동률</h2>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={resourceUtilization.workforce_utilization}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="shift" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" domain={[0, 120]} />
                  <Tooltip />
                  
                  <Bar yAxisId="left" dataKey="planned_hours" fill="#E5E7EB" name="계획시간" />
                  <Bar yAxisId="left" dataKey="worked_hours" fill="#10B981" name="작업시간" />
                  <Bar yAxisId="left" dataKey="overtime_hours" fill="#F59E0B" name="연장시간" />
                  <Line 
                    yAxisId="right" 
                    type="monotone" 
                    dataKey="efficiency" 
                    stroke="#EF4444" 
                    strokeWidth={2}
                    name="효율성 (%)"
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* Quality Trends */}
      {productionTrends?.quality_trends && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">품질 트렌드</h2>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={productionTrends.quality_trends.map(item => ({
                ...item,
                date: new Date(item.date).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' }),
              }))}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis domain={[0, 100]} />
                <Tooltip formatter={(value: any) => [`${Number(value || 0).toFixed(2)}%`]} />
                
                <Area
                  type="monotone"
                  dataKey="pass_rate"
                  stackId="quality"
                  stroke="#10B981"
                  fill="#10B981"
                  fillOpacity={0.6}
                  name="합격률"
                />
                <Area
                  type="monotone"
                  dataKey="rework_rate"
                  stackId="quality"
                  stroke="#F59E0B"
                  fill="#F59E0B"
                  fillOpacity={0.6}
                  name="재작업률"
                />
                <Area
                  type="monotone"
                  dataKey="defect_rate"
                  stackId="quality"
                  stroke="#EF4444"
                  fill="#EF4444"
                  fillOpacity={0.6}
                  name="불량률"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">분석 메뉴</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Link
            href="/analytics/equipment"
            className="flex flex-col items-center p-4 bg-primary-50 hover:bg-primary-100 rounded-lg transition-colors"
          >
            <Activity className="h-8 w-8 text-primary-600 mb-2" />
            <span className="text-sm font-medium text-primary-900">설비 분석</span>
          </Link>
          <Link
            href="/analytics/lot-trace"
            className="flex flex-col items-center p-4 bg-green-50 hover:bg-green-100 rounded-lg transition-colors"
          >
            <Target className="h-8 w-8 text-green-600 mb-2" />
            <span className="text-sm font-medium text-green-900">Lot 추적</span>
          </Link>
          <div className="flex flex-col items-center p-4 bg-yellow-50 hover:bg-yellow-100 rounded-lg transition-colors opacity-75 cursor-not-allowed">
            <TrendingUp className="h-8 w-8 text-yellow-600 mb-2" />
            <span className="text-sm font-medium text-yellow-900">예측 분석</span>
          </div>
          <div className="flex flex-col items-center p-4 bg-purple-50 hover:bg-purple-100 rounded-lg transition-colors opacity-75 cursor-not-allowed">
            <BarChart3 className="h-8 w-8 text-purple-600 mb-2" />
            <span className="text-sm font-medium text-purple-900">비용 분석</span>
          </div>
        </div>
      </div>
    </div>
    </ErrorBoundary>
  );
}