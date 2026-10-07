"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { scenarioService, productService } from "@/services/master";
import { Plus, Trash2, X, ToggleLeft, ToggleRight, FileJson, Download, AlertCircle, Edit2, Workflow } from "lucide-react";
import { Scenario } from "@/types";

export default function ScenariosPage() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const [showModal, setShowModal] = useState(false);
  const [editingScenario, setEditingScenario] = useState<Scenario | null>(null);
  const [formData, setFormData] = useState({
    code: "",
    name: "",
    file_path: "",
    product_id: undefined as number | undefined,
    is_active: true,
  });

  // Preview modal state
  const [showPreview, setShowPreview] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewContent, setPreviewContent] = useState<{
    scenario_name?: string;
    file_path: string;
    content?: any;
    error?: string;
  } | null>(null);

  const handlePreview = async (scenarioId: number) => {
    setPreviewLoading(true);
    setShowPreview(true);
    try {
      const content = await scenarioService.getContent(scenarioId);
      setPreviewContent(content);
    } catch (error: any) {
      setPreviewContent({
        file_path: "",
        error: error.response?.data?.detail || error.message || "파일을 불러올 수 없습니다.",
      });
    } finally {
      setPreviewLoading(false);
    }
  };

  const downloadJson = () => {
    if (!previewContent?.content) return;
    const blob = new Blob([JSON.stringify(previewContent.content, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${previewContent.scenario_name || "scenario"}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const { data: scenarios, isLoading } = useQuery({
    queryKey: ["scenarios"],
    queryFn: () => scenarioService.getAll(undefined, false),
  });

  const { data: products } = useQuery({
    queryKey: ["products"],
    queryFn: () => productService.getAll(),
  });

  const createMutation = useMutation({
    mutationFn: scenarioService.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scenarios"] });
      closeModal();
    },
    onError: (error: any) => {
      alert(`생성 실패: ${error.response?.data?.detail || error.message}`);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => scenarioService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scenarios"] });
      closeModal();
    },
    onError: (error: any) => {
      alert(`수정 실패: ${error.response?.data?.detail || error.message}`);
    },
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, isActive }: { id: number; isActive: boolean }) =>
      scenarioService.toggleActive(id, isActive),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scenarios"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: scenarioService.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scenarios"] });
    },
    onError: (error: any) => {
      alert(error?.response?.data?.detail || "삭제에 실패했습니다.");
    },
  });

  const closeModal = () => {
    setShowModal(false);
    setEditingScenario(null);
    setFormData({ code: "", name: "", file_path: "", product_id: undefined, is_active: true });
  };

  const openEditModal = (scenario: Scenario) => {
    setEditingScenario(scenario);
    setFormData({
      code: scenario.code || "",
      name: scenario.name,
      file_path: scenario.file_path,
      product_id: scenario.product_id || undefined,
      is_active: scenario.is_active,
    });
    setShowModal(true);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const data = {
      ...formData,
      code: formData.code || undefined,
      product_id: formData.product_id || undefined,
    };
    if (editingScenario) {
      updateMutation.mutate({ id: editingScenario.id, data });
    } else {
      createMutation.mutate(data);
    }
  };

  const getProductName = (productId: number | null) => {
    if (!productId) return "-";
    return products?.find((p) => p.id === productId)?.name || "-";
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">물류 시나리오</h1>
          <p className="text-sm text-gray-500">AGV/로봇 제어 시나리오를 관리합니다.</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="btn btn-primary flex items-center gap-2"
        >
          <Plus size={16} />
          시나리오 추가
        </button>
      </div>

      {/* Scenario Table */}
      {isLoading ? (
        <div className="text-center py-8 text-gray-500">로딩 중...</div>
      ) : scenarios && scenarios.length > 0 ? (
        <div className="card overflow-hidden">
          <table className="table">
            <thead>
              <tr>
                <th>코드</th>
                <th>시나리오명</th>
                <th>대상 제품</th>
                <th>제어 파일</th>
                <th>상태</th>
                <th>등록일</th>
                <th>액션</th>
              </tr>
            </thead>
            <tbody>
              {scenarios.map((scenario) => (
                <tr key={scenario.id}>
                  <td className="font-mono font-medium text-sm">
                    {scenario.code || <span className="text-gray-400">-</span>}
                  </td>
                  <td className="font-medium">{scenario.name}</td>
                  <td>{getProductName(scenario.product_id)}</td>
                  <td>
                    <button
                      onClick={() => handlePreview(scenario.id)}
                      className="font-mono text-sm text-primary-600 hover:text-primary-800 hover:underline flex items-center gap-1"
                      title="JSON 미리보기"
                    >
                      <FileJson size={14} />
                      {scenario.file_path}
                    </button>
                  </td>
                  <td>
                    <button
                      onClick={() =>
                        toggleMutation.mutate({
                          id: scenario.id,
                          isActive: !scenario.is_active,
                        })
                      }
                      className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
                        scenario.is_active
                          ? "bg-green-100 text-green-800"
                          : "bg-gray-100 text-gray-600"
                      }`}
                    >
                      {scenario.is_active ? (
                        <>
                          <ToggleRight size={14} /> 활성
                        </>
                      ) : (
                        <>
                          <ToggleLeft size={14} /> 비활성
                        </>
                      )}
                    </button>
                  </td>
                  <td className="text-gray-500">
                    {new Date(scenario.created_at).toLocaleDateString()}
                  </td>
                  <td>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() =>
                          router.push(`/master/scenarios/${scenario.id}/edit`)
                        }
                        className="p-1 text-purple-600 hover:bg-purple-50 rounded"
                        title="워크플로우 편집 (n8n YAML editor)"
                      >
                        <Workflow size={18} />
                      </button>
                      <button
                        onClick={() => openEditModal(scenario)}
                        className="p-1 text-primary-600 hover:bg-primary-50 rounded"
                        title="수정"
                      >
                        <Edit2 size={18} />
                      </button>
                      <button
                        onClick={() => {
                          if (confirm("정말 삭제하시겠습니까?")) {
                            deleteMutation.mutate(scenario.id);
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
          <p className="text-gray-500 mb-4">등록된 시나리오가 없습니다.</p>
          <button onClick={() => setShowModal(true)} className="btn btn-primary">
            첫 시나리오 추가
          </button>
        </div>
      )}

      {/* Create/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="text-lg font-semibold">
                {editingScenario ? "시나리오 수정" : "시나리오 추가"}
              </h2>
              <button
                onClick={closeModal}
                className="p-2 hover:bg-gray-100 rounded"
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  시나리오 코드
                </label>
                <input
                  type="text"
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md font-mono"
                  placeholder="SCN-001"
                />
                <p className="mt-1 text-xs text-gray-500">비워두면 자동 생성됩니다.</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  시나리오명 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md"
                  placeholder="1라인 로봇 핸들링"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  제어 파일 경로 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.file_path}
                  onChange={(e) => setFormData({ ...formData, file_path: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md font-mono"
                  placeholder="/scenarios/robot_path_a.yaml"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  대상 제품 (선택)
                </label>
                <select
                  value={formData.product_id || ""}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      product_id: e.target.value ? parseInt(e.target.value) : undefined,
                    })
                  }
                  className="w-full px-3 py-2 border rounded-md"
                >
                  <option value="">전체 제품에 적용</option>
                  {products?.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.code} - {p.name}
                    </option>
                  ))}
                </select>
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

      {/* JSON Preview Modal */}
      {showPreview && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[80vh] flex flex-col">
            <div className="flex items-center justify-between p-4 border-b">
              <div>
                <h2 className="text-lg font-semibold">
                  {previewContent?.scenario_name || "제어 파일 내용"}
                </h2>
                {previewContent?.file_path && (
                  <p className="text-sm text-gray-500 font-mono">{previewContent.file_path}</p>
                )}
              </div>
              <div className="flex items-center gap-2">
                {previewContent?.content && (
                  <button
                    onClick={downloadJson}
                    className="btn btn-secondary text-sm flex items-center gap-1"
                  >
                    <Download size={14} />
                    다운로드
                  </button>
                )}
                <button
                  onClick={() => {
                    setShowPreview(false);
                    setPreviewContent(null);
                  }}
                  className="p-2 hover:bg-gray-100 rounded"
                >
                  <X size={20} />
                </button>
              </div>
            </div>
            <div className="p-4 overflow-auto flex-1">
              {previewLoading ? (
                <div className="text-center py-8 text-gray-500">로딩 중...</div>
              ) : previewContent?.error ? (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
                  <AlertCircle className="text-red-500 flex-shrink-0 mt-0.5" size={20} />
                  <div>
                    <p className="font-medium text-red-700">파일을 불러올 수 없습니다</p>
                    <p className="text-sm text-red-600 mt-1">{previewContent.error}</p>
                  </div>
                </div>
              ) : previewContent?.content ? (
                <pre className="bg-gray-900 text-green-400 p-4 rounded-lg text-sm overflow-auto">
                  {JSON.stringify(previewContent.content, null, 2)}
                </pre>
              ) : (
                <div className="text-center py-8 text-gray-500">내용이 없습니다</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
