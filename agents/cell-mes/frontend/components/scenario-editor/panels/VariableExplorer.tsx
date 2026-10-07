"use client";

/**
 * VariableExplorer — collapsible left side panel listing all available
 * expression tokens for the current scenario.
 *
 * Categories:
 *   - acquire — {{acq.main/sub1/sub2/sub3}}
 *   - assets — from scenarioConfig
 *   - step results — every defined ScenarioStep
 *   - common variables — res / var.x
 *   - functions — built-ins from expressionFunctions.ts
 *
 * V1 (M7): read-only browser. Click an entry to copy to clipboard.
 *
 * Design Ref: §11 M7 Module, §5.4 Page UI Checklist (Variable Explorer)
 */

import { useMemo, useState } from "react";
import type { Node } from "reactflow";
import { ChevronRight, ChevronDown, Copy } from "lucide-react";

import type { EditorNodeData } from "@/types/scenario";
import { useExpressionSuggestions } from "../expression/useExpressionSuggestions";

interface Props {
  nodes: Node<EditorNodeData>[];
}

export function VariableExplorer({ nodes }: Props) {
  const [open, setOpen] = useState(false);
  const suggestions = useExpressionSuggestions(nodes);

  const grouped = useMemo(() => {
    const map = new Map<string, typeof suggestions>();
    for (const s of suggestions) {
      const key = s.category;
      if (!map.has(key)) map.set(key, []);
      map.get(key)!.push(s);
    }
    return map;
  }, [suggestions]);

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        title="변수 탐색기 열기"
        className="absolute left-2 top-2 z-20 inline-flex items-center gap-1 rounded border border-gray-300 bg-white px-2 py-1 text-[11px] shadow-sm hover:bg-gray-50"
      >
        <ChevronRight size={12} />
        변수
      </button>
    );
  }

  return (
    <aside className="absolute left-0 top-0 z-20 flex h-full w-64 flex-col border-r border-gray-200 bg-white shadow-md">
      <div className="flex items-center justify-between border-b border-gray-200 px-3 py-2">
        <div className="text-[11px] font-semibold uppercase tracking-wider text-gray-700">
          변수 탐색기
        </div>
        <button
          onClick={() => setOpen(false)}
          className="rounded p-1 text-gray-500 hover:bg-gray-100"
          title="닫기"
        >
          <ChevronDown size={12} />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-2 text-xs">
        {Array.from(grouped.entries()).map(([cat, items]) => (
          <div key={cat} className="mb-2">
            <div className="mb-0.5 text-[10px] font-semibold uppercase tracking-wider text-gray-500">
              {cat}
            </div>
            <ul className="space-y-0.5">
              {items.map((s) => (
                <li key={s.insert}>
                  <button
                    onClick={() => {
                      navigator.clipboard
                        ?.writeText(s.insert)
                        .catch(() => {});
                    }}
                    className="group flex w-full items-start justify-between gap-2 rounded px-1.5 py-0.5 text-left hover:bg-gray-100"
                    title="클릭하여 클립보드 복사"
                  >
                    <span className="min-w-0 flex-1">
                      <span className="block truncate font-mono text-[11px] text-gray-800">
                        {s.label}
                      </span>
                      {s.description && (
                        <span className="block truncate text-[10px] text-gray-500">
                          {s.description}
                        </span>
                      )}
                    </span>
                    <Copy
                      size={10}
                      className="mt-0.5 flex-shrink-0 text-gray-300 group-hover:text-gray-600"
                    />
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </aside>
  );
}
