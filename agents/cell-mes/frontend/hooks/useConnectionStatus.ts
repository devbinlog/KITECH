/**
 * 외부 서비스 연결 상태를 확인하는 훅
 * MES UX Patterns 스킬을 따름
 */

import { useQuery } from "@tanstack/react-query";
import { productService } from "@/services/master";
import { routingService } from "@/services/master";
import { useMemo } from "react";
import { POLLING, STALE_TIME } from "@/config/constants";

export interface ConnectionStatus {
  status: "connected" | "disconnected" | "checking";
  url?: string;
  lastCheck?: string;
}

export interface ProductConnection {
  productId: number;
  hasRouting: boolean;
  routingCount: number;
  canCreateOrder: boolean;
}

/**
 * 제품별 연결 상태 확인
 */
export function useProductConnections(productIds?: number[]) {
  const { data: routingCounts, isLoading } = useQuery({
    queryKey: ["product-routing-counts", productIds],
    queryFn: async () => {
      if (!productIds?.length) return {};
      
      const results: Record<number, number> = {};
      for (const productId of productIds) {
        try {
          const routings = await routingService.getByProduct(productId);
          results[productId] = routings.length;
        } catch {
          results[productId] = 0;
        }
      }
      return results;
    },
    enabled: !!productIds?.length,
    staleTime: STALE_TIME.MEDIUM,
  });

  const connections = useMemo<ProductConnection[]>(() => {
    if (!productIds?.length || !routingCounts) return [];
    
    return productIds.map((productId) => {
      const routingCount = routingCounts[productId] || 0;
      return {
        productId,
        hasRouting: routingCount > 0,
        routingCount,
        canCreateOrder: routingCount > 0,
      };
    });
  }, [productIds, routingCounts]);

  return {
    connections,
    isLoading,
  };
}

/**
 * 단일 제품 연결 상태
 */
export function useProductConnection(productId?: number) {
  const { connections, isLoading } = useProductConnections(
    productId ? [productId] : undefined
  );

  return {
    connection: connections[0],
    isLoading,
  };
}

/**
 * 서비스별 헬스 체크
 */
export function useServiceHealth() {
  const { data: health, isError } = useQuery({
    queryKey: ["service-health"],
    queryFn: async () => {
      try {
        // 여러 서비스의 헬스체크를 병렬로 실행
        const schedulerUrl = process.env.NEXT_PUBLIC_SCHEDULER_URL || "http://localhost:8002";
        const [mesHealth, schedulerHealth] = await Promise.allSettled([
          fetch("/health").then(r => r.json()),
          fetch(`${schedulerUrl}/health`).then(r => r.json()),
        ]);

        return {
          mes: {
            status: mesHealth.status === "fulfilled" ? "connected" : "disconnected",
            url: "/health",
            lastCheck: new Date().toISOString(),
          } as ConnectionStatus,
          scheduler: {
            status: schedulerHealth.status === "fulfilled" ? "connected" : "disconnected",
            url: `${schedulerUrl}/health`,
            lastCheck: new Date().toISOString(),
          } as ConnectionStatus,
        };
      } catch {
        return {
          mes: { status: "disconnected" as const },
          scheduler: { status: "disconnected" as const },
        };
      }
    },
    refetchInterval: POLLING.NORMAL,
    retry: false,
  });

  return {
    health: health || { 
      mes: { status: "checking" as const },
      scheduler: { status: "checking" as const }
    },
    isError,
  };
}