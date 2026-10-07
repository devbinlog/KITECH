"use client";

/**
 * ParameterPanel — right sidebar form dispatcher.
 *
 * Looks up the single selected node from props.nodes and routes to:
 *   - StepParameterForm (scenarioStep)
 *   - ConfigParameterForm (scenarioConfig)
 *   - StickyParameterForm (stickyNote)
 *   - empty state otherwise (manualTrigger has nothing to edit)
 *
 * Patches go through props.setNodes (immutable update by id).
 *
 * Design Ref: §5.1 Layout (right column), §5.4 Page UI Checklist
 */

import type { Node } from "reactflow";

import type {
  EditorNodeData,
  ScenarioConfigData,
  ScenarioStepData,
  StickyNoteData,
} from "@/types/scenario";
import { useEditorStore } from "../store/useEditorStore";

import { StepParameterForm } from "./StepParameterForm";
import { ConfigParameterForm } from "./ConfigParameterForm";
import { StickyParameterForm } from "./StickyParameterForm";

interface Props {
  nodes: Node<EditorNodeData>[];
  setNodes: (
    updater: (
      nds: Node<EditorNodeData>[]
    ) => Node<EditorNodeData>[]
  ) => void;
  /** Optional — called once before each batch of edits to enable undo. */
  onCommit?: () => void;
}

export function ParameterPanel({ nodes, setNodes, onCommit }: Props) {
  const selectedIds = useEditorStore((s) => s.selectedNodeIds);
  const markDirty = useEditorStore((s) => s.markDirty);

  // Show form only when exactly one node is selected.
  if (selectedIds.length !== 1) {
    return (
      <div className="flex h-full items-center justify-center px-4 text-center text-sm text-gray-500">
        {selectedIds.length === 0
          ? "노드를 선택하면 파라미터를 편집할 수 있습니다"
          : `${selectedIds.length}개 노드 선택됨 — 단일 선택 시 편집`}
      </div>
    );
  }

  const id = selectedIds[0];
  const node = nodes.find((n) => n.id === id);
  if (!node) {
    return (
      <div className="flex h-full items-center justify-center px-4 text-center text-sm text-gray-400">
        선택된 노드를 찾을 수 없습니다
      </div>
    );
  }

  const patchData = (patch: Partial<EditorNodeData>) => {
    if (onCommit) onCommit();
    setNodes((nds) =>
      nds.map((n) =>
        n.id === id
          ? { ...n, data: { ...n.data, ...patch } as EditorNodeData }
          : n
      )
    );
    markDirty();
  };

  const kind = node.data?.kind;

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-gray-200 bg-white px-4 py-2">
        <div className="text-[10px] font-semibold uppercase tracking-wider text-gray-500">
          {kindToTitle(kind)}
        </div>
        <div className="truncate text-sm font-semibold text-gray-900">
          {nodeDisplayName(node)}
        </div>
      </div>
      <div className="flex-1 overflow-y-auto px-4 py-3">
        {kind === "scenarioStep" && (
          <StepParameterForm
            data={node.data as ScenarioStepData}
            onChange={patchData}
            allNodes={nodes}
          />
        )}
        {kind === "scenarioConfig" && (
          <ConfigParameterForm
            data={node.data as ScenarioConfigData}
            onChange={patchData}
          />
        )}
        {kind === "stickyNote" && (
          <StickyParameterForm
            data={node.data as StickyNoteData}
            onChange={patchData}
          />
        )}
        {kind === "manualTrigger" && (
          <div className="rounded border border-dashed border-gray-300 p-3 text-xs text-gray-500">
            Manual Trigger 노드는 편집할 파라미터가 없습니다.
          </div>
        )}
      </div>
    </div>
  );
}

function kindToTitle(kind?: string): string {
  switch (kind) {
    case "scenarioStep":
      return "Scenario Step";
    case "scenarioConfig":
      return "Scenario Config";
    case "stickyNote":
      return "Sticky Note";
    case "manualTrigger":
      return "Manual Trigger";
    default:
      return "Unknown";
  }
}

function nodeDisplayName(node: Node<EditorNodeData>): string {
  const data = node.data;
  if (!data) return node.id;
  if (data.kind === "scenarioStep") {
    return `${data.stepId} ${data.stepName ?? ""}`.trim();
  }
  if (data.kind === "scenarioConfig") return data.scenarioName || "Config";
  if (data.kind === "stickyNote") {
    const t = data.text || "";
    return t.length > 40 ? `${t.slice(0, 40)}…` : t || "Sticky Note";
  }
  if (data.kind === "manualTrigger") return "Manual Trigger";
  return node.id;
}
