"use client";

/**
 * ScenarioStepNode — main building block of the workflow.
 *
 * Visual: white card with green accent (step), input handle on left, one
 * output handle per routing rule on the right (or 1 default if no routing).
 *
 * Design Ref: §5.4 Page UI Checklist > Nodes (ScenarioStep)
 *             §3 Data Model (ScenarioStepData.routing.values[])
 */

import { Handle, Position, type NodeProps } from "reactflow";
import { Activity } from "lucide-react";

import type { ScenarioStepData } from "@/types/scenario";

import { NodeBadge } from "./NodeBadge";
import { NodeStatusIndicator } from "./NodeStatusIndicator";

export function ScenarioStepNode({
  id,
  data,
  selected,
}: NodeProps<ScenarioStepData>) {
  const routes = data.routing?.values ?? [];
  // At least 1 output handle; multiple if routing branches exist.
  const outputCount = Math.max(1, routes.length);

  return (
    <div
      className={`relative min-w-[220px] rounded-lg border-2 bg-white shadow-sm transition-shadow ${
        selected
          ? "border-green-500 shadow-md"
          : "border-gray-300 hover:shadow-md"
      }`}
    >
      <NodeStatusIndicator nodeId={id} />
      <Handle
        type="target"
        position={Position.Left}
        id="in"
        className="!h-2.5 !w-2.5 !bg-green-500"
      />
      <div className="flex items-center gap-2 border-b border-gray-100 bg-gray-50 px-3 py-2">
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-green-100 text-green-700">
          <Activity size={14} />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5">
            <span className="font-mono text-[11px] font-semibold text-gray-700">
              {data.stepId}
            </span>
            <span className="truncate text-sm font-semibold text-gray-900">
              {data.stepName || "(no name)"}
            </span>
          </div>
          {data.action ? (
            <div className="mt-0.5 truncate font-mono text-[10px] text-gray-500">
              {data.action}
            </div>
          ) : (
            <div className="mt-0.5 text-[10px] italic text-gray-400">
              (no action)
            </div>
          )}
        </div>
        <NodeBadge nodeId={id} errors={data.errors} />
      </div>
      {routes.length > 0 && (
        <div className="px-3 py-1.5">
          <div className="text-[10px] font-medium uppercase text-gray-500">
            Routing ({routes.length})
          </div>
          <ul className="mt-0.5 space-y-0.5">
            {routes.slice(0, 3).map((r, i) => (
              <li
                key={i}
                className="truncate font-mono text-[10px] text-gray-600"
                title={r.when || "default"}
              >
                {r.label || r.when || "default"}
              </li>
            ))}
            {routes.length > 3 && (
              <li className="text-[10px] text-gray-400">
                +{routes.length - 3} more
              </li>
            )}
          </ul>
        </div>
      )}
      {/* Output handles — one per route (or 1 default). */}
      {Array.from({ length: outputCount }).map((_, i) => (
        <Handle
          key={i}
          type="source"
          position={Position.Right}
          id={String(i)}
          // Distribute handles vertically across the right edge.
          style={{ top: `${((i + 1) / (outputCount + 1)) * 100}%` }}
          className="!h-2.5 !w-2.5 !bg-green-500"
        />
      ))}
    </div>
  );
}
