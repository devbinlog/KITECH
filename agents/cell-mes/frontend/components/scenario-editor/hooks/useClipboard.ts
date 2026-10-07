"use client";

/**
 * useClipboard — copy / cut / paste / duplicate for selected editor nodes.
 *
 * Bound shortcuts (active when not focused on form input):
 *   Ctrl+C / Cmd+C — copy
 *   Ctrl+X / Cmd+X — cut (copy + delete selected)
 *   Ctrl+V / Cmd+V — paste at PASTE_OFFSET
 *   Ctrl+D / Cmd+D — duplicate (copy + immediate paste)
 *   Delete / Backspace — bulk delete selected
 *
 * Pushes a history snapshot before each mutation.
 *
 * Design Ref: §11 M5 Module, §5.4 Keyboard Shortcuts
 */

import { useCallback, useEffect, useRef } from "react";
import type { Edge, Node } from "reactflow";

import type { EditorNodeData, ScenarioStepData } from "@/types/scenario";
import { useEditorStore } from "../store/useEditorStore";
import { cloneNodesAndEdges } from "../utils/nodeFactory";

interface Args {
  nodes: Node<EditorNodeData>[];
  edges: Edge[];
  setNodes: (
    updater:
      | Node<EditorNodeData>[]
      | ((nds: Node<EditorNodeData>[]) => Node<EditorNodeData>[])
  ) => void;
  setEdges: (
    updater: Edge[] | ((eds: Edge[]) => Edge[])
  ) => void;
  /** Push a history snapshot before mutating. */
  pushSnapshot: () => void;
}

interface ClipboardPayload {
  nodes: Node<EditorNodeData>[];
  edges: Edge[];
}

export function useClipboard({
  nodes,
  edges,
  setNodes,
  setEdges,
  pushSnapshot,
}: Args) {
  const selectedIds = useEditorStore((s) => s.selectedNodeIds);
  const setSelectedNodeIds = useEditorStore((s) => s.setSelectedNodeIds);
  const markDirty = useEditorStore((s) => s.markDirty);

  // Clipboard kept in a ref so it never causes re-renders.
  const clipboard = useRef<ClipboardPayload | null>(null);

  const collectSelected = useCallback((): ClipboardPayload => {
    const sel = new Set(selectedIds);
    const ns = nodes.filter((n) => sel.has(n.id));
    const es = edges.filter((e) => sel.has(e.source) && sel.has(e.target));
    return { nodes: ns, edges: es };
  }, [nodes, edges, selectedIds]);

  const collectStepIds = useCallback((): Set<string> => {
    const out = new Set<string>();
    for (const n of nodes) {
      if (n.data?.kind === "scenarioStep") {
        out.add((n.data as ScenarioStepData).stepId);
      }
    }
    return out;
  }, [nodes]);

  const copy = useCallback(() => {
    if (selectedIds.length === 0) return;
    clipboard.current = collectSelected();
  }, [collectSelected, selectedIds.length]);

  const remove = useCallback(() => {
    if (selectedIds.length === 0) return;
    pushSnapshot();
    const sel = new Set(selectedIds);
    setNodes((nds) => nds.filter((n) => !sel.has(n.id)));
    setEdges((eds) =>
      eds.filter((e) => !sel.has(e.source) && !sel.has(e.target))
    );
    setSelectedNodeIds([]);
    markDirty();
  }, [
    selectedIds,
    pushSnapshot,
    setNodes,
    setEdges,
    setSelectedNodeIds,
    markDirty,
  ]);

  const cut = useCallback(() => {
    if (selectedIds.length === 0) return;
    clipboard.current = collectSelected();
    remove();
  }, [collectSelected, remove, selectedIds.length]);

  const paste = useCallback(() => {
    const payload = clipboard.current;
    if (!payload || payload.nodes.length === 0) return;
    pushSnapshot();
    const cloned = cloneNodesAndEdges(payload.nodes, payload.edges, {
      existingStepIds: collectStepIds(),
    });
    setNodes((nds) => [...nds, ...cloned.nodes]);
    setEdges((eds) => [...eds, ...cloned.edges]);
    setSelectedNodeIds(cloned.nodes.map((n) => n.id));
    markDirty();
  }, [
    pushSnapshot,
    setNodes,
    setEdges,
    setSelectedNodeIds,
    markDirty,
    collectStepIds,
  ]);

  const duplicate = useCallback(() => {
    if (selectedIds.length === 0) return;
    pushSnapshot();
    const payload = collectSelected();
    const cloned = cloneNodesAndEdges(payload.nodes, payload.edges, {
      existingStepIds: collectStepIds(),
    });
    setNodes((nds) => [...nds, ...cloned.nodes]);
    setEdges((eds) => [...eds, ...cloned.edges]);
    setSelectedNodeIds(cloned.nodes.map((n) => n.id));
    markDirty();
  }, [
    selectedIds.length,
    pushSnapshot,
    collectSelected,
    setNodes,
    setEdges,
    setSelectedNodeIds,
    markDirty,
    collectStepIds,
  ]);

  // Keyboard wiring
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      if (
        target &&
        (target.tagName === "INPUT" ||
          target.tagName === "TEXTAREA" ||
          target.isContentEditable)
      ) {
        return;
      }
      const mod = e.ctrlKey || e.metaKey;
      if (mod && e.key === "c") {
        e.preventDefault();
        copy();
        return;
      }
      if (mod && e.key === "x") {
        e.preventDefault();
        cut();
        return;
      }
      if (mod && e.key === "v") {
        e.preventDefault();
        paste();
        return;
      }
      if (mod && e.key === "d") {
        e.preventDefault();
        duplicate();
        return;
      }
      if (e.key === "Delete" || e.key === "Backspace") {
        // Only when there is a selection — otherwise let the browser handle.
        if (selectedIds.length > 0) {
          e.preventDefault();
          remove();
        }
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [copy, cut, paste, duplicate, remove, selectedIds.length]);

  return { copy, cut, paste, duplicate, remove };
}
