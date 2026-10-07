"use client";

/**
 * NodeBadge — validation indicator on node cards.
 *
 * V1 (M2): minimal stub — renders a red dot + count when errors > 0,
 *          tooltip lists messages.
 *
 * Full validation logic and rich tooltip lands in M5 (validate.ts).
 *
 * Design Ref: §5.4 (인라인 validation badge), Plan SC #8
 */

import { AlertCircle } from "lucide-react";

import type { ValidationError } from "@/types/scenario";
import { useEditorStore } from "../store/useEditorStore";

interface NodeBadgeProps {
  /** Pass the React Flow node id when rendered inside a custom node so the
   *  badge can pull errors from the editor store. The legacy `errors`
   *  prop is still honoured if explicitly supplied. */
  nodeId?: string;
  errors?: ValidationError[];
}

export function NodeBadge({ nodeId, errors }: NodeBadgeProps) {
  const fromStore = useEditorStore((s) =>
    nodeId ? s.errorsByNodeId[nodeId] : undefined
  );
  const list = errors ?? fromStore ?? [];
  if (list.length === 0) return null;
  const hasError = list.some((e) => (e.severity ?? "error") === "error");

  return (
    <span
      className={`inline-flex items-center gap-0.5 rounded-full px-1.5 py-0.5 text-[10px] font-medium ${
        hasError
          ? "bg-red-100 text-red-800"
          : "bg-yellow-100 text-yellow-800"
      }`}
      title={list.map((e) => `${e.field}: ${e.message}`).join("\n")}
    >
      <AlertCircle size={10} />
      {list.length}
    </span>
  );
}
