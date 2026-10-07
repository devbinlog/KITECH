"use client";

/**
 * useUndoRedo — wires HistoryStore to React Flow's lifted nodes/edges and
 * binds keyboard shortcuts (Ctrl+Z / Ctrl+Y, Cmd on Mac).
 *
 * Usage (page.tsx):
 *   const { pushSnapshot, undo, redo, canUndo, canRedo } = useUndoRedo({
 *     nodes, edges, setNodes, setEdges,
 *   });
 *   // call pushSnapshot() before any mutation you want to be undoable.
 *
 * Design Ref: §11 M4 Module
 */

import { useCallback, useEffect } from "react";
import type { Edge, Node } from "reactflow";

import type { EditorNodeData } from "@/types/scenario";
import { useHistoryStore } from "../store/useHistoryStore";

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
}

export function useUndoRedo({ nodes, edges, setNodes, setEdges }: Args) {
  const push = useHistoryStore((s) => s.push);
  const undo = useHistoryStore((s) => s.undo);
  const redo = useHistoryStore((s) => s.redo);
  const reset = useHistoryStore((s) => s.reset);

  const pushSnapshot = useCallback(() => {
    push({ nodes, edges });
  }, [push, nodes, edges]);

  const doUndo = useCallback(() => {
    const snap = undo({ nodes, edges });
    if (snap) {
      setNodes(snap.nodes);
      setEdges(snap.edges);
    }
  }, [undo, nodes, edges, setNodes, setEdges]);

  const doRedo = useCallback(() => {
    const snap = redo({ nodes, edges });
    if (snap) {
      setNodes(snap.nodes);
      setEdges(snap.edges);
    }
  }, [redo, nodes, edges, setNodes, setEdges]);

  // Keyboard: Ctrl+Z / Cmd+Z, Ctrl+Y or Ctrl+Shift+Z for redo
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const mod = e.ctrlKey || e.metaKey;
      if (!mod) return;
      // Avoid hijacking keystrokes inside form fields.
      const target = e.target as HTMLElement | null;
      if (
        target &&
        (target.tagName === "INPUT" ||
          target.tagName === "TEXTAREA" ||
          target.isContentEditable)
      ) {
        return;
      }
      if (e.key === "z" && !e.shiftKey) {
        e.preventDefault();
        doUndo();
      } else if ((e.key === "y") || (e.key === "z" && e.shiftKey)) {
        e.preventDefault();
        doRedo();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [doUndo, doRedo]);

  return {
    pushSnapshot,
    undo: doUndo,
    redo: doRedo,
    reset,
    canUndo: useHistoryStore((s) => s.canUndo()),
    canRedo: useHistoryStore((s) => s.canRedo()),
  };
}
