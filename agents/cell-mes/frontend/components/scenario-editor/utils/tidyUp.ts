/**
 * tidyUp — client-side auto-layout for the scenario canvas.
 *
 * V1 (M6): BFS-based left-to-right layout starting from the manual trigger
 * (or first node if no trigger), stacking siblings vertically. This is
 * deliberately dependency-free (no dagre import) since our scenarios are
 * small (< 100 nodes) and the layout shape mirrors the server-side
 * compute_layout in scenario_converter.py.
 *
 * Rules:
 *   - Sticky notes are NOT moved (they're free annotations).
 *   - Disconnected nodes (no incoming/outgoing edges with the trigger
 *     subgraph) are placed in a separate row below the main flow.
 *
 * Design Ref: §11 M6 Module
 */

import type { Edge, Node } from "reactflow";

import type { EditorNodeData } from "@/types/scenario";

const X_START = 240;
const Y_MAIN = 300;
const X_STEP = 240;
const Y_STEP = 140; // vertical separation for sibling nodes

interface TidyOptions {
  preserveSticky?: boolean;
}

export function tidyUp(
  nodes: Node<EditorNodeData>[],
  edges: Edge[],
  options: TidyOptions = {}
): Node<EditorNodeData>[] {
  const preserveSticky = options.preserveSticky ?? true;

  // Filter sticky notes out of the layout if requested; they keep their
  // own positions. They'll be re-added unchanged at the end.
  const layoutNodes = nodes.filter(
    (n) => !preserveSticky || n.data?.kind !== "stickyNote"
  );
  const sticky = nodes.filter(
    (n) => preserveSticky && n.data?.kind === "stickyNote"
  );

  if (layoutNodes.length === 0) return nodes;

  // Build adjacency: source -> [target, ...]
  const adj = new Map<string, string[]>();
  const incoming = new Map<string, number>();
  layoutNodes.forEach((n) => {
    adj.set(n.id, []);
    incoming.set(n.id, 0);
  });
  for (const e of edges) {
    if (!adj.has(e.source) || !incoming.has(e.target)) continue;
    adj.get(e.source)!.push(e.target);
    incoming.set(e.target, (incoming.get(e.target) ?? 0) + 1);
  }

  // Find roots: prefer manualTrigger; otherwise nodes with no incoming.
  const triggers = layoutNodes.filter(
    (n) => n.data?.kind === "manualTrigger"
  );
  const roots: string[] =
    triggers.length > 0
      ? triggers.map((n) => n.id)
      : layoutNodes
          .filter((n) => (incoming.get(n.id) ?? 0) === 0)
          .map((n) => n.id);

  if (roots.length === 0 && layoutNodes.length > 0) {
    // Fully cyclic graph fallback — pick the first node.
    roots.push(layoutNodes[0].id);
  }

  // BFS to assign columns.
  const column = new Map<string, number>();
  const visited = new Set<string>();
  const queue: Array<{ id: string; col: number }> = roots.map((id) => ({
    id,
    col: 0,
  }));
  while (queue.length > 0) {
    const { id, col } = queue.shift()!;
    if (visited.has(id)) {
      // Update column to max so all paths flow rightward.
      column.set(id, Math.max(column.get(id) ?? 0, col));
      continue;
    }
    visited.add(id);
    column.set(id, col);
    for (const next of adj.get(id) ?? []) {
      queue.push({ id: next, col: col + 1 });
    }
  }

  // Group nodes by column for vertical stacking.
  const byCol = new Map<number, string[]>();
  for (const [id, col] of column) {
    if (!byCol.has(col)) byCol.set(col, []);
    byCol.get(col)!.push(id);
  }

  // Compute new positions.
  const newPos = new Map<string, { x: number; y: number }>();
  for (const [col, ids] of byCol) {
    ids.forEach((id, idx) => {
      const x = X_START + col * X_STEP;
      // Center the column vertically around Y_MAIN.
      const yCenterOffset = ((ids.length - 1) * Y_STEP) / 2;
      const y = Y_MAIN - yCenterOffset + idx * Y_STEP;
      newPos.set(id, { x, y });
    });
  }

  // Orphans: any layoutNode not visited (e.g. disconnected from any root).
  const orphans = layoutNodes.filter((n) => !visited.has(n.id));
  const orphanY = Y_MAIN + 4 * Y_STEP;
  orphans.forEach((n, i) => {
    newPos.set(n.id, { x: X_START + i * X_STEP, y: orphanY });
  });

  // Apply.
  return [
    ...layoutNodes.map((n) => {
      const p = newPos.get(n.id);
      return p ? { ...n, position: p } : n;
    }),
    ...sticky, // unchanged
  ];
}
