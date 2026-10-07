"use client";

/**
 * StickyParameterForm — edit StickyNoteData (text, color, size).
 *
 * Design Ref: §5.4 Page UI Checklist > Parameter Panel (StickyParameterForm)
 */

import type { StickyColor, StickyNoteData } from "@/types/scenario";

const COLOR_SWATCHES: Array<{ key: StickyColor; cls: string; label: string }> =
  [
    { key: "yellow", cls: "bg-yellow-300", label: "Yellow" },
    { key: "blue", cls: "bg-blue-300", label: "Blue" },
    { key: "pink", cls: "bg-pink-300", label: "Pink" },
    { key: "green", cls: "bg-green-300", label: "Green" },
  ];

interface Props {
  data: StickyNoteData;
  onChange: (patch: Partial<StickyNoteData>) => void;
}

export function StickyParameterForm({ data, onChange }: Props) {
  return (
    <div className="space-y-3">
      <div>
        <label className="mb-1 block text-[11px] font-semibold uppercase tracking-wider text-gray-700">
          Text
        </label>
        <textarea
          rows={6}
          value={data.text}
          onChange={(e) => onChange({ text: e.target.value })}
          className="w-full rounded border border-gray-300 px-2 py-1 text-xs focus:border-blue-500 focus:outline-none"
        />
      </div>

      <div>
        <label className="mb-1 block text-[11px] font-semibold uppercase tracking-wider text-gray-700">
          Color
        </label>
        <div className="flex gap-2">
          {COLOR_SWATCHES.map((s) => (
            <button
              key={s.key}
              onClick={() => onChange({ color: s.key })}
              className={`h-7 w-7 rounded border-2 ${s.cls} ${
                data.color === s.key
                  ? "border-gray-900 ring-2 ring-blue-400"
                  : "border-gray-300"
              }`}
              title={s.label}
            />
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className="mb-1 block text-[11px] font-semibold uppercase tracking-wider text-gray-700">
            Width
          </label>
          <input
            type="number"
            min={120}
            max={1000}
            value={data.width}
            onChange={(e) =>
              onChange({ width: Number(e.target.value) || 240 })
            }
            className="w-full rounded border border-gray-300 px-2 py-1 text-xs focus:border-blue-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold uppercase tracking-wider text-gray-700">
            Height
          </label>
          <input
            type="number"
            min={80}
            max={1000}
            value={data.height}
            onChange={(e) =>
              onChange({ height: Number(e.target.value) || 180 })
            }
            className="w-full rounded border border-gray-300 px-2 py-1 text-xs focus:border-blue-500 focus:outline-none"
          />
        </div>
      </div>
    </div>
  );
}
