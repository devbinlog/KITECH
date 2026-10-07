"use client";

import { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { stdProcessService } from "@/services/master";
import { Plus, Trash2, X, Edit2 } from "lucide-react";
import { SortableHeader } from "@/components/ui/SortableHeader";
import { StdProcess } from "@/types";
import { useMachineTypes } from "@/hooks/useMachineTypes";

type SortField = "code" | "name" | "process_category" | "required_machines" | "cycle_time_sec" | "created_at";
type SortOrder = "asc" | "desc";

const PROCESS_CATEGORIES = [
  { value: "MACHINING", label: "가공" },
  { value: "ASSEMBLY", label: "조립" },
  { value: "INSPECTION", label: "검사" },
  { value: "SURFACE", label: "표면처리" },
  { value: "HEAT_TREATMENT", label: "열처리" },
  { value: "OTHER", label: "기타" },
];

const EQUIPMENT_TYPES = [
  { value: "CNC", label: "CNC" },
  { value: "ROBOT", label: "ROBOT" },
  { value: "AMR", label: "AMR" },
  { value: "PLC", label: "PLC" },
];

export default function ProcessesPage() {
  const queryClient = useQueryClient();
  const machineTypes = useMachineTypes();
  const machineTypeOptions = machineTypes.length > 0 ? machineTypes : EQUIPMENT_TYPES.map((type) => type.value);
  const [showModal, setShowModal] = useState(false);
  const [editingProcess, setEditingProcess] = useState<StdProcess | null>(null);
  const [sortField, setSortField] = useState<SortField>("code");
  const [sortOrder, setSortOrder] = useState<SortOrder>("asc");
  const [formData, setFormData] = useState({
    code: "",
    name: "",
    description: "",
    process_category: "",
    equipment_type: "",
    required_machines: [] as string[],
    cycle_time_sec: 0,
    setup_time_sec: 0,
  });

  const { data: processes, isLoading } = useQuery({
    queryKey: ["std-processes"],
    queryFn: stdProcessService.getAll,
  });

  const createMutation = useMutation({
    mutationFn: stdProcessService.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["std-processes"] });
      closeModal();
    },
    onError: (error: any) => {
      alert(`생성 실패: ${error.response?.data?.detail || error.message}`);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => stdProcessService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["std-processes"] });
      closeModal();
    },
    onError: (error: any) => {
      alert(`수정 실패: ${error.response?.data?.detail || error.message}`);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: stdProcessService.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["std-processes"] });
    },
    onError: (error: any) => {
      alert(`삭제 실패: ${error.response?.data?.detail || error.message}`);
    },
  });

  const closeModal = () => {
    setShowModal(false);
    setEditingProcess(null);
    setFormData({
      code: "",
      name: "",
      description: "",
      process_category: "",
      equipment_type: "",
      required_machines: [],
      cycle_time_sec: 0,
      setup_time_sec: 0,
    });
  };

  const openEditModal = (process: StdProcess) => {
    setEditingProcess(process);
    setFormData({
      code: process.code,
      name: process.name,
      description: process.description || "",
      process_category: process.process_category || "",
      equipment_type: process.equipment_type || "",
      required_machines: process.required_machines || (process.equipment_type ? [process.equipment_type] : []),
      cycle_time_sec: process.cycle_time_sec || 0,
      setup_time_sec: process.setup_time_sec || 0,
    });
    setShowModal(true);
  };

  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortField(field as SortField);
      setSortOrder("asc");
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const data = {
      ...formData,
      process_category: formData.process_category || null,
      equipment_type: formData.equipment_type || formData.required_machines[0] || null,
      required_machines: formData.required_machines.length > 0 ? formData.required_machines : null,
    };
    if (editingProcess) {
      updateMutation.mutate({ id: editingProcess.id, data });
    } else {
      createMutation.mutate(data);
    }
  };

  const sortedProcesses = useMemo(() => {
    if (!processes) return [];
    return [...processes].sort((a, b) => {
      let aVal: any = a[sortField] || "";
      let bVal: any = b[sortField] || "";
      if (typeof aVal === "string") aVal = aVal.toLowerCase();
      if (typeof bVal === "string") bVal = bVal.toLowerCase();
      if (aVal < bVal) return sortOrder === "asc" ? -1 : 1;
      if (aVal > bVal) return sortOrder === "asc" ? 1 : -1;
      return 0;
    });
  }, [processes, sortField, sortOrder]);

  const getCategoryLabel = (category: string | null) => {
    if (!category) return "-";
    return PROCESS_CATEGORIES.find((c) => c.value === category)?.label || category;
  };

  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${seconds}초`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return secs > 0 ? `${mins}분 ${secs}초` : `${mins}분`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">표준공정 관리</h1>
        <button
          onClick={() => setShowModal(true)}
          className="btn btn-primary flex items-center gap-2"
        >
          <Plus size={16} />
          표준공정 추가
        </button>
      </div>

      {/* Process Table */}
      {isLoading ? (
        <div className="text-center py-8 text-gray-500">로딩 중...</div>
      ) : processes && processes.length > 0 ? (
        <div className="card overflow-hidden">
          <table className="table">
            <thead>
              <tr>
                <th>
                  <SortableHeader label="코드" field="code" currentSort={sortField} currentOrder={sortOrder} onSort={handleSort} />
                </th>
                <th>
                  <SortableHeader label="공정명" field="name" currentSort={sortField} currentOrder={sortOrder} onSort={handleSort} />
                </th>
                <th>
                  <SortableHeader label="카테고리" field="process_category" currentSort={sortField} currentOrder={sortOrder} onSort={handleSort} />
                </th>
                <th>
                  <SortableHeader label="설비타입" field="required_machines" currentSort={sortField} currentOrder={sortOrder} onSort={handleSort} />
                </th>
                <th>
                  <SortableHeader label="Cycle Time" field="cycle_time_sec" currentSort={sortField} currentOrder={sortOrder} onSort={handleSort} />
                </th>
                <th>Setup Time</th>
                <th>설명</th>
                <th>
                  <SortableHeader label="등록일" field="created_at" currentSort={sortField} currentOrder={sortOrder} onSort={handleSort} />
                </th>
                <th>액션</th>
              </tr>
            </thead>
            <tbody>
              {sortedProcesses.map((process) => (
                <tr key={process.id}>
                  <td className="font-mono font-medium">{process.code}</td>
                  <td>{process.name}</td>
                  <td>
                    {process.process_category ? (
                      <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
                        {getCategoryLabel(process.process_category)}
                      </span>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                  <td>
                    {(process.required_machines?.length || process.equipment_type) ? (
                      <div className="flex flex-wrap gap-1">
                        {(process.required_machines?.length ? process.required_machines : [process.equipment_type]).filter(Boolean).map((machine) => (
                          <span key={machine} className="px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                            {machine}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                  <td className="font-mono text-sm">{formatTime(process.cycle_time_sec)}</td>
                  <td className="font-mono text-sm text-gray-500">{formatTime(process.setup_time_sec)}</td>
                  <td className="text-gray-500 max-w-xs truncate">
                    {process.description || "-"}
                  </td>
                  <td className="text-gray-500">
                    {new Date(process.created_at).toLocaleDateString()}
                  </td>
                  <td>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => openEditModal(process)}
                        className="p-1 text-primary-600 hover:bg-primary-50 rounded"
                        title="수정"
                      >
                        <Edit2 size={18} />
                      </button>
                      <button
                        onClick={() => {
                          if (confirm("정말 삭제하시겠습니까?")) {
                            deleteMutation.mutate(process.id);
                          }
                        }}
                        className="p-1 text-red-600 hover:bg-red-50 rounded"
                        title="삭제"
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-12 bg-white rounded-lg border border-dashed border-gray-300">
          <p className="text-gray-500 mb-4">등록된 표준공정이 없습니다.</p>
          <button onClick={() => setShowModal(true)} className="btn btn-primary">
            첫 표준공정 추가
          </button>
        </div>
      )}

      {/* Create/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="text-lg font-semibold">
                {editingProcess ? "표준공정 수정" : "표준공정 추가"}
              </h2>
              <button
                onClick={closeModal}
                className="p-2 hover:bg-gray-100 rounded"
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    공정 코드 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.code}
                    onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                    className="w-full px-3 py-2 border rounded-md"
                    placeholder="STD-CUT-01"
                    required
                    disabled={!!editingProcess}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    공정명 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 border rounded-md"
                    placeholder="레이저 절단"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    공정 카테고리
                  </label>
                  <select
                    value={formData.process_category}
                    onChange={(e) => setFormData({ ...formData, process_category: e.target.value })}
                    className="w-full px-3 py-2 border rounded-md"
                  >
                    <option value="">선택 안함</option>
                    {PROCESS_CATEGORIES.map((cat) => (
                      <option key={cat.value} value={cat.value}>
                        {cat.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    설비 타입 (복수 선택)
                  </label>
                  <div className="border rounded-md px-3 py-2 space-y-1 min-h-[42px]">
                    {machineTypeOptions.map((machineType) => (
                      <label key={machineType} className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={formData.required_machines.includes(machineType)}
                          onChange={(e) => {
                            const next = e.target.checked
                              ? [...formData.required_machines, machineType]
                              : formData.required_machines.filter((item) => item !== machineType);
                            setFormData({
                              ...formData,
                              required_machines: next,
                              equipment_type: next[0] || "",
                            });
                          }}
                          className="accent-primary-600"
                        />
                        <span className="text-sm">{machineType}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Cycle Time (초)
                  </label>
                  <input
                    type="number"
                    value={formData.cycle_time_sec}
                    onChange={(e) => setFormData({ ...formData, cycle_time_sec: parseInt(e.target.value) || 0 })}
                    className="w-full px-3 py-2 border rounded-md"
                    min="0"
                    placeholder="300"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Setup Time (초)
                  </label>
                  <input
                    type="number"
                    value={formData.setup_time_sec}
                    onChange={(e) => setFormData({ ...formData, setup_time_sec: parseInt(e.target.value) || 0 })}
                    className="w-full px-3 py-2 border rounded-md"
                    min="0"
                    placeholder="60"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  설명
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md"
                  rows={3}
                  placeholder="작업 표준 설명..."
                />
              </div>

              <div className="flex justify-end gap-2 pt-4">
                <button
                  type="button"
                  onClick={closeModal}
                  className="btn btn-secondary"
                >
                  취소
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending || updateMutation.isPending}
                  className="btn btn-primary"
                >
                  {createMutation.isPending || updateMutation.isPending ? "저장 중..." : "저장"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
