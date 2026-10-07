"use client";

import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { productService } from "@/services/master";
import { InspectionPlan, Product, InspectionItemFormData } from "@/types";
import { Plus, Trash2, X } from "lucide-react";

interface InspectionPlanFormProps {
  initialData?: Partial<InspectionPlan>;
  onSubmit: (data: {
    product_id: number;
    process_routing_id?: number;
    inspection_type: "INCOMING" | "IN_PROCESS" | "FINAL";
    inspection_items: InspectionItemFormData[];
  }) => void;
  onCancel: () => void;
  isLoading?: boolean;
  title?: string;
}

const inspectionTypeOptions = [
  { value: "INCOMING", label: "입고검사" },
  { value: "IN_PROCESS", label: "공정검사" },
  { value: "FINAL", label: "최종검사" },
];

export function InspectionPlanForm({
  initialData,
  onSubmit,
  onCancel,
  isLoading = false,
  title = "검사계획"
}: InspectionPlanFormProps) {
  const [formData, setFormData] = useState({
    product_id: initialData?.product_id || 0,
    process_routing_id: initialData?.process_routing_id || undefined,
    inspection_type: (initialData?.inspection_type || "IN_PROCESS") as "INCOMING" | "IN_PROCESS" | "FINAL",
    inspection_items: initialData?.inspection_items || [
      {
        item_name: "",
        specification: "",
        usl: null,
        lsl: null,
        target: null,
        measurement_method: "",
        sort_order: 1,
      }
    ] as InspectionItemFormData[],
  });

  const { data: products } = useQuery({
    queryKey: ["products-for-form"],
    queryFn: () => productService.getAll(),
  });

  const addInspectionItem = () => {
    setFormData({
      ...formData,
      inspection_items: [
        ...formData.inspection_items,
        {
          item_name: "",
          specification: "",
          usl: null,
          lsl: null,
          target: null,
          measurement_method: "",
          sort_order: formData.inspection_items.length + 1,
        }
      ],
    });
  };

  const removeInspectionItem = (index: number) => {
    if (formData.inspection_items.length > 1) {
      const items = formData.inspection_items.filter((_, i) => i !== index);
      setFormData({
        ...formData,
        inspection_items: items.map((item, i) => ({ ...item, sort_order: i + 1 })),
      });
    }
  };

  const updateInspectionItem = (index: number, field: keyof InspectionItemFormData, value: any) => {
    const items = formData.inspection_items.map((item, i) =>
      i === index ? { ...item, [field]: value } : item
    );
    setFormData({ ...formData, inspection_items: items });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation
    if (!formData.product_id) {
      alert("제품을 선택해주세요.");
      return;
    }

    const hasEmptyItems = formData.inspection_items.some(
      item => !item.item_name || !item.specification || !item.measurement_method
    );
    
    if (hasEmptyItems) {
      alert("모든 검사항목의 필수 정보를 입력해주세요.");
      return;
    }

    onSubmit(formData);
  };

  // Auto-calculate target value when USL and LSL are both set
  const handleSpecLimitChange = (index: number, field: "usl" | "lsl", value: number | null) => {
    updateInspectionItem(index, field, value);
    
    const item = formData.inspection_items[index];
    const newUsl = field === "usl" ? value : item.usl;
    const newLsl = field === "lsl" ? value : item.lsl;
    
    if (newUsl !== null && newLsl !== null && !item.target) {
      const calculatedTarget = (newUsl + newLsl) / 2;
      updateInspectionItem(index, "target", calculatedTarget);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Information */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">{title} 기본 정보</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                제품 선택 *
              </label>
              <select
                value={formData.product_id}
                onChange={(e) => setFormData({ ...formData, product_id: parseInt(e.target.value) || 0 })}
                className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                required
              >
                <option value={0}>제품을 선택하세요...</option>
                {products?.map((product) => (
                  <option key={product.id} value={product.id}>
                    {product.code} - {product.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                검사유형 *
              </label>
              <select
                value={formData.inspection_type}
                onChange={(e) => setFormData({ ...formData, inspection_type: e.target.value as any })}
                className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                required
              >
                {inspectionTypeOptions.map((option) => (
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
              className="btn btn-secondary flex items-center gap-2"
            >
              <Plus size={16} />
              항목 추가
            </button>
          </div>

          <div className="space-y-4">
            {formData.inspection_items.map((item, index) => (
              <div key={index} className="p-4 border rounded-lg bg-gray-50">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium text-gray-800">검사항목 #{index + 1}</h4>
                  {formData.inspection_items.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeInspectionItem(index)}
                      className="p-1 text-red-600 hover:bg-red-50 rounded"
                      title="항목 삭제"
                    >
                      <Trash2 size={16} />
                    </button>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      항목명 *
                    </label>
                    <input
                      type="text"
                      value={item.item_name}
                      onChange={(e) => updateInspectionItem(index, "item_name", e.target.value)}
                      className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                      placeholder="예: 외경 치수"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      규격 *
                    </label>
                    <input
                      type="text"
                      value={item.specification}
                      onChange={(e) => updateInspectionItem(index, "specification", e.target.value)}
                      className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                      placeholder="예: 50.0 ± 0.1 mm"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      측정방법 *
                    </label>
                    <input
                      type="text"
                      value={item.measurement_method}
                      onChange={(e) => updateInspectionItem(index, "measurement_method", e.target.value)}
                      className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                      placeholder="예: 마이크로미터"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      상한값 (USL)
                    </label>
                    <input
                      type="number"
                      step="0.001"
                      value={item.usl || ""}
                      onChange={(e) => handleSpecLimitChange(index, "usl", e.target.value ? parseFloat(e.target.value) : null)}
                      className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                      placeholder="50.1"
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
                      onChange={(e) => handleSpecLimitChange(index, "lsl", e.target.value ? parseFloat(e.target.value) : null)}
                      className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                      placeholder="49.9"
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
                      onChange={(e) => updateInspectionItem(index, "target", e.target.value ? parseFloat(e.target.value) : null)}
                      className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                      placeholder="50.0"
                    />
                  </div>
                </div>

                {/* Specification Summary */}
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
            ))}
          </div>

          {/* Quick Add Templates */}
          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <h4 className="text-sm font-medium text-gray-700 mb-2">빠른 템플릿</h4>
            <div className="flex gap-2 flex-wrap">
              <button
                type="button"
                onClick={() => addInspectionItem()}
                className="px-3 py-1 text-xs bg-white border rounded hover:bg-gray-50"
              >
                치수 항목 추가
              </button>
              <button
                type="button"
                onClick={() => {
                  const newItem: InspectionItemFormData = {
                    item_name: "표면 거칠기",
                    specification: "Ra 1.6μm 이하",
                    usl: 1.6,
                    lsl: null,
                    target: 0.8,
                    measurement_method: "표면거칠기측정기",
                    sort_order: formData.inspection_items.length + 1,
                  };
                  setFormData({
                    ...formData,
                    inspection_items: [...formData.inspection_items, newItem],
                  });
                }}
                className="px-3 py-1 text-xs bg-white border rounded hover:bg-gray-50"
              >
                표면거칠기 추가
              </button>
              <button
                type="button"
                onClick={() => {
                  const newItem: InspectionItemFormData = {
                    item_name: "평행도",
                    specification: "0.02mm 이내",
                    usl: 0.02,
                    lsl: -0.02,
                    target: 0,
                    measurement_method: "3차원측정기",
                    sort_order: formData.inspection_items.length + 1,
                  };
                  setFormData({
                    ...formData,
                    inspection_items: [...formData.inspection_items, newItem],
                  });
                }}
                className="px-3 py-1 text-xs bg-white border rounded hover:bg-gray-50"
              >
                기하공차 추가
              </button>
            </div>
          </div>
        </div>

        {/* Form Actions */}
        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500"
          >
            취소
          </button>
          <button
            type="submit"
            disabled={isLoading}
            className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? "저장 중..." : "저장"}
          </button>
        </div>
      </form>
    </div>
  );
}