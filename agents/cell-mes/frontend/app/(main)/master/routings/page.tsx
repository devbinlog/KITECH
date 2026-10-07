"use client";

import { useState, useEffect, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { productService, stdProcessService, routingService } from "@/services/master";
import { DtFileRef, Product, ProcessRouting } from "@/types";
import {
  Plus,
  Save,
  Trash2,
  ChevronRight,
  FileText,
  Image as ImageIcon,
  File,
  AlertCircle,
  Upload,
  Database,
  X,
} from "lucide-react";
import { useMachineTypes } from "@/hooks/useMachineTypes";
import ProductCellsEditor from "@/components/master/ProductCellsEditor";

const fileTypeIcons = {
  NC: FileText,
  IMAGE: ImageIcon, // Corrected from Image to ImageIcon
  DOC: File,
};

type RoutingDraft = {
  std_process_id: number;
  sequence: number;
  revision: string;
  setup_id?: string | null;
  dt_workplan_id?: number | null;
  required_machines?: string[] | null;
  cycle_time_sec?: number | null;
  cycle_time_breakdown?: Record<string, any> | null;
  remarks: string;
  files: Array<{
    file_type: string;
    file_path: string;
    original_filename?: string | null;
    source_type?: "LOCAL_UPLOAD" | "DTP";
    dt_file_ref_id?: number | null;
    dt_file?: DtFileRef | null;
    compatible_machines?: string[] | null;
    sort_order: number;
  }>;
};

export default function RoutingsPage() {
  const queryClient = useQueryClient();
  const machineTypes = useMachineTypes();
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [routings, setRoutings] = useState<RoutingDraft[]>([]);
  const [ncPickerRoutingIndex, setNcPickerRoutingIndex] = useState<number | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [hasCellChanges, setHasCellChanges] = useState(false);
  const [isSavingCells, setIsSavingCells] = useState(false);
  const [isUploading, setIsUploading] = useState(false); // Added isUploading state
  const initialLoadDone = useRef(false);

  const { data: products } = useQuery({
    queryKey: ["products"],
    queryFn: () => productService.getAll(),
  });

  const { data: processes } = useQuery({
    queryKey: ["std-processes"],
    queryFn: stdProcessService.getAll,
  });

  const { data: existingRoutings, isSuccess: routingsLoaded, isError: routingsFailed, refetch: refetchRoutings } = useQuery({
    queryKey: ["routings", selectedProduct?.id],
    queryFn: () => (selectedProduct ? routingService.getByProduct(selectedProduct.id) : []),
    enabled: !!selectedProduct,
  });

  const { data: dtProjectLink } = useQuery({
    queryKey: ["product-dt-project", selectedProduct?.id],
    queryFn: () => productService.getDtProject(selectedProduct!.id),
    enabled: !!selectedProduct,
  });

  const currentDtProject = dtProjectLink?.dt_project || selectedProduct?.current_dt_project || null;
  const pickerRouting = ncPickerRoutingIndex !== null ? routings[ncPickerRoutingIndex] : null;
  const pickerWorkplan = currentDtProject?.workplans.find((workplan) => workplan.id === pickerRouting?.dt_workplan_id);

  const { data: dtNcFiles, isFetching: isFetchingDtNcFiles } = useQuery({
    queryKey: ["product-dt-nc-files", selectedProduct?.id, pickerWorkplan?.workplan_id],
    queryFn: () => productService.getDtNcFiles(selectedProduct!.id, pickerWorkplan?.workplan_id),
    enabled: !!selectedProduct && ncPickerRoutingIndex !== null && !!pickerWorkplan,
  });

  // Auto-load routings when product changes or data fetched
  useEffect(() => {
    if (initialLoadDone.current) return;
    if (existingRoutings && selectedProduct) {
      setRoutings(
        existingRoutings.map((r) => ({
          std_process_id: r.std_process_id,
          sequence: r.sequence,
          revision: r.revision,
          setup_id: r.setup_id,
          dt_workplan_id: r.dt_workplan_id,
          required_machines: r.required_machines,
          cycle_time_sec: r.cycle_time_sec,
          cycle_time_breakdown: r.cycle_time_breakdown,
          remarks: r.remarks || "",
          files: r.files.map((f) => ({
            file_type: f.file_type,
            file_path: f.file_path,
            original_filename: f.original_filename,
            source_type: f.source_type || "LOCAL_UPLOAD",
            dt_file_ref_id: f.dt_file_ref_id,
            dt_file: f.dt_file,
            compatible_machines: f.compatible_machines,
            sort_order: f.sort_order,
          })),
        }))
      );
      setHasUnsavedChanges(false);
      initialLoadDone.current = true;
    } else if (selectedProduct && !existingRoutings) {
      // Product selected but no routings exist yet
      setRoutings([]);
      setHasUnsavedChanges(false);
    }
  }, [existingRoutings, selectedProduct]);

  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => {
      if (hasUnsavedChanges || hasCellChanges) { event.preventDefault(); event.returnValue = ""; }
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [hasUnsavedChanges, hasCellChanges]);

  // Track unsaved changes
  const updateRoutingsWithChange = (newRoutings: typeof routings) => {
    setRoutings(newRoutings);
    if (initialLoadDone.current) {
      setHasUnsavedChanges(true);
    }
  };

  const saveMutation = useMutation({
    mutationFn: (data: { productId: number; routings: typeof routings }) =>
      routingService.save(data.productId, data.routings),
    onSuccess: (data, variables) => {
      initialLoadDone.current = false;
      queryClient.setQueryData(["routings", variables.productId], data);
      queryClient.invalidateQueries({ queryKey: ["routings", selectedProduct?.id] });
      setHasUnsavedChanges(false);
      alert("라우팅이 저장되었습니다.");
    },
    onError: (error: any) => {
      alert(`저장 실패: ${error.response?.data?.detail || error.message}`);
    },
  });

  const handleProductSelect = (product: Product) => {
    if (selectedProduct?.id === product.id || saveMutation.isPending || isSavingCells) return;
    if ((hasUnsavedChanges || hasCellChanges) && selectedProduct && selectedProduct.id !== product.id) {
      if (!confirm("저장되지 않은 변경사항이 있습니다. 계속하시겠습니까?")) {
        return;
      }
    }
    initialLoadDone.current = false;
    setSelectedProduct(product);
    setHasUnsavedChanges(false);
    setHasCellChanges(false);
    setNcPickerRoutingIndex(null);
  };

  const addRouting = () => {
    const maxSeq = routings.length > 0 ? Math.max(...routings.map((r) => r.sequence)) : 0;
    updateRoutingsWithChange([
      ...routings,
      {
        std_process_id: processes?.[0]?.id || 0,
        sequence: maxSeq + 10,
        revision: "A",
        setup_id: null,
        dt_workplan_id: null,
        required_machines: null,
        cycle_time_sec: null,
        cycle_time_breakdown: null,
        remarks: "",
        files: [],
      },
    ]);
  };

  const removeRouting = (index: number) => {
    updateRoutingsWithChange(routings.filter((_, i) => i !== index));
  };

  const updateRouting = (index: number, field: string, value: any) => {
    const newRoutings = [...routings];
    (newRoutings[index] as any)[field] = value;
    updateRoutingsWithChange(newRoutings);
  };

  const updateCycleTime = (index: number, value: number | null) => {
    updateRoutingsWithChange(routings.map((routing, i) => i === index
      ? { ...routing, cycle_time_sec: value, cycle_time_breakdown: null } : routing));
  };

  const addFile = (routingIndex: number) => {
    const newRoutings = [...routings];
    newRoutings[routingIndex].files.push({
      file_type: "NC",
      file_path: "",
      source_type: "LOCAL_UPLOAD",
      dt_file_ref_id: null,
      compatible_machines: null,
      sort_order: newRoutings[routingIndex].files.length + 1,
    });
    updateRoutingsWithChange(newRoutings);
  };

  const removeFile = (routingIndex: number, fileIndex: number) => {
    const newRoutings = [...routings];
    newRoutings[routingIndex].files = newRoutings[routingIndex].files.filter(
      (_, i) => i !== fileIndex
    );
    updateRoutingsWithChange(newRoutings);
  };

  const handleFileUpload = async (routingIndex: number, fileIndex: number, e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setIsUploading(true);
      const res = await routingService.uploadRoutingFile(file);
      const newRoutings = [...routings];
      newRoutings[routingIndex].files[fileIndex].file_path = res.file_path;
      newRoutings[routingIndex].files[fileIndex].original_filename = res.original_filename;
      newRoutings[routingIndex].files[fileIndex].source_type = "LOCAL_UPLOAD";
      newRoutings[routingIndex].files[fileIndex].dt_file_ref_id = null;
      newRoutings[routingIndex].files[fileIndex].dt_file = null;
      updateRoutingsWithChange(newRoutings);
    } catch (err: any) {
      alert("파일 업로드 오류: " + (err.response?.data?.detail || err.message));
    } finally {
      setIsUploading(false);
      e.target.value = ""; // 초기화
    }
  };

  const handleSave = () => {
    if (!selectedProduct) return;
    if (routings.some(r => r.cycle_time_sec != null &&
      (!Number.isSafeInteger(r.cycle_time_sec) || r.cycle_time_sec < 0 || r.cycle_time_sec > 2147483647))) {
      alert("사이클 타임은 0 이상의 정수(초)로 입력해주세요. 최대 2147483647초입니다.");
      return;
    }
    saveMutation.mutate({ productId: selectedProduct.id, routings });
  };

  const addDtpNcFile = (ncFile: DtFileRef) => {
    if (ncPickerRoutingIndex === null) return;
    const newRoutings = [...routings];
    const routing = newRoutings[ncPickerRoutingIndex];
    routing.files.push({
      file_type: "NC",
      file_path: ncFile.path,
      original_filename: ncFile.display_name || ncFile.path.split("/").pop() || "DTP NC",
      source_type: "DTP",
      dt_file_ref_id: ncFile.id,
      dt_file: ncFile,
      compatible_machines: null,
      sort_order: routing.files.length + 1,
    });
    updateRoutingsWithChange(newRoutings);
    setNcPickerRoutingIndex(null);
  };

  const getProcessName = (processId: number) => {
    return processes?.find((p) => p.id === processId)?.name || "";
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">라우팅 설계</h1>
        {selectedProduct && (
          <button
            onClick={handleSave}
            disabled={saveMutation.isPending || !routingsLoaded}
            className="btn btn-primary flex items-center gap-2"
          >
            <Save size={16} />
            {saveMutation.isPending ? "저장 중..." : "저장"}
          </button>
        )}
      </div>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Product List */}
        <div className="w-full lg:w-64 shrink-0">
          <div className="card">
            <h2 className="card-header">제품 목록</h2>
            <div className="space-y-1">
              {products?.map((product) => (
                <button
                  key={product.id}
                  onClick={() => handleProductSelect(product)}
                  className={`w-full text-left px-3 py-2 rounded-md flex items-center justify-between ${selectedProduct?.id === product.id
                    ? "bg-primary-100 text-primary-700"
                    : "hover:bg-gray-100"
                    }`}
                >
                  <div>
                    <div className="font-medium">{product.name}</div>
                    <div className="text-xs text-gray-500">{product.code}</div>
                  </div>
                  <ChevronRight size={16} />
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Routing Editor */}
        <div className="flex-1 min-w-0">
          {selectedProduct ? (
            <div className="card">
              <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="text-lg font-semibold">{selectedProduct.name}</h2>
                    {hasUnsavedChanges && (
                      <span className="flex items-center gap-1 px-2 py-0.5 bg-yellow-100 text-yellow-700 text-xs rounded">
                        <AlertCircle size={12} />
                        변경사항 있음
                      </span>
                    )}
                    {existingRoutings && existingRoutings.length > 0 && !hasUnsavedChanges && (
                      <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded">
                        저장됨 ({existingRoutings.length}개 공정)
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <span>{selectedProduct.code}</span>
                    {currentDtProject && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded">
                        <Database size={12} />
                        {currentDtProject.display_name || currentDtProject.element_id}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={addRouting}
                    disabled={!routingsLoaded || !processes?.length || saveMutation.isPending}
                    className="btn btn-primary text-sm flex items-center gap-1"
                  >
                    <Plus size={14} />
                    공정 추가
                  </button>
                </div>
              </div>

              <ProductCellsEditor key={selectedProduct.id} productId={selectedProduct.id}
                onDirtyChange={setHasCellChanges} onBusyChange={setIsSavingCells} />
              {routingsFailed && <p className="text-sm text-red-600 mb-3" role="alert">
                라우팅 조회 실패
                <button className="underline ml-2" onClick={() => void refetchRoutings()}>다시 시도</button>
              </p>}
              {/* Routing Steps */}
              <fieldset disabled={saveMutation.isPending || !routingsLoaded} className="space-y-4 min-w-0">
                {routings.length === 0 ? (
                  <div className="text-center py-8 border border-dashed rounded-md text-gray-500">
                    공정을 추가하여 라우팅을 설계하세요.
                  </div>
                ) : (
                  routings.map((routing, idx) => (
                    <div key={idx} className="border rounded-lg p-4 bg-gray-50">
                      <div className="flex flex-wrap items-start gap-4">
                        {/* Sequence */}
                        <div className="w-20">
                          <label className="text-xs text-gray-500">순서</label>
                          <input
                            type="number"
                            value={routing.sequence}
                            onChange={(e) =>
                              updateRouting(idx, "sequence", parseInt(e.target.value))
                            }
                            className="w-full px-2 py-1 border rounded text-center"
                          />
                        </div>

                        {/* Process */}
                        <div className="flex-1 min-w-[160px]">
                          <label className="text-xs text-gray-500">표준공정</label>
                          <select
                            value={routing.std_process_id}
                            onChange={(e) =>
                              updateRouting(idx, "std_process_id", parseInt(e.target.value))
                            }
                            className="w-full px-2 py-1 border rounded"
                          >
                            {processes?.map((p) => (
                              <option key={p.id} value={p.id}>
                                {p.code} - {p.name}
                              </option>
                            ))}
                          </select>
                        </div>

                        {/* Setup ID */}
                        <div className="w-32 shrink-0">
                          <label className="text-xs text-gray-500">Setup ID</label>
                          <input
                            type="text"
                            value={routing.setup_id || ""}
                            onChange={(e) => updateRouting(idx, "setup_id", e.target.value || null)}
                            className="w-full px-2 py-1 border rounded"
                            placeholder="SETUP-1"
                          />
                        </div>

                        {/* Remarks */}
                        <div className="flex-1 min-w-[140px]">
                          <label className="text-xs text-gray-500">비고</label>
                          <input
                            type="text"
                            value={routing.remarks}
                            onChange={(e) => updateRouting(idx, "remarks", e.target.value)}
                            className="w-full px-2 py-1 border rounded"
                            placeholder="선택사항"
                          />
                        </div>

                        {/* Delete */}
                        <button
                          onClick={() => removeRouting(idx)}
                          className="p-2 text-red-600 hover:bg-red-50 rounded mt-4"
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>

                      <div className="mt-3 flex flex-wrap items-end gap-4">
                        <fieldset className="min-w-0">
                          <legend className="text-xs text-gray-500 mb-1">사이클 타임</legend>
                          <div className="flex flex-wrap gap-3 text-sm">
                            <label className="inline-flex items-center gap-1">
                              <input type="radio" name={`cycle-mode-${idx}`} checked={routing.cycle_time_sec == null}
                                onChange={() => updateCycleTime(idx, null)} className="accent-primary-600" />표준시간 사용
                            </label>
                            <label className="inline-flex items-center gap-1">
                              <input type="radio" name={`cycle-mode-${idx}`} checked={routing.cycle_time_sec != null}
                                onChange={() => updateCycleTime(idx, processes?.find(p => p.id === routing.std_process_id)?.cycle_time_sec ?? 0)}
                                className="accent-primary-600" />직접 입력
                            </label>
                          </div>
                        </fieldset>
                        <label className="text-xs text-gray-500 w-32">
                          사이클 타임 (초)
                          <input type="number" min={0} max={2147483647} step={1}
                            aria-label={`공정 ${routing.sequence} 사이클 타임 (초)`}
                            disabled={routing.cycle_time_sec == null}
                            value={routing.cycle_time_sec == null
                              ? processes?.find(p => p.id === routing.std_process_id)?.cycle_time_sec ?? ""
                              : Number.isFinite(routing.cycle_time_sec) ? routing.cycle_time_sec : ""}
                            onChange={e => updateCycleTime(idx, e.target.value === "" ? Number.NaN : Number(e.target.value))}
                            className="w-full px-2 py-1 border rounded text-sm text-gray-800 disabled:bg-gray-100" />
                        </label>
                        <span className="text-xs text-gray-500 pb-1">
                          표준 {processes?.find(p => p.id === routing.std_process_id)?.cycle_time_sec ?? "-"}초
                        </span>
                      </div>

                      {/* Required Machines Override */}
                      <div className="mt-3 lg:ml-24">
                        <label className="text-xs text-gray-500">
                          장비 후보 오버라이드
                          <span className="ml-1 text-gray-400">(비워두면 표준공정 기본값)</span>
                        </label>
                        <div className="flex flex-wrap gap-x-3 gap-y-1 mt-1 min-h-[28px]">
                          {machineTypes.length === 0 ? (
                            <span className="text-xs text-gray-400">등록된 장비 타입 없음</span>
                          ) : (
                            machineTypes.map((machineType) => {
                              const checked = (routing.required_machines ?? []).includes(machineType);
                              return (
                                <label key={machineType} className="flex items-center gap-1 cursor-pointer text-sm">
                                  <input
                                    type="checkbox"
                                    checked={checked}
                                    onChange={(e) => {
                                      const current = routing.required_machines ?? [];
                                      const next = e.target.checked
                                        ? [...current, machineType]
                                        : current.filter((item) => item !== machineType);
                                      updateRouting(idx, "required_machines", next.length > 0 ? next : null);
                                    }}
                                    className="accent-primary-600"
                                  />
                                  {machineType}
                                </label>
                              );
                            })
                          )}
                        </div>
                      </div>

                      {currentDtProject && (
                        <div className="mt-3 lg:ml-24 flex flex-wrap items-end gap-2">
                          <div className="min-w-[260px] flex-1">
                            <label className="text-xs text-gray-500">DT Workplan</label>
                            <select
                              value={routing.dt_workplan_id || ""}
                              onChange={(e) =>
                                updateRouting(
                                  idx,
                                  "dt_workplan_id",
                                  e.target.value ? Number(e.target.value) : null
                                )
                              }
                              className="w-full px-2 py-1 border rounded text-sm bg-white"
                            >
                              <option value="">선택 안함</option>
                              {currentDtProject.workplans.map((workplan) => (
                                <option key={workplan.id} value={workplan.id}>
                                  {"  ".repeat(workplan.level)}
                                  {workplan.display_name || workplan.workplan_id}
                                </option>
                              ))}
                            </select>
                          </div>
                          <button
                            type="button"
                            onClick={() => setNcPickerRoutingIndex(idx)}
                            disabled={!routing.dt_workplan_id}
                            className="btn btn-secondary text-sm flex items-center gap-1 disabled:opacity-50"
                          >
                            <Database size={14} />
                            DTP NC 선택
                          </button>
                        </div>
                      )}

                      {/* Files */}
                      <div className="mt-3 ml-24">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-xs text-gray-500">파일</span>
                          <button
                            onClick={() => addFile(idx)}
                            className="text-xs text-primary-600 hover:underline"
                          >
                            + 파일 추가
                          </button>
                        </div>

                        {routing.files.map((file, fIdx) => {
                          const Icon = fileTypeIcons[file.file_type as keyof typeof fileTypeIcons] || File;
                          return (
                            <div key={fIdx} className="flex items-center gap-2 mb-1">
                              <Icon size={14} className="text-gray-400" />
                              <select
                                value={file.file_type}
                                onChange={(e) => {
                                  const newRoutings = [...routings];
                                  newRoutings[idx].files[fIdx].file_type = e.target.value;
                                  updateRoutingsWithChange(newRoutings);
                                }}
                                className="px-2 py-1 border rounded text-sm w-24"
                              >
                                {Object.keys(fileTypeIcons).map((type) => (
                                  <option key={type} value={type}>
                                    {type}
                                  </option>
                                ))}
                              </select>

                              <div className="flex-1 flex items-center gap-2">
                                <input
                                  type="text"
                                  readOnly={file.source_type === "DTP"}
                                  className={`input py-1 text-sm flex-1 ${
                                    file.source_type === "DTP"
                                      ? "bg-gray-50 text-gray-600 cursor-default"
                                      : ""
                                  }`}
                                  value={file.file_path}
                                  onChange={(e) => {
                                    if (file.source_type === "DTP") return;
                                    const newRoutings = [...routings];
                                    newRoutings[idx].files[fIdx].file_path = e.target.value;
                                    newRoutings[idx].files[fIdx].original_filename = null;
                                    newRoutings[idx].files[fIdx].source_type = "LOCAL_UPLOAD";
                                    newRoutings[idx].files[fIdx].dt_file_ref_id = null;
                                    newRoutings[idx].files[fIdx].dt_file = null;
                                    updateRoutingsWithChange(newRoutings);
                                  }}
                                  placeholder="/uploads/nc/..."
                                />
                                {file.source_type === "DTP" && (
                                  <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded">
                                    <Database size={12} />
                                    DTP
                                  </span>
                                )}
                                {file.original_filename && (
                                  <span className="text-xs text-gray-500 truncate max-w-[160px]" title={file.original_filename}>
                                    {file.original_filename}
                                  </span>
                                )}
                                {file.source_type !== "DTP" && (
                                  <label className={`cursor-pointer ${isUploading ? 'opacity-50' : 'hover:bg-gray-100'} p-1.5 border rounded bg-white text-gray-600 transition-colors flex items-center gap-1`}>
                                    <Upload size={14} />
                                    <span className="text-xs font-medium">업로드</span>
                                    <input
                                      type="file"
                                      className="hidden"
                                      disabled={isUploading}
                                      onChange={(e) => handleFileUpload(idx, fIdx, e)}
                                    />
                                  </label>
                                )}
                              </div>

                              {file.file_type === "NC" && machineTypes.length > 0 && (
                                <div className="flex flex-wrap gap-x-2 gap-y-1 max-w-[260px]">
                                  {machineTypes.map((machineType) => {
                                    const checked = (file.compatible_machines ?? []).includes(machineType);
                                    return (
                                      <label key={machineType} className="flex items-center gap-1 text-xs cursor-pointer">
                                        <input
                                          type="checkbox"
                                          checked={checked}
                                          onChange={(e) => {
                                            const newRoutings = [...routings];
                                            const current = newRoutings[idx].files[fIdx].compatible_machines ?? [];
                                            const next = e.target.checked
                                              ? [...current, machineType]
                                              : current.filter((item) => item !== machineType);
                                            newRoutings[idx].files[fIdx].compatible_machines = next.length > 0 ? next : null;
                                            updateRoutingsWithChange(newRoutings);
                                          }}
                                          className="accent-primary-600"
                                        />
                                        {machineType}
                                      </label>
                                    );
                                  })}
                                </div>
                              )}

                              <button
                                onClick={() => removeFile(idx, fIdx)}
                                className="p-1 text-red-500 hover:bg-red-50 rounded"
                              >
                                <Trash2 size={14} />
                              </button>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ))
                )}
              </fieldset>
            </div>
          ) : (
            <div className="card text-center py-12 text-gray-500">
              왼쪽에서 제품을 선택하여 라우팅을 설계하세요.
            </div>
          )}
        </div>
      </div>

      {ncPickerRoutingIndex !== null && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[80vh] overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b">
              <div>
                <h2 className="text-lg font-semibold">DTP NC 선택</h2>
                <p className="text-sm text-gray-500">
                  {pickerWorkplan?.display_name || pickerWorkplan?.workplan_id}
                </p>
              </div>
              <button
                onClick={() => setNcPickerRoutingIndex(null)}
                className="p-2 hover:bg-gray-100 rounded"
              >
                <X size={20} />
              </button>
            </div>
            <div className="p-4 overflow-y-auto max-h-[60vh]">
              {!pickerWorkplan ? (
                <div className="text-center py-8 text-gray-500">DT Workplan을 먼저 선택하세요.</div>
              ) : isFetchingDtNcFiles ? (
                <div className="text-center py-8 text-gray-500">NC 파일 조회 중...</div>
              ) : dtNcFiles && dtNcFiles.length > 0 ? (
                <div className="space-y-2">
                  {dtNcFiles.map((file) => (
                    <button
                      key={file.id}
                      type="button"
                      onClick={() => addDtpNcFile(file)}
                      className="w-full text-left border rounded-md p-3 hover:bg-primary-50"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div className="min-w-0">
                          <div className="font-medium truncate">
                            {file.display_name || file.path.split("/").pop()}
                          </div>
                          <div className="text-xs text-gray-500 truncate">{file.path}</div>
                        </div>
                        <span className="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-600">
                          {file.workplan_id || "NC"}
                        </span>
                      </div>
                    </button>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">선택한 Workplan의 NC 파일이 없습니다.</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
