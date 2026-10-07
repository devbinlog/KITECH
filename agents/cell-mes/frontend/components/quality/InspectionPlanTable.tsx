"use client";

import { InspectionPlan } from "@/types";
import { Edit, Trash2, Eye } from "lucide-react";

interface InspectionPlanTableProps {
  plans: InspectionPlan[];
  onView?: (plan: InspectionPlan) => void;
  onEdit?: (plan: InspectionPlan) => void;
  onDelete?: (plan: InspectionPlan) => void;
  isLoading?: boolean;
}

const inspectionTypeLabels = {
  INCOMING: "입고검사",
  IN_PROCESS: "공정검사",
  FINAL: "최종검사",
};

const inspectionTypeColors = {
  INCOMING: "bg-primary-100 text-primary-800",
  IN_PROCESS: "bg-yellow-100 text-yellow-800",
  FINAL: "bg-green-100 text-green-800",
};

export function InspectionPlanTable({ 
  plans, 
  onView, 
  onEdit, 
  onDelete, 
  isLoading 
}: InspectionPlanTableProps) {
  if (isLoading) {
    return (
      <div className="card">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-12 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (plans.length === 0) {
    return (
      <div className="card">
        <div className="text-center py-8 text-gray-500">
          <div className="text-gray-400 mb-2">📋</div>
          <p>검사계획이 없습니다.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="table">
          <thead>
            <tr>
              <th className="text-left">제품</th>
              <th className="text-left">검사유형</th>
              <th className="text-left">검사항목</th>
              <th className="text-left">상태</th>
              <th className="text-left">생성일</th>
              <th className="text-right">액션</th>
            </tr>
          </thead>
          <tbody>
            {plans.map((plan) => (
              <tr key={plan.id} className="hover:bg-gray-50">
                <td>
                  {plan.product ? (
                    <div>
                      <div className="font-medium text-gray-900">
                        {plan.product.name}
                      </div>
                      <div className="text-sm text-gray-500">
                        {plan.product.code}
                      </div>
                    </div>
                  ) : (
                    <span className="text-gray-400 text-sm">
                      제품 정보 없음
                    </span>
                  )}
                </td>
                <td>
                  <span 
                    className={`px-2 py-1 rounded-full text-xs font-medium ${
                      inspectionTypeColors[plan.inspection_type]
                    }`}
                  >
                    {inspectionTypeLabels[plan.inspection_type]}
                  </span>
                </td>
                <td>
                  <div className="flex items-center gap-2">
                    <span className="font-medium">
                      {plan.inspection_items?.length || 0}개
                    </span>
                    {plan.inspection_items && plan.inspection_items.length > 0 && (
                      <div className="text-xs text-gray-500">
                        {plan.inspection_items.slice(0, 2).map(item => item.item_name).join(', ')}
                        {plan.inspection_items.length > 2 && ' 외'}
                      </div>
                    )}
                  </div>
                </td>
                <td>
                  <span 
                    className={`px-2 py-1 rounded-full text-xs font-medium ${
                      plan.is_active 
                        ? "bg-green-100 text-green-800" 
                        : "bg-gray-100 text-gray-800"
                    }`}
                  >
                    {plan.is_active ? "활성" : "비활성"}
                  </span>
                </td>
                <td className="text-sm text-gray-500">
                  {new Date(plan.created_at).toLocaleDateString('ko-KR')}
                </td>
                <td>
                  <div className="flex items-center justify-end gap-1">
                    {onView && (
                      <button
                        onClick={() => onView(plan)}
                        className="p-1 text-primary-600 hover:bg-primary-50 rounded transition-colors"
                        title="상세보기"
                      >
                        <Eye size={18} />
                      </button>
                    )}
                    {onEdit && (
                      <button
                        onClick={() => onEdit(plan)}
                        className="p-1 text-gray-600 hover:bg-gray-50 rounded transition-colors"
                        title="수정"
                      >
                        <Edit size={18} />
                      </button>
                    )}
                    {onDelete && (
                      <button
                        onClick={() => onDelete(plan)}
                        className="p-1 text-red-600 hover:bg-red-50 rounded transition-colors"
                        title="삭제"
                      >
                        <Trash2 size={18} />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {plans.length > 0 && (
        <div className="px-4 py-3 border-t border-gray-200 bg-gray-50 text-sm text-gray-700">
          총 {plans.length}개의 검사계획
        </div>
      )}
    </div>
  );
}