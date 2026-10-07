"use client";

import { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { dtpService, productService } from "@/services/master";
import { Plus, Trash2, X, Edit2, Link2, Search, Unlink, RefreshCw, ChevronLeft, ChevronRight } from "lucide-react";
import { SortableHeader } from "@/components/ui/SortableHeader";
import { getErrorMessage } from "@/lib/errorHandler";
import type { DtProjectLookup, DtProjectSelect, Product } from "@/types";

type SortField = "code" | "name" | "product_category" | "unit" | "created_at";
type SortOrder = "asc" | "desc";

const PRODUCT_CATEGORIES = [
  { value: "BRACKET", label: "브라켓" },
  { value: "SHAFT", label: "샤프트" },
  { value: "HOUSING", label: "하우징" },
  { value: "GEAR", label: "기어" },
  { value: "PLATE", label: "플레이트" },
  { value: "COVER", label: "커버" },
  { value: "OTHER", label: "기타" },
];

const UNITS = [
  { value: "EA", label: "EA (개)" },
  { value: "SET", label: "SET (세트)" },
  { value: "KG", label: "KG (킬로그램)" },
  { value: "M", label: "M (미터)" },
];

const DTP_PROJECTS_PAGE_SIZE = 5;

export default function ProductsPage() {
  const queryClient = useQueryClient();
  const [showModal, setShowModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [sortField, setSortField] = useState<SortField>("code");
  const [sortOrder, setSortOrder] = useState<SortOrder>("asc");
  const [projectSearch, setProjectSearch] = useState("");
  const [dtProjectResults, setDtProjectResults] = useState<DtProjectLookup[]>([]);
  const [projectPage, setProjectPage] = useState(1);
  const [hasSearchedDtProjects, setHasSearchedDtProjects] = useState(false);
  const [selectedDtProject, setSelectedDtProject] = useState<DtProjectSelect | null>(null);
  const [formData, setFormData] = useState({
    code: "",
    name: "",
    product_category: "",
    unit: "EA",
  });

  const { data: products, isLoading } = useQuery({
    queryKey: ["products"],
    queryFn: () => productService.getAll(),
  });

  const dtProjectSearchMutation = useMutation({
    mutationFn: () => dtpService.getProjects(projectSearch.trim() || undefined),
    onSuccess: (projects) => {
      setDtProjectResults(projects);
      setProjectPage(1);
      setHasSearchedDtProjects(true);
    },
    onError: (error: any) => {
      alert(`DT Project 조회 실패: ${getErrorMessage(error)}`);
    },
  });

  const createMutation = useMutation({
    mutationFn: productService.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["products"] });
      closeModal();
    },
    onError: (error: any) => {
      alert(`생성 실패: ${getErrorMessage(error)}`);
    },
  });

  const updateMutation = useMutation({
    mutationFn: async ({
      id,
      data,
      dtProject,
      shouldUnlink,
    }: {
      id: number;
      data: any;
      dtProject: DtProjectSelect | null;
      shouldUnlink: boolean;
    }) => {
      const product = await productService.update(id, data);
      if (dtProject) {
        await productService.linkDtProject(id, dtProject);
      } else if (shouldUnlink) {
        await productService.unlinkDtProject(id);
      }
      return product;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["products"] });
      closeModal();
    },
    onError: (error: any) => {
      alert(`수정 실패: ${getErrorMessage(error)}`);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: productService.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["products"] });
    },
    onError: (error: any) => {
      alert(getErrorMessage(error) || "삭제에 실패했습니다.");
    },
  });

  const closeModal = () => {
    setShowModal(false);
    setEditingProduct(null);
    setFormData({
      code: "",
      name: "",
      product_category: "",
      unit: "EA",
    });
    setSelectedDtProject(null);
    setProjectSearch("");
    setDtProjectResults([]);
    setProjectPage(1);
    setHasSearchedDtProjects(false);
  };

  const openEditModal = (product: Product) => {
    setEditingProduct(product);
    setFormData({
      code: product.code,
      name: product.name,
      product_category: product.product_category || "",
      unit: product.unit,
    });
    setSelectedDtProject(product.current_dt_project || null);
    setProjectSearch("");
    setDtProjectResults([]);
    setProjectPage(1);
    setHasSearchedDtProjects(false);
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
      product_category: formData.product_category || null,
    };
    if (editingProduct) {
      updateMutation.mutate({
        id: editingProduct.id,
        data,
        dtProject: selectedDtProject,
        shouldUnlink: !!editingProduct.current_dt_project && !selectedDtProject,
      });
    } else {
      createMutation.mutate({
        code: data.code,
        name: data.name,
        unit: data.unit,
        dt_project: selectedDtProject,
      });
    }
  };

  const sortedProducts = useMemo(() => {
    if (!products) return [];
    return [...products].sort((a, b) => {
      let aVal: any = a[sortField] || "";
      let bVal: any = b[sortField] || "";
      if (typeof aVal === "string") aVal = aVal.toLowerCase();
      if (typeof bVal === "string") bVal = bVal.toLowerCase();
      if (aVal < bVal) return sortOrder === "asc" ? -1 : 1;
      if (aVal > bVal) return sortOrder === "asc" ? 1 : -1;
      return 0;
    });
  }, [products, sortField, sortOrder]);

  const totalProjectPages = Math.max(
    1,
    Math.ceil(dtProjectResults.length / DTP_PROJECTS_PAGE_SIZE)
  );

  const pagedDtProjects = useMemo(() => {
    const start = (projectPage - 1) * DTP_PROJECTS_PAGE_SIZE;
    return dtProjectResults.slice(start, start + DTP_PROJECTS_PAGE_SIZE);
  }, [dtProjectResults, projectPage]);

  const getCategoryLabel = (category: string | null) => {
    if (!category) return "-";
    return PRODUCT_CATEGORIES.find((c) => c.value === category)?.label || category;
  };

  const getCategoryColor = (category: string | null) => {
    const colors: Record<string, string> = {
      BRACKET: "bg-primary-100 text-primary-800",
      SHAFT: "bg-green-100 text-green-800",
      HOUSING: "bg-purple-100 text-purple-800",
      GEAR: "bg-yellow-100 text-yellow-800",
      PLATE: "bg-orange-100 text-orange-800",
      COVER: "bg-pink-100 text-pink-800",
      OTHER: "bg-gray-100 text-gray-800",
    };
    return category ? colors[category] || "bg-gray-100 text-gray-800" : "";
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">제품 관리</h1>
        <button
          onClick={() => setShowModal(true)}
          className="btn btn-primary flex items-center gap-2"
        >
          <Plus size={16} />
          제품 추가
        </button>
      </div>

      {/* Product Table */}
      {isLoading ? (
        <div className="text-center py-8 text-gray-500">로딩 중...</div>
      ) : products && products.length > 0 ? (
        <div className="card overflow-hidden">
          <table className="table">
            <thead>
              <tr>
                <th>
                  <SortableHeader label="제품코드" field="code" currentSort={sortField} currentOrder={sortOrder} onSort={handleSort} />
                </th>
                <th>
                  <SortableHeader label="제품명" field="name" currentSort={sortField} currentOrder={sortOrder} onSort={handleSort} />
                </th>
                <th>
                  <SortableHeader label="카테고리" field="product_category" currentSort={sortField} currentOrder={sortOrder} onSort={handleSort} />
                </th>
                <th>
                  <SortableHeader label="단위" field="unit" currentSort={sortField} currentOrder={sortOrder} onSort={handleSort} />
                </th>
                <th>DT Project</th>
                <th>
                  <SortableHeader label="등록일" field="created_at" currentSort={sortField} currentOrder={sortOrder} onSort={handleSort} />
                </th>
                <th>액션</th>
              </tr>
            </thead>
            <tbody>
              {sortedProducts.map((product) => (
                <tr key={product.id}>
                  <td className="font-mono font-medium">{product.code}</td>
                  <td>{product.name}</td>
                  <td>
                    {product.product_category ? (
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getCategoryColor(product.product_category)}`}>
                        {getCategoryLabel(product.product_category)}
                      </span>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                  <td>{product.unit}</td>
                  <td>
                    {product.current_dt_project ? (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-green-100 text-green-700 text-xs font-medium">
                        <Link2 size={12} />
                        {product.current_dt_project.display_name || product.current_dt_project.element_id}
                      </span>
                    ) : (
                      <span className="text-gray-400">미연동</span>
                    )}
                  </td>
                  <td className="text-gray-500">
                    {new Date(product.created_at).toLocaleDateString()}
                  </td>
                  <td>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => openEditModal(product)}
                        className="p-1 text-primary-600 hover:bg-primary-50 rounded"
                        title="수정"
                      >
                        <Edit2 size={18} />
                      </button>
                      <button
                        onClick={() => {
                          if (confirm("정말 삭제하시겠습니까?")) {
                            deleteMutation.mutate(product.id);
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
          <p className="text-gray-500 mb-4">등록된 제품이 없습니다.</p>
          <button onClick={() => setShowModal(true)} className="btn btn-primary">
            첫 제품 추가
          </button>
        </div>
      )}

      {/* Create/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="text-lg font-semibold">
                {editingProduct ? "제품 수정" : "제품 추가"}
              </h2>
              <button
                onClick={closeModal}
                className="p-2 hover:bg-gray-100 rounded"
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-4 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    제품 코드 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.code}
                    onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                    className="w-full px-3 py-2 border rounded-md"
                    placeholder="PROD-001"
                    required
                    disabled={!!editingProduct}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    제품명 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 border rounded-md"
                    placeholder="브라켓 A"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    제품 카테고리
                  </label>
                  <select
                    value={formData.product_category}
                    onChange={(e) => setFormData({ ...formData, product_category: e.target.value })}
                    className="w-full px-3 py-2 border rounded-md"
                  >
                    <option value="">선택 안함</option>
                    {PRODUCT_CATEGORIES.map((cat) => (
                      <option key={cat.value} value={cat.value}>
                        {cat.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    단위
                  </label>
                  <select
                    value={formData.unit}
                    onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
                    className="w-full px-3 py-2 border rounded-md"
                  >
                    {UNITS.map((u) => (
                      <option key={u.value} value={u.value}>
                        {u.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="border rounded-md bg-gray-50">
                <div className="flex items-center justify-between gap-3 mb-3">
                  <div className="px-3 pt-3">
                    <div className="text-sm font-medium text-gray-700">DT Project 연동</div>
                    <div className="text-xs text-gray-500">
                      선택하지 않으면 기존 방식의 일반 제품으로 저장됩니다.
                    </div>
                  </div>
                  {selectedDtProject && (
                    <button
                      type="button"
                      onClick={() => setSelectedDtProject(null)}
                      className="btn btn-secondary text-xs flex items-center gap-1 mr-3 mt-3"
                    >
                      <Unlink size={14} />
                      연동 해제
                    </button>
                  )}
                </div>

                {selectedDtProject ? (
                  <div className="mx-3 mb-3 rounded border bg-white p-3">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-sm font-medium text-green-700">
                        <Link2 size={15} />
                        <span>
                          {selectedDtProject.display_name || selectedDtProject.element_id}
                        </span>
                      </div>
                      <div className="grid grid-cols-[110px_1fr] gap-x-3 gap-y-1 text-xs">
                        <div className="text-gray-400">Asset Global Id</div>
                        <div className="break-all text-gray-600">{selectedDtProject.asset_global_id}</div>
                        <div className="text-gray-400">Asset id</div>
                        <div className="break-all text-gray-600">{selectedDtProject.asset_id}</div>
                        <div className="text-gray-400">Element id</div>
                        <div className="break-all text-gray-600">{selectedDtProject.element_id}</div>
                        {selectedDtProject.element_full_id && (
                          <>
                            <div className="text-gray-400">Element id(Full)</div>
                            <div className="break-all text-gray-600">
                              {selectedDtProject.element_full_id}
                            </div>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                ) : null}

                <div className="flex items-center gap-2 px-3 mb-2">
                  <div className="relative flex-1">
                    <Search size={14} className="absolute left-3 top-2.5 text-gray-400" />
                    <input
                      type="text"
                      value={projectSearch}
                      onChange={(e) => setProjectSearch(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          e.preventDefault();
                          dtProjectSearchMutation.mutate();
                        }
                      }}
                      className="w-full pl-8 pr-3 py-2 border rounded-md text-sm"
                      placeholder="프로젝트명, element id 검색"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={() => dtProjectSearchMutation.mutate()}
                    disabled={dtProjectSearchMutation.isPending}
                    className="btn btn-secondary text-sm flex items-center gap-1 shrink-0"
                  >
                    <RefreshCw
                      size={14}
                      className={dtProjectSearchMutation.isPending ? "animate-spin" : ""}
                    />
                    갱신
                  </button>
                </div>

                <div className="mx-3 mb-3 overflow-hidden border rounded bg-white">
                  <div className="flex items-center justify-between border-b px-3 py-2 text-xs">
                    <span className="font-medium text-gray-600">
                      조회 결과 총 {dtProjectResults.length}개
                    </span>
                    {dtProjectSearchMutation.isPending && dtProjectResults.length > 0 && (
                      <span className="text-gray-400">갱신 중</span>
                    )}
                  </div>
                  <div className="h-[290px] overflow-hidden">
                    {dtProjectSearchMutation.isPending && dtProjectResults.length === 0 ? (
                      <div className="p-3 text-sm text-gray-500">조회 중...</div>
                    ) : dtProjectResults.length > 0 ? (
                      pagedDtProjects.map((project) => {
                      const selected =
                        selectedDtProject?.asset_global_id === project.asset_global_id &&
                        selectedDtProject?.asset_id === project.asset_id &&
                        selectedDtProject?.element_id === project.element_id;
                      return (
                        <button
                          key={`${project.asset_global_id}-${project.asset_id}-${project.element_id}`}
                          type="button"
                          onClick={() => setSelectedDtProject(project)}
                          className={`w-full min-h-[58px] text-left px-3 py-2 border-b hover:bg-primary-50 ${
                            selected ? "bg-primary-50 text-primary-700" : ""
                          }`}
                        >
                          <div className="text-sm font-medium">
                            {project.display_name || project.element_id}
                          </div>
                          <div className="text-xs text-gray-500 break-all leading-4">
                            {project.asset_id} / {project.element_id}
                          </div>
                        </button>
                      );
                    })
                    ) : (
                      <div className="p-3 text-sm text-gray-500">
                        {hasSearchedDtProjects
                          ? "조회된 DT Project가 없습니다."
                          : "갱신 버튼으로 DT Project 목록을 조회하세요."}
                      </div>
                    )}
                  </div>
                  <div className="flex items-center justify-end border-t px-3 py-2 text-xs text-gray-500">
                    <button
                      type="button"
                      onClick={() => setProjectPage((page) => Math.max(1, page - 1))}
                      disabled={projectPage <= 1}
                      className="p-1 rounded hover:bg-gray-100 disabled:opacity-40"
                      aria-label="이전 페이지"
                    >
                      <ChevronLeft size={16} />
                    </button>
                    <span className="mx-2">
                      {projectPage} / {totalProjectPages}
                    </span>
                    <button
                      type="button"
                      onClick={() =>
                        setProjectPage((page) => Math.min(totalProjectPages, page + 1))
                      }
                      disabled={projectPage >= totalProjectPages}
                      className="p-1 rounded hover:bg-gray-100 disabled:opacity-40"
                      aria-label="다음 페이지"
                    >
                      <ChevronRight size={16} />
                    </button>
                  </div>
                </div>
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
