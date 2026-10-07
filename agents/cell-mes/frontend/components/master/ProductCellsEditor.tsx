"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Save } from "lucide-react";
import { cellService } from "@/services/cell";
import { productService } from "@/services/master";

export default function ProductCellsEditor({ productId, onDirtyChange, onBusyChange }: {
  productId: number;
  onDirtyChange: (dirty: boolean) => void;
  onBusyChange: (busy: boolean) => void;
}) {
  const queryClient = useQueryClient();
  const [draft, setDraft] = useState<number[] | null>(null);
  const cells = useQuery({ queryKey: ["cells"], queryFn: cellService.getAll });
  const membership = useQuery({
    queryKey: ["product-cells", productId],
    queryFn: () => productService.getCells(productId),
  });
  const selected = draft ?? membership.data?.cell_ids ?? [];
  const dirty = draft !== null;
  const save = useMutation({
    mutationFn: (ids: number[]) => productService.saveCells(productId, ids),
    onSuccess: (data) => {
      queryClient.setQueryData(["product-cells", productId], data);
      setDraft(null);
    },
  });
  useEffect(() => { onDirtyChange(dirty); }, [dirty, onDirtyChange]);
  useEffect(() => { onBusyChange(save.isPending); }, [save.isPending, onBusyChange]);

  return (
    <section className="border-y py-4 mb-4" aria-label="제품 허용 Cell">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <h3 className="text-sm font-semibold text-gray-800">제품 허용 Cell</h3>
        <button type="button" onClick={() => save.mutate(selected)}
          disabled={!dirty || save.isPending || !cells.isSuccess || !membership.isSuccess}
          className="btn btn-secondary text-sm inline-flex items-center gap-1">
          <Save size={14} />{save.isPending ? "저장 중..." : "Cell 저장"}
        </button>
      </div>
      {cells.isError || membership.isError ? (
        <div className="text-sm text-red-600" role="alert">
          Cell 정보를 불러오지 못했습니다.
          <button type="button" className="ml-2 underline" onClick={() => {
            void cells.refetch(); void membership.refetch();
          }}>다시 시도</button>
        </div>
      ) : !cells.isSuccess || !membership.isSuccess ? (
        <p className="text-sm text-gray-500">Cell 조회 중...</p>
      ) : (
        <>
          <div className="flex flex-wrap gap-x-5 gap-y-2">
            {cells.data.map((cell) => (
              <label key={cell.id} className="inline-flex items-start gap-2 text-sm min-w-0 break-all">
                <input type="checkbox" className="accent-primary-600 mt-1 shrink-0"
                  checked={selected.includes(cell.id)} disabled={save.isPending}
                  onChange={(event) => {
                    save.reset();
                    setDraft(event.target.checked ? [...selected, cell.id] : selected.filter(id => id !== cell.id));
                  }} />
                <span>{cell.name} <span className="text-gray-500">({cell.code})</span></span>
              </label>
            ))}
          </div>
          {!cells.data.length && <p className="text-sm text-gray-500">등록된 Cell 없음</p>}
          {!selected.length && <p className="text-sm text-amber-700 mt-2">허용 Cell 미지정</p>}
          {dirty && <p className="text-xs text-amber-700 mt-2">저장되지 않은 Cell 변경사항</p>}
          {save.isSuccess && !dirty && <p role="status" className="text-xs text-green-700 mt-2">Cell 저장 완료</p>}
        </>
      )}
      {save.isError && <p role="alert" className="text-sm text-red-600 mt-2">
        Cell 저장 실패: {(save.error as any).response?.data?.detail || save.error.message}
      </p>}
    </section>
  );
}
