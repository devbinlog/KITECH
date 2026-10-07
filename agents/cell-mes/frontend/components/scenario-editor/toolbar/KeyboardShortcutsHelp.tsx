"use client";

/**
 * KeyboardShortcutsHelp — modal cheat sheet for the editor.
 *
 * Toggle with `?` key (and the toolbar `?` button). Lists all shortcuts the
 * editor binds, grouped by category.
 *
 * Design Ref: §5.4 Page UI Checklist > Keyboard shortcuts table
 */

import { X } from "lucide-react";

interface Props {
  open: boolean;
  onClose: () => void;
}

const SECTIONS: Array<{ title: string; rows: Array<[string, string]> }> = [
  {
    title: "편집",
    rows: [
      ["Ctrl/Cmd + Z", "Undo"],
      ["Ctrl/Cmd + Y / Shift+Z", "Redo"],
      ["Ctrl/Cmd + C", "Copy 선택"],
      ["Ctrl/Cmd + X", "Cut 선택"],
      ["Ctrl/Cmd + V", "Paste"],
      ["Ctrl/Cmd + D", "Duplicate"],
      ["Delete / Backspace", "Bulk delete 선택"],
    ],
  },
  {
    title: "탐색",
    rows: [
      ["Ctrl/Cmd + K", "노드 검색 / 신규 step 추가"],
      ["Space + drag", "Pan 이동"],
      ["휠", "Zoom in/out"],
      ["Esc", "선택 해제 / 모달 닫기"],
    ],
  },
  {
    title: "저장",
    rows: [
      ["Ctrl/Cmd + S", "수동 저장"],
      ["Auto", "수정 후 2초 디바운스 저장"],
    ],
  },
  {
    title: "기타",
    rows: [["?", "이 단축키 목록 토글"]],
  },
];

export function KeyboardShortcutsHelp({ open, onClose }: Props) {
  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      onClick={onClose}
    >
      <div
        className="w-[520px] max-w-[90vw] overflow-hidden rounded-lg bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
          <h2 className="text-sm font-semibold text-gray-900">
            키보드 단축키
          </h2>
          <button
            onClick={onClose}
            className="rounded p-1 text-gray-500 hover:bg-gray-100"
            title="닫기"
          >
            <X size={16} />
          </button>
        </div>
        <div className="max-h-[70vh] overflow-y-auto p-4">
          {SECTIONS.map((s) => (
            <div key={s.title} className="mb-4 last:mb-0">
              <h3 className="mb-1.5 text-[11px] font-semibold uppercase tracking-wider text-gray-500">
                {s.title}
              </h3>
              <table className="w-full">
                <tbody>
                  {s.rows.map(([keys, desc]) => (
                    <tr key={keys}>
                      <td className="py-0.5 pr-3">
                        <kbd className="rounded border border-gray-300 bg-gray-50 px-1.5 py-0.5 font-mono text-[11px] text-gray-700">
                          {keys}
                        </kbd>
                      </td>
                      <td className="text-xs text-gray-700">{desc}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
