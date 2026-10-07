"use client";

/**
 * NodeStatusIndicator — overlays a status dot on a node card during a run.
 *
 * Modes (per useExecutionStore.nodes[id].status):
 *   pending — gray
 *   running — blue, animate-pulse
 *   success — green check
 *   error   — red X
 *
 * Design Ref: §5.4 Page UI Checklist > Nodes (NodeStatusIndicator)
 */

import { Check, X, Loader2 } from "lucide-react";

import { useExecutionStore } from "../store/useExecutionStore";

interface Props {
  nodeId: string;
}

export function NodeStatusIndicator({ nodeId }: Props) {
  const node = useExecutionStore((s) => s.nodes[nodeId]);
  if (!node) return null;
  const cls =
    "absolute -right-2 -top-2 z-10 inline-flex h-5 w-5 items-center justify-center rounded-full border-2 border-white shadow";
  if (node.status === "running") {
    return (
      <span className={`${cls} bg-blue-500 text-white`} title="실행 중">
        <Loader2 size={11} className="animate-spin" />
      </span>
    );
  }
  if (node.status === "success") {
    return (
      <span className={`${cls} bg-green-500 text-white`} title="성공">
        <Check size={12} />
      </span>
    );
  }
  if (node.status === "error") {
    return (
      <span className={`${cls} bg-red-500 text-white`} title={node.error ?? "실패"}>
        <X size={12} />
      </span>
    );
  }
  return (
    <span className={`${cls} bg-gray-300 text-white`} title="대기">
      <span className="block h-1.5 w-1.5 rounded-full bg-white" />
    </span>
  );
}
