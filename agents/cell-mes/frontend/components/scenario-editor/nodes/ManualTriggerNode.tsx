"use client";

/**
 * ManualTriggerNode — n8n-style starter node.
 *
 * Visual: gray rounded card with lightning icon, single output handle.
 * Always sits at the head of the workflow; doesn't take input.
 *
 * Design Ref: §5.4 Page UI Checklist > Nodes (ManualTrigger)
 */

import { Handle, Position, type NodeProps } from "reactflow";
import { Zap } from "lucide-react";

import type { ManualTriggerData } from "@/types/scenario";

export function ManualTriggerNode({ selected }: NodeProps<ManualTriggerData>) {
  return (
    <div
      className={`flex items-center gap-2 rounded-lg border-2 bg-white px-3 py-2 shadow-sm transition-shadow ${
        selected
          ? "border-blue-500 shadow-md"
          : "border-gray-300 hover:shadow-md"
      }`}
    >
      <div className="flex h-8 w-8 items-center justify-center rounded-md bg-gray-100 text-gray-700">
        <Zap size={16} />
      </div>
      <div>
        <div className="text-xs font-medium text-gray-700">트리거</div>
        <div className="text-sm font-semibold text-gray-900">Manual Trigger</div>
      </div>
      <Handle
        type="source"
        position={Position.Right}
        id="0"
        className="!h-2.5 !w-2.5 !bg-gray-500"
      />
    </div>
  );
}
