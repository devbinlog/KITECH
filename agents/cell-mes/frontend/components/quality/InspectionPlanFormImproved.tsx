/**
 * 개선된 InspectionPlanForm 컴포넌트
 * React Best Practices와 MES UX Patterns 스킬을 적용
 */

"use client";

import { useState, useEffect, useCallback, useMemo, memo } from "react";
import { useQuery } from "@tanstack/react-query";
import { productService } from "@/services/master";
import { InspectionPlan, Product, InspectionItemFormData } from "@/types";
import { Plus, Trash2, X } from "lucide-react";
import { useProductConnections } from "@/hooks/useConnectionStatus";
import { RoutingStatus } from "@/components/ui/ConnectionBadge";
import { getQualityErrorMessage, getConfirmMessage } from "@/utils/errorMessages";

interface InspectionPlanFormProps {
  initialData?: Partial<InspectionPlan>;
  onSubmit: (data: {
    product_id: number;
    process_routing_id?: number | null;
    inspection_type: "INCOMING" | "IN_PROCESS" | "FINAL";
    inspection_items: InspectionItemFormData[];
  }) => void;
  onCancel: () => void;
  isLoading?: boolean;
  title?: string;
}

interface InspectionPlanFormData {
  product_id: number | undefined;
  process_routing_id?: number | null;
  inspection_type: "INCOMING" | "IN_PROCESS" | "FINAL";
  inspection_items: InspectionItemFormData[];
}

// Memoized constants
const INSPECTION_TYPE_OPTIONS = [
  { value: "INCOMING", label: "입고검사" },
  { value: "IN_PROCESS", label: "공정검사" },
  { value: "FINAL", label: "최종검사" },
] as const;

const DEFAULT_INSPECTION_ITEM: InspectionItemFormData = {
  item_name: "",
  specification: "",
  usl: null,
  lsl: null,
  target: null,
  measurement_method: "",
  sort_order: 1,
};

/**
 * 개별 검사 항목 컴포넌트 - 메모화로 최적화
 */
