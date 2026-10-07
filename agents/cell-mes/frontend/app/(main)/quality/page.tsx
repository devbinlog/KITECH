"use client";

import React, { useState, useEffect, useMemo, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { qualityService } from "@/services/quality";
import ErrorBoundary from "@/components/ErrorBoundary";
import { QualityDashboardLoader } from "@/components/LoadingState";
import { QualityConnectionCard } from "@/components/ConnectionStatus";
import { createErrorHandler } from "@/lib/errorHandler";
import { 
  Shield, 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  TrendingUp, 
  TrendingDown,
  BarChart3,
  FileText,
  Clock
} from "lucide-react";
import Link from "next/link";
import { POLLING } from "@/config/constants";
import {
  BarChart,
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  PieChart, 
  Pie, 
  Cell,
  LineChart,
  Line
} from "recharts";

const COLORS = ['#10B981', '#EF4444', '#F59E0B', '#8B5CF6'];

const kpiColorMap: Record<string, { bg: string; text: string }> = {
  blue: { bg: "bg-primary-100", text: "text-primary-600" },
  green: { bg: "bg-green-100", text: "text-green-600" },
  red: { bg: "bg-red-100", text: "text-red-600" },
  yellow: { bg: "bg-yellow-100", text: "text-yellow-600" },
  purple: { bg: "bg-purple-100", text: "text-purple-600" },
};

// KPI Card Component with React.memo
const KPICard = React.memo(({ card }: { card: any }) => {
  const Icon = card.icon;
  const colors = kpiColorMap[card.color] || kpiColorMap.blue;
  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">{card.title}</p>
          <p className="text-2xl font-bold text-gray-900">{card.value}</p>
        </div>
        <div className={`p-3 rounded-full ${colors.bg}`}>
          <Icon className={`h-6 w-6 ${colors.text}`} />
        </div>
      </div>
      {card.change && (
        <div className="mt-2 flex items-center">
          {card.change === "up" ? (
            <TrendingUp className="h-4 w-4 text-green-600 mr-1" />
          ) : (
            <TrendingDown className="h-4 w-4 text-red-600 mr-1" />
          )}
          <span
            className={`text-sm ${
              card.change === "up" ? "text-green-600" : "text-red-600"
            }`}
          >
            {card.title.includes("불량") ? "개선" : "좋음"}
          </span>
        </div>
      )}
    </div>
  );
});

KPICard.displayName = "KPICard";

