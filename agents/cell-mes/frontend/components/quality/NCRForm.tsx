"use client";

import { useState } from "react";
import { X } from "lucide-react";

interface NCRFormData {
  ncr_no: string;
  work_order_id?: number;
  inspection_result_id?: number;
  defect_type: "DIMENSION" | "SURFACE" | "MATERIAL" | "PROCESS" | "OTHER";
  defect_description: string;
  severity: "CRITICAL" | "MAJOR" | "MINOR";
  root_cause: string;
  corrective_action: string;
  preventive_action: string;
  created_by: string;
  assigned_to: string;
}

interface NCRFormProps {
  initialData?: Partial<NCRFormData>;
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: NCRFormData) => void;
  isLoading?: boolean;
  workOrders?: Array<{ id: number; lot_no: string; product?: { name: string } }>;
  inspectionResults?: Array<{ id: number; lot_no: string }>;
}

const defectTypeLabels = {
  DIMENSION: "치수불량",
  SURFACE: "표면불량",
  MATERIAL: "재료불량",
  PROCESS: "공정불량",
  OTHER: "기타",
};

const severityLabels = {
  CRITICAL: "심각",
  MAJOR: "주요",
  MINOR: "경미",
};

const severityDescriptions = {
  CRITICAL: "제품 기능에 심각한 영향을 미치는 불량",
  MAJOR: "제품 기능에 주요한 영향을 미치는 불량",
  MINOR: "제품 기능에 경미한 영향을 미치는 불량",
};

export function NCRForm({
  initialData,
  isOpen,
  onClose,
  onSubmit,
  isLoading,
  workOrders = [],
  inspectionResults = []
}: NCRFormProps) {
  const [formData, setFormData] = useState<NCRFormData>({
    ncr_no: "",
    work_order_id: undefined,
    inspection_result_id: undefined,
    defect_type: "OTHER",
    defect_description: "",
    severity: "MINOR",
    root_cause: "",
    corrective_action: "",
    preventive_action: "",
    created_by: "",
    assigned_to: "",
    ...initialData,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  const handleChange = (field: keyof NCRFormData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const generateNCRNo = () => {
    const now = new Date();
    const year = now.getFullYear();
    const month = (now.getMonth() + 1).toString().padStart(2, '0');
    const day = now.getDate().toString().padStart(2, '0');
    const random = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
    return `NCR-${year}${month}${day}-${random}`;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold">부적합 보고서 (NCR)</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded transition-colors"
            type="button"
          >
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Basic Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                NCR No *
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={formData.ncr_no}
                  onChange={(e) => handleChange("ncr_no", e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="NCR-YYYYMMDD-XXX"
                  required
                />
                <button
                  type="button"
                  onClick={() => handleChange("ncr_no", generateNCRNo())}
                  className="px-3 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors text-sm"
                >
                  자동생성
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                작업지시 선택
              </label>
              <select
                value={formData.work_order_id || ""}
                onChange={(e) => handleChange("work_order_id", e.target.value ? parseInt(e.target.value) : undefined)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="">선택 안함</option>
                {workOrders.map((order) => (
                  <option key={order.id} value={order.id}>
                    {order.lot_no} - {order.product?.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                불량유형 *
              </label>
              <select
                value={formData.defect_type}
                onChange={(e) => handleChange("defect_type", e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                required
              >
                {Object.entries(defectTypeLabels).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                심각도 *
              </label>
              <select
                value={formData.severity}
                onChange={(e) => handleChange("severity", e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                required
              >
                {Object.entries(severityLabels).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-500 mt-1">
                {severityDescriptions[formData.severity as keyof typeof severityDescriptions]}
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                생성자 *
              </label>
              <input
                type="text"
                value={formData.created_by}
                onChange={(e) => handleChange("created_by", e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="생성자 이름"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                담당자 지정
              </label>
              <input
                type="text"
                value={formData.assigned_to}
                onChange={(e) => handleChange("assigned_to", e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="담당자 이름"
              />
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              불량 내용 *
            </label>
            <textarea
              value={formData.defect_description}
              onChange={(e) => handleChange("defect_description", e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              rows={4}
              placeholder="불량 상황에 대한 상세 설명을 입력하세요..."
              required
            />
          </div>

          {/* Analysis & Actions */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 border-b pb-2">
              분석 및 조치사항
            </h3>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                근본 원인
              </label>
              <textarea
                value={formData.root_cause}
                onChange={(e) => handleChange("root_cause", e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                rows={3}
                placeholder="불량의 근본 원인 분석..."
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  시정조치
                </label>
                <textarea
                  value={formData.corrective_action}
                  onChange={(e) => handleChange("corrective_action", e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  rows={3}
                  placeholder="즉시 시정조치 내용..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  예방조치
                </label>
                <textarea
                  value={formData.preventive_action}
                  onChange={(e) => handleChange("preventive_action", e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  rows={3}
                  placeholder="재발 방지를 위한 예방조치..."
                />
              </div>
            </div>
          </div>

          {/* Form Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
              disabled={isLoading}
            >
              취소
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? "저장 중..." : "저장"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}