"use client";

import { useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Edit2, Link2, Plus, RefreshCw, Save, Trash2, Unlink, X } from "lucide-react";
import { isAxiosError } from "axios";
import { cellService } from "@/services/cell";
import type { Cell, CellInput } from "@/services/cell";
import { equipmentService } from "@/services/equipment";
import { useAuthStore } from "@/stores/authStore";
import { getErrorMessage } from "@/lib/errorHandler";
import { getEquipmentSourceLabel, isVirtualEquipment } from "@/utils/equipment";
import type { Equipment } from "@/types";

const emptyForm: CellInput = { code: "", name: "", location: "" };

function errorText(error: unknown): string {
  if (isAxiosError(error) && typeof error.response?.data?.detail === "string") {
    return error.response.data.detail;
  }
  return getErrorMessage(error);
}

export default function CellsPage() {
  const queryClient = useQueryClient();
  const isAdmin = useAuthStore((state) => state.user?.role === "ADMIN");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [tab, setTab] = useState<"assigned" | "available">("assigned");
  const [search, setSearch] = useState("");
  const [source, setSource] = useState("all");
  const [includeDeleted, setIncludeDeleted] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [editing, setEditing] = useState<Cell | null>(null);
  const [form, setForm] = useState<CellInput>(emptyForm);
  const dialog = useRef<HTMLDialogElement>(null);
  const cellsQuery = useQuery({ queryKey: ["cells"], queryFn: cellService.getAll });
  const equipmentQuery = useQuery({
    queryKey: ["equipments", "cell-management"],
    queryFn: () => equipmentService.getAll(true),
  });
  const cells = cellsQuery.data ?? [];
  const equipments = equipmentQuery.data ?? [];
  const selected = cells.find((cell) => cell.id === selectedId) ?? cells[0];
  const cellLabel = (id: number | null) => {
    const cell = cells.find((item) => item.id === id);
    return cell ? `${cell.code} · ${cell.name}` : id === null ? "미할당" : `Cell #${id}`;
  };
  const refresh = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["cells"] }),
      queryClient.invalidateQueries({ queryKey: ["equipments"] }),
    ]);
  };
  const save = useMutation({
    mutationFn: () => editing ? cellService.update(editing.id, form) : cellService.create(form),
    onSuccess: async (cell) => {
      setSelectedId(cell.id);
      dialog.current?.close();
      setError("");
      setMessage("Cell 정보가 저장되었습니다.");
      await refresh();
    },
    onError: (cause) => setError(errorText(cause)),
  });
  const assignment = useMutation({
    mutationFn: ({ equipment, target }: { equipment: Equipment; target: number | null }) =>
      cellService.assign(equipment, target),
    onSuccess: async () => {
      setMessage("설비 소속이 저장되었습니다.");
      setError("");
      await refresh();
    },
    onError: async (cause) => {
      setError(errorText(cause));
      await refresh();
    },
  });
  const remove = useMutation({
    mutationFn: cellService.delete,
    onSuccess: async () => {
      setSelectedId(null);
      setMessage("Cell이 삭제되었습니다.");
      setError("");
      await refresh();
    },
    onError: (cause) => setError(errorText(cause)),
  });
  const busy = save.isPending || assignment.isPending || remove.isPending;
  const openForm = (cell: Cell | null) => {
    setEditing(cell);
    setForm(cell ? { code: cell.code, name: cell.name, location: cell.location } : emptyForm);
    setError("");
    setMessage("");
    dialog.current?.showModal();
  };
  const assign = (equipment: Equipment, target: number | null) => {
    if (equipment.cell_id !== null && !window.confirm(
      target === null
        ? `${equipment.eq_name}의 ${cellLabel(equipment.cell_id)} 소속을 해제하시겠습니까?`
        : `${equipment.eq_name}을 ${cellLabel(equipment.cell_id)}에서 ${cellLabel(target)}로 이동하시겠습니까?`
    )) return;
    setError("");
    setMessage("");
    assignment.mutate({ equipment, target });
  };
  const rows = equipments.filter((equipment) => {
    if (!selected) return false;
    if (equipment.is_deleted && (!includeDeleted || tab === "available")) return false;
    if ((equipment.cell_id === selected.id) !== (tab === "assigned")) return false;
    if (source === "physical" && isVirtualEquipment(equipment)) return false;
    if (source === "virtual" && !isVirtualEquipment(equipment)) return false;
    return `${equipment.eq_code} ${equipment.eq_name} ${equipment.equipment_type}`
      .toLowerCase().includes(search.toLowerCase());
  });
  const loading = cellsQuery.isLoading || equipmentQuery.isLoading;
  const loadError = cellsQuery.error || equipmentQuery.error;

  return (
    <div className="space-y-6 min-w-0">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold">Cell 관리</h1>
        <div className="flex items-center gap-2">
          <button type="button" title="새로고침" aria-label="새로고침" onClick={() => void refresh()}
            disabled={busy} className="p-2 border rounded hover:bg-gray-50 disabled:opacity-50"><RefreshCw size={18} /></button>
          {isAdmin && <button type="button" onClick={() => openForm(null)} disabled={busy}
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50"><Plus size={18} />Cell 등록</button>}
        </div>
      </header>
      {message && <p role="status" className="text-sm text-green-700">{message}</p>}
      {(error || loadError) && !dialog.current?.open && <p role="alert" className="text-sm text-red-600">{error || errorText(loadError)}</p>}
      {loading ? <p className="py-8 text-gray-500" role="status">불러오는 중...</p> : !loadError && <>
        <section className="flex flex-wrap items-end gap-3 border-b pb-5">
          <label className="flex flex-col gap-1 text-sm w-full sm:w-80">
            <span className="font-medium">Cell</span>
            <select aria-label="Cell" value={selected?.id ?? ""} onChange={(event) => { setSelectedId(Number(event.target.value)); setError(""); setMessage(""); }}
              className="border rounded px-3 py-2 w-full" disabled={busy || !cells.length}>
              {!cells.length && <option value="">등록된 Cell 없음</option>}
              {cells.map((cell) => <option key={cell.id} value={cell.id}>{cell.code} · {cell.name}</option>)}
            </select>
          </label>
          {selected && <>
            <p className="py-2 text-sm text-gray-500 break-all">{selected.location || "위치 미등록"}</p>
            {isAdmin && <div className="flex gap-1">
              <button type="button" title="Cell 수정" aria-label="Cell 수정" disabled={busy} onClick={() => openForm(selected)} className="p-2 text-primary-600 hover:bg-primary-50 rounded"><Edit2 size={18} /></button>
              <button type="button" title="Cell 삭제" aria-label="Cell 삭제" disabled={busy} onClick={() => {
                if (window.confirm(`${selected.code}을 삭제하시겠습니까?`)) remove.mutate(selected.id);
              }} className="p-2 text-red-600 hover:bg-red-50 rounded"><Trash2 size={18} /></button>
            </div>}
          </>}
        </section>
        {selected && <section className="space-y-4">
          <div className="flex border-b" role="tablist" aria-label="설비 목록">
            {([ ["assigned", "소속 설비"], ["available", "설비 할당"] ] as const).map(([value, label]) =>
              <button key={value} type="button" role="tab" aria-selected={tab === value} onClick={() => setTab(value)}
                className={`px-4 py-3 text-sm border-b-2 ${tab === value ? "border-primary-600 text-primary-600 font-medium" : "border-transparent text-gray-500"}`}>{label}</button>)}
          </div>
          <div className="flex flex-wrap gap-3 items-center">
            <input aria-label="설비 검색" placeholder="설비 코드, 이름, 종류 검색" value={search} onChange={(event) => setSearch(event.target.value)} className="border rounded px-3 py-2 text-sm w-full sm:w-72" />
            <select aria-label="설비 구분" value={source} onChange={(event) => setSource(event.target.value)} className="border rounded px-3 py-2 text-sm">
              <option value="all">전체 설비</option><option value="physical">실장비</option><option value="virtual">가상장비</option>
            </select>
            {tab === "assigned" && <label className="flex gap-2 items-center text-sm"><input type="checkbox" checked={includeDeleted} onChange={(event) => setIncludeDeleted(event.target.checked)} />삭제 설비 포함</label>}
            <span className="text-sm text-gray-500">{rows.length}대</span>
          </div>
          <div className="overflow-x-auto border rounded-lg bg-white">
            <table className="w-full text-sm text-left min-w-[720px]">
              <thead className="bg-gray-50 text-gray-600"><tr>{["설비 코드", "설비명", "종류", "구분", "소속 Cell", "관리"].map((label) => <th key={label} className="px-4 py-3 font-medium">{label}</th>)}</tr></thead>
              <tbody className="divide-y">
                {rows.map((equipment) => <tr key={equipment.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono break-all max-w-[240px]">{equipment.eq_code}</td>
                  <td className="px-4 py-3 break-all max-w-[200px]">{equipment.eq_name}</td>
                  <td className="px-4 py-3">{equipment.equipment_type}</td>
                  <td className="px-4 py-3"><span className={`text-xs rounded px-2 py-1 whitespace-nowrap ${isVirtualEquipment(equipment) ? "bg-amber-50 text-amber-800" : "bg-green-50 text-green-800"}`}>{getEquipmentSourceLabel(equipment)}</span>{equipment.is_deleted && <span className="block text-red-600 text-xs mt-1">삭제됨</span>}</td>
                  <td className="px-4 py-3 break-all max-w-[220px]">{cellLabel(equipment.cell_id)}</td>
                  <td className="px-4 py-3">{isAdmin && <button type="button" disabled={busy}
                    title={tab === "assigned" ? "소속 해제" : equipment.cell_id === null ? "선택 Cell에 할당" : "선택 Cell로 이동"}
                    aria-label={`${equipment.eq_name} ${tab === "assigned" ? "소속 해제" : "할당"}`}
                    onClick={() => assign(equipment, tab === "assigned" ? null : selected.id)}
                    className="p-2 rounded text-primary-600 hover:bg-primary-50 disabled:opacity-50">{tab === "assigned" ? <Unlink size={18} /> : <Link2 size={18} />}</button>}</td>
                </tr>)}
                {!rows.length && <tr><td colSpan={6} className="text-center py-12 text-gray-500">해당 설비가 없습니다.</td></tr>}
              </tbody>
            </table>
          </div>
        </section>}
      </>}
      <dialog ref={dialog} aria-labelledby="cell-form-title" className="rounded-lg p-6 w-[calc(100%-2rem)] max-w-lg backdrop:bg-black/50" onCancel={(event) => { if (save.isPending) event.preventDefault(); }}>
        <form onSubmit={(event) => { event.preventDefault(); setError(""); save.mutate(); }} className="space-y-4">
          <div className="flex items-center justify-between"><h2 id="cell-form-title" className="text-lg font-semibold">{editing ? "Cell 수정" : "Cell 등록"}</h2><button type="button" aria-label="닫기" title="닫기" disabled={save.isPending} onClick={() => dialog.current?.close()} className="p-2"><X size={20} /></button></div>
          {error && <p role="alert" className="text-sm text-red-600">{error}</p>}
          <label className="block text-sm">Cell 코드<input autoFocus required maxLength={20} value={form.code} onChange={(event) => setForm({ ...form, code: event.target.value })} className="mt-1 w-full border rounded px-3 py-2" /></label>
          <label className="block text-sm">Cell 이름<input required maxLength={100} value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} className="mt-1 w-full border rounded px-3 py-2" /></label>
          <label className="block text-sm">위치<input maxLength={100} value={form.location ?? ""} onChange={(event) => setForm({ ...form, location: event.target.value })} className="mt-1 w-full border rounded px-3 py-2" /></label>
          <div className="flex justify-end gap-2 pt-2"><button type="button" disabled={save.isPending} onClick={() => dialog.current?.close()} className="border rounded px-4 py-2">취소</button><button type="submit" disabled={save.isPending} className="flex items-center gap-2 bg-primary-600 text-white rounded px-4 py-2 disabled:opacity-50"><Save size={16} />{save.isPending ? "저장 중..." : "저장"}</button></div>
        </form>
      </dialog>
    </div>
  );
}