export default function QualityDashboard() {
  const [dateRange, setDateRange] = useState({
    date_from: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    date_to: new Date().toISOString().split('T')[0],
  });

  const { data: dashboardData, isLoading, error } = useQuery({
    queryKey: ["quality-dashboard", dateRange],
    queryFn: () => qualityService.getQualityDashboard(dateRange.date_from, dateRange.date_to),
    refetchInterval: POLLING.NORMAL,
    retry: (failureCount, error: any) => {
      // Network 에러는 3회 재시도
      if (error.code === "ERR_NETWORK") return failureCount < 3;
      // 4xx 에러는 재시도 하지 않음
      if (error.response?.status >= 400 && error.response?.status < 500) return false;
      // 5xx 에러는 2회 재시도
      return failureCount < 2;
    },
  });

  // 에러 처리를 useEffect로 이동
  React.useEffect(() => {
    if (error) {
      createErrorHandler("quality")(error);
    }
  }, [error]);

  // 연결 상태 확인을 위한 추가 쿼리
  const { data: connectionData } = useQuery({
    queryKey: ["quality-connection-status"],
    queryFn: async () => {
      try {
        const [plans, results] = await Promise.all([
          qualityService.getInspectionPlans({ limit: 200 }),
          qualityService.getInspectionResults({ limit: 200 })
        ]);
        
        const planItems = plans.items || [];
        const resultItems = Array.isArray(results) ? results : (results as any).items || [];
        const resultPlanIds = new Set(resultItems.map((r: any) => r.inspection_plan_id));
        const connectedPlans = planItems.filter((p: any) => resultPlanIds.has(p.id));

        return {
          plansCount: planItems.length,
          resultsCount: resultItems.length,
          connectedCount: connectedPlans.length,
          disconnectedPlans: planItems.filter((p: any) => !resultPlanIds.has(p.id))
        };
      } catch (error) {
        // Connection status check failed silently
        return {
          plansCount: 0,
          resultsCount: 0,
          connectedCount: 0,
          disconnectedPlans: []
        };
      }
    },
    refetchInterval: POLLING.SLOW,
  });

  // Memoized date change handlers
  const handleDateFromChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setDateRange(prev => ({ ...prev, date_from: e.target.value }));
  }, []);

  const handleDateToChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setDateRange(prev => ({ ...prev, date_to: e.target.value }));
  }, []);

  // Memoized KPI cards calculation
  const kpiCards = useMemo(() => [
    {
      title: "총 검사건수",
      value: dashboardData?.total_inspections || 0,
      icon: FileText,
      color: "blue",
      change: null,
    },
    {
      title: "합격률",
      value: `${(dashboardData?.pass_rate || 0).toFixed(1)}%`,
      icon: CheckCircle,
      color: "green",
      change: dashboardData?.pass_rate ? (dashboardData.pass_rate > 95 ? "up" : "down") : null,
    },
    {
      title: "불량률",
      value: `${(dashboardData?.fail_rate || 0).toFixed(1)}%`,
      icon: XCircle,
      color: "red",
      change: dashboardData?.fail_rate ? (dashboardData.fail_rate < 5 ? "down" : "up") : null,
    },
    {
      title: "재작업률",
      value: dashboardData?.rework_rate != null && dashboardData.rework_rate > 0
        ? `${dashboardData.rework_rate.toFixed(1)}%`
        : "N/A",
      icon: AlertTriangle,
      color: "yellow",
      change: null,
    },
    {
      title: "미해결 NCR",
      value: dashboardData?.open_ncrs || 0,
      icon: Shield,
      color: "purple",
      change: null,
    },
  ], [dashboardData]);

  if (isLoading) {
    return <QualityDashboardLoader />;
  }

  return (
    <ErrorBoundary>
      <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">품질 대시보드</h1>
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
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-6">
        {kpiCards.map((card, index) => (
          <KPICard key={index} card={card} />
        ))}
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Quality Trend Chart */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">품질 트렌드</h2>
            <BarChart3 className="h-5 w-5 text-gray-400" />
          </div>
          <div className="h-80">
            {(dashboardData?.trend_data || []).length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={dashboardData?.trend_data || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="pass_rate"
                    stroke="#10B981"
                    strokeWidth={2}
                    name="합격률 (%)"
                  />
                  <Line
                    type="monotone"
                    dataKey="fail_rate"
                    stroke="#EF4444"
                    strokeWidth={2}
                    name="불량률 (%)"
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-gray-400">
                <div className="text-center">
                  <TrendingUp className="h-12 w-12 mx-auto mb-2 opacity-30" />
                  <p className="text-sm">데이터가 부족합니다.</p>
                  <p className="text-xs mt-1">검사결과를 등록하면 트렌드가 표시됩니다.</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Defect by Type */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">불량 유형별 분포</h2>
            <Shield className="h-5 w-5 text-gray-400" />
          </div>
          <div className="h-80">
            {(dashboardData?.defect_by_type || []).length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={dashboardData?.defect_by_type || []}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="count"
                  >
                    {(dashboardData?.defect_by_type || []).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-gray-400">
                <div className="text-center">
                  <Shield className="h-12 w-12 mx-auto mb-2 opacity-30" />
                  <p className="text-sm">데이터가 부족합니다.</p>
                  <p className="text-xs mt-1">검사결과를 등록하면 분포가 표시됩니다.</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Top Issues, Quick Actions, and Connection Status */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Top Quality Issues */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">주요 품질 이슈</h2>
          <div className="space-y-3">
            {(dashboardData?.top_issues || []).length > 0 ? (
              (dashboardData?.top_issues || []).slice(0, 5).map((issue, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium">{issue.product_name}</p>
                    <p className="text-sm text-gray-600">{issue.defect_count}건의 불량</p>
                  </div>
                  <div className="text-right">
                    <span className="px-2 py-1 bg-red-100 text-red-800 rounded-full text-xs font-medium">
                      주의 필요
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div className="flex items-center justify-center py-8 text-gray-400">
                <div className="text-center">
                  <AlertTriangle className="h-10 w-10 mx-auto mb-2 opacity-30" />
                  <p className="text-sm">보고된 품질 이슈가 없습니다.</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">바로가기</h2>
          <div className="grid grid-cols-2 gap-4">
            <Link
              href="/quality/inspection-plans"
              className="flex flex-col items-center p-4 bg-primary-50 hover:bg-primary-100 rounded-lg transition-colors"
            >
              <FileText className="h-8 w-8 text-primary-600 mb-2" />
              <span className="text-sm font-medium text-primary-900">검사계획</span>
            </Link>
            <Link
              href="/quality/inspection-results"
              className="flex flex-col items-center p-4 bg-green-50 hover:bg-green-100 rounded-lg transition-colors"
            >
              <CheckCircle className="h-8 w-8 text-green-600 mb-2" />
              <span className="text-sm font-medium text-green-900">측정결과</span>
            </Link>
            <Link
              href="/quality/spc"
              className="flex flex-col items-center p-4 bg-purple-50 hover:bg-purple-100 rounded-lg transition-colors"
            >
              <BarChart3 className="h-8 w-8 text-purple-600 mb-2" />
              <span className="text-sm font-medium text-purple-900">SPC 차트</span>
            </Link>
            <Link
              href="/quality/ncr"
              className="flex flex-col items-center p-4 bg-red-50 hover:bg-red-100 rounded-lg transition-colors"
            >
              <AlertTriangle className="h-8 w-8 text-red-600 mb-2" />
              <span className="text-sm font-medium text-red-900">부적합 관리</span>
            </Link>
          </div>
          
          {/* Analytics Integration */}
          <div className="mt-6 p-4 bg-gradient-to-r from-primary-50 to-purple-50 rounded-lg border border-primary-100">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">📊 분석 연동</h3>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-primary-600" />
                <span className="text-sm text-gray-600">품질 지표를 KPI 대시보드에서 확인</span>
              </div>
              <Link
                href={`/analytics?tab=quality&date_from=${dateRange.date_from}&date_to=${dateRange.date_to}`}
                className="px-3 py-1 bg-primary-600 text-white text-xs rounded-md hover:bg-primary-700 transition-colors"
              >
                상세 분석
              </Link>
            </div>
          </div>
        </div>

        {/* Quality Connection Status */}
        {connectionData && (
          <QualityConnectionCard
            plansCount={connectionData.plansCount}
            resultsCount={connectionData.resultsCount}
            connectedCount={connectionData.connectedCount}
          />
        )}
      </div>
    </div>
    </ErrorBoundary>
  );
}