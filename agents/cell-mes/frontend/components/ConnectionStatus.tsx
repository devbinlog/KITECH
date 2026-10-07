"use client";

import React from "react";
import { CheckCircle, AlertCircle, XCircle, Clock, Wifi, WifiOff } from "lucide-react";

export type ConnectionStatusType = "connected" | "disconnected" | "warning" | "pending";

interface ConnectionStatusProps {
  status: ConnectionStatusType;
  title: string;
  description?: string;
  count?: number;
  showIcon?: boolean;
  className?: string;
}

const statusConfig = {
  connected: {
    icon: CheckCircle,
    bgColor: "bg-green-100",
    textColor: "text-green-800",
    iconColor: "text-green-600",
    label: "연결됨"
  },
  disconnected: {
    icon: XCircle,
    bgColor: "bg-red-100", 
    textColor: "text-red-800",
    iconColor: "text-red-600",
    label: "연결 안됨"
  },
  warning: {
    icon: AlertCircle,
    bgColor: "bg-yellow-100",
    textColor: "text-yellow-800", 
    iconColor: "text-yellow-600",
    label: "주의"
  },
  pending: {
    icon: Clock,
    bgColor: "bg-primary-100",
    textColor: "text-primary-800",
    iconColor: "text-primary-600", 
    label: "대기 중"
  }
};

export const ConnectionBadge: React.FC<ConnectionStatusProps> = ({
  status,
  title,
  count,
  showIcon = true,
  className = ""
}) => {
  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${config.bgColor} ${config.textColor} ${className}`}>
      {showIcon && <Icon className={`h-3 w-3 mr-1 ${config.iconColor}`} />}
      <span>{title}</span>
      {count !== undefined && (
        <span className="ml-1 font-bold">{count}</span>
      )}
    </div>
  );
};

export const ServiceConnectionStatus: React.FC<{
  serviceName: string;
  isConnected: boolean;
  url?: string;
  lastChecked?: Date;
  className?: string;
}> = ({ serviceName, isConnected, url, lastChecked, className = "" }) => {
  const Icon = isConnected ? Wifi : WifiOff;
  
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <Icon className={`h-4 w-4 ${isConnected ? "text-green-600" : "text-red-600"}`} />
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">{serviceName}</span>
          <ConnectionBadge 
            status={isConnected ? "connected" : "disconnected"}
            title={isConnected ? "연결됨" : "연결 안됨"}
            showIcon={false}
          />
        </div>
        {url && (
          <div className="text-xs text-gray-500">{url}</div>
        )}
        {lastChecked && (
          <div className="text-xs text-gray-400">
            마지막 확인: {lastChecked.toLocaleTimeString()}
          </div>
        )}
      </div>
    </div>
  );
};

export const QualityConnectionCard: React.FC<{
  plansCount: number;
  resultsCount: number;
  connectedCount: number;
  className?: string;
}> = ({ plansCount, resultsCount, connectedCount, className = "" }) => {
  const connectionRate = plansCount > 0 ? (connectedCount / plansCount) * 100 : 0;
  
  const getConnectionStatus = (): ConnectionStatusType => {
    if (connectionRate >= 90) return "connected";
    if (connectionRate >= 70) return "warning";
    return "disconnected";
  };

  return (
    <div className={`card ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">검사계획 ↔ 측정결과 연결</h3>
        <ConnectionBadge
          status={getConnectionStatus()}
          title={`${connectionRate.toFixed(0)}%`}
        />
      </div>
      
      <div className="space-y-3">
        <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
          <span className="text-sm text-gray-600">총 검사계획</span>
          <span className="font-medium">{plansCount}개</span>
        </div>
        
        <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
          <span className="text-sm text-gray-600">측정결과 있음</span>
          <div className="flex items-center gap-2">
            <span className="font-medium">{connectedCount}개</span>
            <ConnectionBadge
              status={connectedCount > 0 ? "connected" : "warning"}
              title=""
              showIcon={true}
            />
          </div>
        </div>
        
        <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
          <span className="text-sm text-gray-600">측정결과 없음</span>
          <div className="flex items-center gap-2">
            <span className="font-medium">{plansCount - connectedCount}개</span>
            {(plansCount - connectedCount) > 0 && (
              <ConnectionBadge
                status="warning"
                title="대기"
                showIcon={true}
              />
            )}
          </div>
        </div>
      </div>
      
      {connectionRate < 70 && (
        <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-yellow-600" />
            <span className="text-sm text-yellow-800 font-medium">
              연결률이 낮습니다 ({connectionRate.toFixed(0)}%)
            </span>
          </div>
          <p className="text-xs text-yellow-700 mt-1">
            검사계획에 대응하는 측정결과를 추가해주세요.
          </p>
        </div>
      )}
    </div>
  );
};

export default ConnectionBadge;