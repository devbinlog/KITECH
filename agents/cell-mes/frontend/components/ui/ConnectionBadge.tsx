/**
 * 연결 상태 표시 배지 컴포넌트
 * MES UX Patterns 스킬을 따름
 */

import { CheckCircle, AlertTriangle, Wifi, WifiOff, RefreshCw } from "lucide-react";
import { memo } from "react";

interface ConnectionBadgeProps {
  hasRouting: boolean;
  routingCount: number;
  className?: string;
}

export const ConnectionBadge = memo(function ConnectionBadge({ 
  hasRouting, 
  routingCount, 
  className = "" 
}: ConnectionBadgeProps) {
  if (hasRouting) {
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800 ${className}`}>
        <CheckCircle size={12} />
        {routingCount}개 공정
      </span>
    );
  }

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800 ${className}`}>
      <AlertTriangle size={12} />
      라우팅 없음
    </span>
  );
});

interface ServiceBadgeProps {
  status: "connected" | "disconnected" | "checking";
  serviceName: string;
  url?: string;
  className?: string;
}

export const ServiceBadge = memo(function ServiceBadge({ 
  status, 
  serviceName, 
  url, 
  className = "" 
}: ServiceBadgeProps) {
  const statusConfig = {
    connected: {
      icon: Wifi,
      text: "연결됨",
      bgColor: "bg-green-100",
      textColor: "text-green-700",
    },
    disconnected: {
      icon: WifiOff,
      text: "연결 안됨",
      bgColor: "bg-red-100", 
      textColor: "text-red-700",
    },
    checking: {
      icon: RefreshCw,
      text: "확인 중",
      bgColor: "bg-gray-100",
      textColor: "text-gray-700",
    },
  };

  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <div className={`inline-flex items-center gap-2 ${className}`}>
      <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full ${config.bgColor} ${config.textColor}`}>
        <Icon size={12} className={status === "checking" ? "animate-spin" : ""} />
        {config.text}
      </span>
      {url && (
        <span className="text-xs text-gray-500">{serviceName}</span>
      )}
    </div>
  );
});

interface RoutingStatusProps {
  productId?: number;
  routingCount: number;
  showDetails?: boolean;
  className?: string;
}

export const RoutingStatus = memo(function RoutingStatus({ 
  productId, 
  routingCount, 
  showDetails = false,
  className = "" 
}: RoutingStatusProps) {
  const hasRouting = routingCount > 0;

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <ConnectionBadge hasRouting={hasRouting} routingCount={routingCount} />
      
      {showDetails && !hasRouting && (
        <span className="text-xs text-gray-500">
          작업지시 생성 불가
        </span>
      )}

      {showDetails && hasRouting && (
        <span className="text-xs text-gray-500">
          작업지시 생성 가능
        </span>
      )}
    </div>
  );
});

/**
 * 제품 카드에서 사용할 종합 상태 배지
 */
interface ProductStatusBadgeProps {
  productCode: string;
  routingCount: number;
  hasActiveOrders?: boolean;
  className?: string;
}

export const ProductStatusBadge = memo(function ProductStatusBadge({ 
  productCode, 
  routingCount, 
  hasActiveOrders = false,
  className = "" 
}: ProductStatusBadgeProps) {
  return (
    <div className={`space-y-1 ${className}`}>
      <RoutingStatus routingCount={routingCount} showDetails />
      
      {hasActiveOrders && (
        <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full bg-primary-100 text-primary-800">
          <RefreshCw size={12} />
          생산 중
        </span>
      )}
    </div>
  );
});