"use client";

/**
 * ScenarioCanvas — React Flow shell for the scenario editor.
 *
 * V1 (M1+M2): pan/zoom, mini-map, controls, custom node types, RoutingEdge.
 * V2 (M3): controlled — receives nodes/edges + handlers from the page so
 * ParameterPanel can patch the same source.
 *
 * Design Ref: §11 M1+M2+M3
 */

import { useCallback } from "react";
import ReactFlow, {
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  type Edge,
  type Node,
  type OnEdgesChange,
  type OnNodesChange,
  type OnSelectionChangeParams,
} from "reactflow";
import "reactflow/dist/style.css";

import { useEditorStore } from "../store/useEditorStore";
import { ManualTriggerNode } from "../nodes/ManualTriggerNode";
import { ScenarioConfigNode } from "../nodes/ScenarioConfigNode";
import { ScenarioStepNode } from "../nodes/ScenarioStepNode";
import { StickyNoteNode } from "../nodes/StickyNoteNode";
import { RoutingEdge } from "../edges/RoutingEdge";

const nodeTypes = {
  manualTrigger: ManualTriggerNode,
  scenarioConfig: ScenarioConfigNode,
  scenarioStep: ScenarioStepNode,
  stickyNote: StickyNoteNode,
};

const edgeTypes = {
  routing: RoutingEdge,
};

interface ScenarioCanvasProps {
  nodes: Node[];
  edges: Edge[];
  onNodesChange: OnNodesChange;
  onEdgesChange: OnEdgesChange;
  /** Optional — called on drag end / node remove to push history snapshot. */
  onCommit?: () => void;
}

export function ScenarioCanvas({
  nodes,
  edges,
  onNodesChange,
  onEdgesChange,
  onCommit,
}: ScenarioCanvasProps) {
  const setSelectedNodeIds = useEditorStore((s) => s.setSelectedNodeIds);
  const markDirty = useEditorStore((s) => s.markDirty);

  const handleSelectionChange = useCallback(
    (params: OnSelectionChangeParams) => {
      setSelectedNodeIds(params.nodes.map((n) => n.id));
    },
    [setSelectedNodeIds]
  );

  return (
    <div className="h-full w-full bg-gray-50">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        onNodesChange={(changes) => {
          onNodesChange(changes);
          if (
            changes.some(
              (c) =>
                c.type === "position" ||
                c.type === "remove" ||
                c.type === "dimensions"
            )
          ) {
            markDirty();
          }
        }}
        onEdgesChange={(changes) => {
          onEdgesChange(changes);
          if (changes.some((c) => c.type === "remove" || c.type === "add")) {
            markDirty();
          }
        }}
        onSelectionChange={handleSelectionChange}
        onNodeDragStop={onCommit}
        selectionOnDrag
        fitView
        fitViewOptions={{ padding: 0.2 }}
      >
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} />
        <Controls position="bottom-right" />
        <MiniMap pannable zoomable position="top-right" />
      </ReactFlow>
    </div>
  );
}
