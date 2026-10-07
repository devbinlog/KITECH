"use client";

/**
 * ExecutionPanel — collapsible bottom panel showing per-node run results.
 *
 * Layout:
 *   - Left column: list of nodes with status pill (clickable -> selects node)
 *   - Right column: ExecutionDataViewer for the selected node
 *
 * Design Ref: §5.1 Layout (collapsible bottom), §11 M10 Module
 */

import { useState } from "react";
import type { Node } from "reactflow";
import {
  ChevronDown,
  ChevronUp,
  Pin,
  PinOff,
  CheckCircle2,
  XCircle,
  Loader2,
  Circle,
} from "lucide-react";

import type { EditorNodeData, ScenarioStepData } from "@/types/scenario";
import { useExecutionStore, type NodeRunState } from "../store/useExecutionStore";
import { ExecutionDataViewer } from "../execution/ExecutionDataViewer";

interface Props {
  nodes: Node<EditorNodeData>[];
}

export function ExecutionPanel({ nodes }: Props) {
  const status = useExecutionStore((s) => s.status);
  const runNodes = useExecutionStore((s) => s.nodes);
  const togglePin = useExecutionStore((s) => s.togglePin);
  const pinned = useExecutionStore((s) => s.pinned);
  const [open, setOpen] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const hasRun = status !== "idle";

  // Auto-open on first run start.
  if (status === "running" && !open) {
    setOpen(true);
  }

  const entries = nodes
    .filter((n) => n.data?.kind !== "stickyNote")
    .map((n) => ({
      node: n,
      run: runNodes[n.id] as NodeRunState | undefined,
      label:
        n.data?.kind === "scenarioStep"
          ? `${(n.data as ScenarioStepData).stepId} ${
              (n.data as ScenarioStepData).stepName ?? ""
            }`.trim()
          : n.data?.kind === "manualTrigger"
            ? "Manual Trigger"
            : n.data?.kind === "scenarioConfig"
              ? "Scenario Config"
              : n.id,
    }));

  return (
    <div className="border-t border-gray-200 bg-white">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between border-b border-gray-100 bg-gray-50 px-3 py-1.5 text-left text-xs font-semibold uppercase tracking-wider text-gray-700 hover:bg-gray-100"
      >
        <span className="flex items-center gap-2">
          실행 결과
          {hasRun && (
            <span className="rounded-full bg-gray-200 px-2 py-0.5 text-[10px] normal-case tracking-normal">
              {status}
            </span>
          )}
        </span>
        {open ? <ChevronDown size={14} /> : <ChevronUp size={14} />}
      </button>
      {open && (
        <div className="grid h-56 grid-cols-2 divide-x divide-gray-200">
          <div className="overflow-y-auto">
            {entries.length === 0 && (
              <div className="px-3 py-4 text-xs text-gray-400">
                노드 없음
              </div>
            )}
            {entries.map(({ node, run, label }) => (
              <div
                key={node.id}
                className={`flex items-center gap-2 border-b border-gray-100 px-3 py-1.5 hover:bg-gray-50 ${
                  selectedId === node.id ? "bg-blue-50" : ""
                }`}
              >
                <button
                  onClick={() => setSelectedId(node.id)}
                  className="flex flex-1 items-center gap-2 text-left"
                >
                  <StatusIcon status={run?.status} />
                  <span className="truncate text-xs">{label}</span>
                  {run?.durationMs != null && (
                    <span className="text-[10px] text-gray-400">
                      {run.durationMs}ms
                    </span>
                  )}
                </button>
                <button
                  onClick={() => togglePin(node.id)}
                  title="다음 실행에 mock으로 사용"
                  className="rounded p-0.5 text-gray-400 hover:text-gray-700"
                >
                  {pinned.has(node.id) ? (
                    <Pin size={12} className="text-amber-600" />
                  ) : (
                    <PinOff size={12} />
                  )}
                </button>
              </div>
            ))}
          </div>
          <div className="overflow-y-auto">
            <ExecutionDataViewer
              state={selectedId ? runNodes[selectedId] : undefined}
            />
          </div>
        </div>
      )}
    </div>
  );
}

function StatusIcon({ status }: { status?: NodeRunState["status"] }) {
  if (status === "success")
    return <CheckCircle2 size={12} className="flex-shrink-0 text-green-600" />;
  if (status === "error")
    return <XCircle size={12} className="flex-shrink-0 text-red-600" />;
  if (status === "running")
    return (
      <Loader2 size={12} className="flex-shrink-0 animate-spin text-blue-600" />
    );
  return <Circle size={12} className="flex-shrink-0 text-gray-300" />;
}