const InspectionItemComponent = memo(function InspectionItemComponent({
  item,
  index,
  onUpdate,
  onRemove,
  canRemove,
}: {
  item: InspectionItemFormData;
  index: number;
  onUpdate: (index: number, field: keyof InspectionItemFormData, value: any) => void;
  onRemove: (index: number) => void;
  canRemove: boolean;
}) {
  // 최적화: 스펙 한계값 변경 시 목표값 자동 계산
  const handleSpecLimitChange = useCallback((field: "usl" | "lsl", value: number | null) => {
    onUpdate(index, field, value);
    
    // 목표값이 없고 양쪽 한계값이 모두 있으면 자동 계산
    const newUsl = field === "usl" ? value : item.usl;
    const newLsl = field === "lsl" ? value : item.lsl;
    
    if (newUsl !== null && newLsl !== null && !item.target) {
      const calculatedTarget = (newUsl + newLsl) / 2;
      onUpdate(index, "target", calculatedTarget);
    }
  }, [index, item.usl, item.lsl, item.target, onUpdate]);

  return (
    <div className="p-4 border rounded-lg bg-gray-50">
      <div className="flex items-center justify-between mb-4">
        <h4 className="font-medium">검사 항목 {index + 1}</h4>
        {canRemove && (
          <button
            type="button"
            onClick={() => {
              if (confirm(getConfirmMessage("삭제", `검사 항목 ${index + 1}`))) {
                onRemove(index);
              }
            }}
            className="p-1 text-red-500 hover:bg-red-50 rounded"
            title="검사 항목 삭제"
          >
            <Trash2 size={16} />
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* 기본 정보 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            검사 항목명 *
          </label>
          <input
            type="text"
            value={item.item_name}
            onChange={(e) => onUpdate(index, "item_name", e.target.value)}
            className="w-full px-3 py-2 border rounded-md"
            placeholder="예: 치수, 표면거칠기"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            규격
          </label>
          <input
            type="text"
            value={item.specification}
            onChange={(e) => onUpdate(index, "specification", e.target.value)}
            className="w-full px-3 py-2 border rounded-md"
            placeholder="예: 100±0.1mm"
          />
        </div>

        {/* 측정 방법 */}
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            측정 방법
          </label>
          <input
            type="text"
            value={item.measurement_method}
            onChange={(e) => onUpdate(index, "measurement_method", e.target.value)}
            className="w-full px-3 py-2 border rounded-md"
            placeholder="예: 버니어 캘리퍼스, 3차원측정기"
          />
        </div>

        {/* 관리 한계 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            상한값 (USL)
          </label>
          <input
            type="number"
            step="0.001"
            value={item.usl || ""}
            onChange={(e) => handleSpecLimitChange("usl", e.target.value ? parseFloat(e.target.value) : null)}
            className="w-full px-3 py-2 border rounded-md"
            placeholder="상한 규격값"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            하한값 (LSL)
          </label>
          <input
            type="number"
            step="0.001"
            value={item.lsl || ""}
            onChange={(e) => handleSpecLimitChange("lsl", e.target.value ? parseFloat(e.target.value) : null)}
            className="w-full px-3 py-2 border rounded-md"
            placeholder="하한 규격값"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            목표값
            {item.usl !== null && item.lsl !== null && (
              <span className="text-xs text-gray-500 ml-1">(자동계산됨)</span>
            )}
          </label>
          <input
            type="number"
            step="0.001"
            value={item.target || ""}
            onChange={(e) => onUpdate(index, "target", e.target.value ? parseFloat(e.target.value) : null)}
            className="w-full px-3 py-2 border rounded-md"
            placeholder="목표값"
          />
        </div>
      </div>

      {/* 규격 요약 */}
      {(item.usl !== null || item.lsl !== null || item.target !== null) && (
        <div className="mt-3 p-3 bg-primary-50 rounded-md">
          <p className="text-sm text-primary-800">
            <span className="font-medium">규격 요약:</span>
            {item.lsl !== null && ` LSL: ${item.lsl}`}
            {item.target !== null && ` 목표: ${item.target}`}
            {item.usl !== null && ` USL: ${item.usl}`}
            {item.usl !== null && item.lsl !== null && (
              ` (공차: ±${((item.usl - item.lsl) / 2).toFixed(3)})`
            )}
          </p>
        </div>
      )}
    </div>
  );
});

export const InspectionPlanFormImproved = memo(function InspectionPlanFormImproved({
  initialData,
  onSubmit,
  onCancel,
  isLoading = false,
  title = "검사계획"
}: InspectionPlanFormProps) {
  // State management with improved initial values
  const [formData, setFormData] = useState<InspectionPlanFormData>(() => ({
    product_id: initialData?.product_id,  // undefined instead of 0
    process_routing_id: initialData?.process_routing_id,
    inspection_type: (initialData?.inspection_type || "IN_PROCESS") as "INCOMING" | "IN_PROCESS" | "FINAL",
    inspection_items: initialData?.inspection_items || [{ ...DEFAULT_INSPECTION_ITEM }],
  }));

  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Data fetching with React Query
  const { data: products, isLoading: productsLoading } = useQuery({
    queryKey: ["products-for-form"],
    queryFn: () => productService.getAll(),
  });

  // Connection status for products
  const productIds = useMemo(() => products?.map(p => p.id) || [], [products]);
  const { connections, isLoading: connectionsLoading } = useProductConnections(productIds);

  // Find connection for selected product
  const selectedProductConnection = useMemo(() => {
    if (!formData.product_id) return null;
    return connections.find(conn => conn.productId === formData.product_id);
  }, [formData.product_id, connections]);

  // Optimized handlers with useCallback
  const updateFormData = useCallback((updates: Partial<InspectionPlanFormData>) => {
    setFormData(prev => ({ ...prev, ...updates }));
    setHasUnsavedChanges(true);
  }, []);

  const handleProductChange = useCallback((productId: number | undefined) => {
    if (hasUnsavedChanges) {
      if (!confirm(getConfirmMessage("제품 변경", "저장되지 않은 변경사항이 있습니다"))) {
        return;
      }
    }
    
    updateFormData({ product_id: productId });
    setHasUnsavedChanges(false);
  }, [hasUnsavedChanges, updateFormData]);

  const addInspectionItem = useCallback(() => {
    updateFormData({
      inspection_items: [
        ...formData.inspection_items,
        {
          ...DEFAULT_INSPECTION_ITEM,
          sort_order: formData.inspection_items.length + 1,
        }
      ],
    });
  }, [formData.inspection_items, updateFormData]);

  const removeInspectionItem = useCallback((index: number) => {
    if (formData.inspection_items.length <= 1) return;
    
    const items = formData.inspection_items.filter((_, i) => i !== index);
    updateFormData({
      inspection_items: items.map((item, i) => ({ ...item, sort_order: i + 1 })),
    });
  }, [formData.inspection_items, updateFormData]);

  const updateInspectionItem = useCallback((index: number, field: keyof InspectionItemFormData, value: any) => {
    const items = formData.inspection_items.map((item, i) =>
      i === index ? { ...item, [field]: value } : item
    );
    updateFormData({ inspection_items: items });
  }, [formData.inspection_items, updateFormData]);

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.product_id) {
      alert("제품을 선택해주세요.");
      return;
    }

    if (!selectedProductConnection?.hasRouting) {
      alert("선택한 제품에 라우팅이 설정되지 않았습니다. 먼저 라우팅을 설정해주세요.");
      return;
    }

    onSubmit({
      product_id: formData.product_id,
      process_routing_id: formData.process_routing_id,
      inspection_type: formData.inspection_type,
      inspection_items: formData.inspection_items,
    });
  }, [formData, selectedProductConnection, onSubmit]);

  // Warning on page leave
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasUnsavedChanges) {
        e.preventDefault();
        e.returnValue = "";
      }
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [hasUnsavedChanges]);

  return (
    <div className="max-w-4xl mx-auto">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Header with unsaved changes indicator */}
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            {title} 기본 정보
            {hasUnsavedChanges && (
              <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded-full">
                변경사항 있음
              </span>
            )}
          </h3>
        </div>

        {/* Basic Information */}
        <div className="card">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                제품 선택 *
              </label>
              <select
                value={formData.product_id || ""}
                onChange={(e) => handleProductChange(parseInt(e.target.value) || undefined)}
                className="w-full px-3 py-2 border rounded-md"
                required
              >
                <option value="">제품을 선택하세요...</option>
                {products?.map((product) => (
                  <option key={product.id} value={product.id}>
                    {product.code} - {product.name}
                  </option>
                ))}
              </select>
              
              {/* Connection status for selected product */}
              {formData.product_id && selectedProductConnection && !connectionsLoading && (
                <div className="mt-2">
                  <RoutingStatus 
                    routingCount={selectedProductConnection.routingCount} 
                    showDetails 
                  />
                </div>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                검사 유형 *
              </label>
              <select
                value={formData.inspection_type}
                onChange={(e) => updateFormData({ 
                  inspection_type: e.target.value as "INCOMING" | "IN_PROCESS" | "FINAL" 
                })}
                className="w-full px-3 py-2 border rounded-md"
                required
              >
                {INSPECTION_TYPE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Inspection Items */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">검사 항목</h3>
            <button
              type="button"
              onClick={addInspectionItem}
              className="btn btn-secondary flex items-center gap-1"
            >
              <Plus size={16} />
              항목 추가
            </button>
          </div>

          <div className="space-y-4">
            {formData.inspection_items.map((item, index) => (
              <InspectionItemComponent
                key={index}
                item={item}
                index={index}
                onUpdate={updateInspectionItem}
                onRemove={removeInspectionItem}
                canRemove={formData.inspection_items.length > 1}
              />
            ))}
          </div>
        </div>

        {/* Form Actions */}
        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={() => {
              if (hasUnsavedChanges && !confirm(getConfirmMessage("취소", "저장되지 않은 변경사항이 있습니다"))) {
                return;
              }
              onCancel();
            }}
            className="btn btn-secondary"
            disabled={isLoading}
          >
            취소
          </button>
          <button
            type="submit"
            disabled={isLoading || !formData.product_id || !selectedProductConnection?.hasRouting}
            className="btn btn-primary"
            title={
              !formData.product_id 
                ? "제품을 선택해주세요" 
                : !selectedProductConnection?.hasRouting 
                  ? "선택한 제품에 라우팅이 필요합니다" 
                  : ""
            }
          >
            {isLoading ? "저장 중..." : "저장"}
          </button>
        </div>
      </form>
    </div>
  );
});

export default InspectionPlanFormImproved;