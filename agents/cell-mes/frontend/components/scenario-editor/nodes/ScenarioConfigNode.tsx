"use client";

/**
 * ScenarioConfigNode — global scenario context (assets, base URL, AAS path).
 *
 * Visual: indigo card with cog icon, single input + single output, assets
 * list rendered inline as chips (max 4 visible, "+N more" otherwise).
 *
 * Design Ref: §5.4 Page UI Checklist > Nodes (ScenarioConfig)
 */

import { Handle, Position, type NodeProps } from "reactflow";
import { Settings } from "lucide-react";

import type { ScenarioConfigData } from "@/types/scenario";

export function ScenarioConfigNode({
  data,
  selected,
}: NodeProps<ScenarioConfigData>) {
  const visibleAssets = data.assets.slice(0, 4);
  const moreAssets = data.assets.length - visibleAssets.length;

  return (
    <div
      className={`min-w-[220px] rounded-lg border-2 bg-white shadow-sm transition-shadow ${
        selected
          ? "border-indigo-500 shadow-md"
          : "border-indigo-200 hover:shadow-md"
      }`}
    >
      <Handle
        type="target"
        position={Position.Left}
        id="in"
        className="!h-2.5 !w-2.5 !bg-indigo-500"
      />
      <div className="flex items-center gap-2 border-b border-indigo-100 bg-indigo-50 px-3 py-2">
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-indigo-100 text-indigo-700">
          <Settings size={14} />
        </div>
        <div className="flex flex-col">
          <div className="text-[10px] font-medium uppercase tracking-wider text-indigo-700">
            Scenario Config
          </div>
          <div className="truncate text-sm font-semibold text-gray-900">
            {data.scenarioName || "(no name)"}
          </div>
        </div>
      </div>
      <div className="px-3 py-2">
        <div className="text-[10px] font-medium uppercase text-gray-500">
          Assets ({data.assets.length})
        </div>
        <div className="mt-1 flex flex-wrap gap-1">
          {visibleAssets.map((a) => (
            <span
              key={a.id}
              className="rounded-full bg-indigo-100 px-2 py-0.5 text-xs font-medium text-indigo-800"
              title={a.name}
            >
              {a.id}
            </span>
          ))}
          {moreAssets > 0 && (
            <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
              +{moreAssets} more
            </span>
          )}
          {data.assets.length === 0 && (
            <span className="text-xs italic text-gray-400">(empty)</span>
          )}
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Right}
        id="0"
        className="!h-2.5 !w-2.5 !bg-indigo-500"
      />
    </div>
  );
}
