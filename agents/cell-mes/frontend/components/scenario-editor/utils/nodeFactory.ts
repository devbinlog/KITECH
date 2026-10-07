/**
 * nodeFactory — clone editor nodes with fresh IDs and unique step IDs.
 *
 * Used by:
 *   - useClipboard (paste / duplicate)
 *   - M5 (Add Step), later M6 (Search palette)
 *
 * For step nodes, the original `stepId` is preserved with a `-copy` suffix
 * (incrementing if the suffix already exists). React Flow node IDs are always
 * regenerated to avoid collisions on the canvas.
 *
 * Design Ref: §11 M5 Manipulation (Copy/Paste/Duplicate)
 */

import type { Edge, Node } from "reactflow";

import type { EditorNodeData, ScenarioStepData } from "@/types/scenario";

const PASTE_OFFSET = { x: 40, y: 40 };

function freshId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  // Fallback for older runtimes (extremely unlikely on modern browsers).
  return `n-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 9)}`;
}

/** Generate a unique step id that doesn't collide with `existingStepIds`. */
function uniqueStepId(base: string, existingStepIds: Set<string>): string {
  if (!existingStepIds.has(base)) return base;
  // Strip any trailing "-copyN" to find the natural base.
  const root = base.replace(/-copy(\d+)?$/, "");
  let i = 1;
  while (existingStepIds.has(`${root}-copy${i === 1 ? "" : i}`)) {
    i++;
  }
  return `${root}-copy${i === 1 ? "" : i}`;
}

export interface CloneOptions {
  /** Multi-select clone offset — applied per row of nodes. */
  offset?: { x: number; y: number };
  /** Existing step IDs in the canvas (for collision avoidance). */
  existingStepIds?: Set<string>;
}

/**
 * Clone a set of nodes (and the edges between them) with fresh React Flow ids
 * and unique step ids. Edges that span outside the cloned set are dropped.
 */
export function cloneNodesAndEdges(
  nodes: Node<EditorNodeData>[],
  edges: Edge[],
  options: CloneOptions = {}
): { nodes: Node<EditorNodeData>[]; edges: Edge[] } {
  const offset = options.offset ?? PASTE_OFFSET;
  const stepIds = new Set(options.existingStepIds ?? []);

  // First pass: build oldId -> newId map; clone nodes with patched data.
  const idMap = new Map<string, string>();
  const newNodes = nodes.map((n) => {
    const newId = freshId();
    idMap.set(n.id, newId);

    let data: EditorNodeData = n.data;
    if (data?.kind === "scenarioStep") {
      const step = data as ScenarioStepData;
      const newStepId = uniqueStepId(step.stepId || "step", stepIds);
      stepIds.add(newStepId);
      data = { ...step, stepId: newStepId };
    }

    return {
      ...n,
      id: newId,
      // Preserve type + selection cleared
      selected: false,
      position: {
        x: n.position.x + offset.x,
        y: n.position.y + offset.y,
      },
      data,
    };
  });

  // Second pass: keep only edges fully within the cloned set, remap endpoints.
  const newEdges = edges
    .filter((e) => idMap.has(e.source) && idMap.has(e.target))
    .map((e) => ({
      ...e,
      id: freshId(),
      source: idMap.get(e.source) as string,
      target: idMap.get(e.target) as string,
      selected: false,
    }));

  return { nodes: newNodes, edges: newEdges };
}

/** Convenience — single-node clone (for Ctrl+D). */
export function duplicateNode(
  node: Node<EditorNodeData>,
  existingStepIds: Set<string>
): Node<EditorNodeData> {
  const { nodes } = cloneNodesAndEdges([node], [], {
    existingStepIds,
  });
  return nodes[0];
}

export { PASTE_OFFSET };
