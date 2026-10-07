"use client";

/**
 * RoutingRulesEditor — list of (label, when, thenJson) routing rules.
 *
 * V1 (M3) UX: textarea-based, no GUI builder.
 *   - Click "+ Add rule" to append a new rule with default label
 *   - Each row: label (small input) + when (textarea) + thenJson (textarea)
 *   - "✕" removes a rule
 *
 * V2 (later): visual condition builder with operator dropdowns.
 *
 * Design Ref: §5.4 Page UI Checklist > Parameter Panel (Routing rules editor)
 */

import { Plus, X } from "lucide-react";

import type { RoutingValue } from "@/types/scenario";

interface Props {
  value: RoutingValue[];
  onChange: (next: RoutingValue[]) => void;
}

export function RoutingRulesEditor({ value, onChange }: Props) {
  const addRule = () => {
    onChange([
      ...value,
      { label: `Rule ${value.length + 1}`, when: "", thenJson: "[]" },
    ]);
  };

  const updateRule = (i: number, patch: Partial<RoutingValue>) => {
    onChange(value.map((r, idx) => (idx === i ? { ...r, ...patch } : r)));
  };

  const removeRule = (i: number) => {
    onChange(value.filter((_, idx) => idx !== i));
  };

  return (
    <div className="space-y-2">
      {value.length === 0 && (
        <div className="rounded border border-dashed border-gray-300 px-3 py-2 text-center text-xs text-gray-500">
          (no routing rules — output flows linearly)
        </div>
      )}
      {value.map((r, i) => (
        <div
          key={i}
          className="rounded border border-gray-200 bg-gray-50 p-2"
        >
          <div className="flex items-center gap-2">
            <span className="rounded bg-gray-200 px-1.5 py-0.5 font-mono text-[10px] text-gray-700">
              {i + 1}
            </span>
            <input
              type="text"
              value={r.label}
              onChange={(e) => updateRule(i, { label: e.target.value })}
              placeholder="label"
              className="flex-1 rounded border border-gray-300 px-2 py-0.5 text-xs focus:border-blue-500 focus:outline-none"
            />
            <button
              onClick={() => removeRule(i)}
              className="rounded p-0.5 text-red-500 hover:bg-red-50"
              title="삭제"
            >
              <X size={14} />
            </button>
          </div>
          <div className="mt-1.5">
            <label className="block text-[10px] font-medium text-gray-600">
              when
            </label>
            <textarea
              rows={2}
              value={r.when}
              onChange={(e) => updateRule(i, { when: e.target.value })}
              placeholder='예: {{var.status}} == "OK"  (empty -> default branch)'
              className="w-full rounded border border-gray-300 px-2 py-1 font-mono text-xs focus:border-blue-500 focus:outline-none"
            />
          </div>
          <div className="mt-1.5">
            <label className="block text-[10px] font-medium text-gray-600">
              then (JSON array)
            </label>
            <textarea
              rows={3}
              value={r.thenJson}
              onChange={(e) => updateRule(i, { thenJson: e.target.value })}
              placeholder='[{"next": "2-1"}]'
              className="w-full rounded border border-gray-300 px-2 py-1 font-mono text-xs focus:border-blue-500 focus:outline-none"
            />
          </div>
        </div>
      ))}
      <button
        onClick={addRule}
        className="inline-flex items-center gap-1 rounded border border-dashed border-gray-400 px-2 py-1 text-xs text-gray-700 hover:border-blue-500 hover:text-blue-700"
      >
        <Plus size={14} /> Add rule
      </button>
    </div>
  );
}
