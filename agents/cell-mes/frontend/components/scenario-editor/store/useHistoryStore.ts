/**
 * useHistoryStore — undo/redo snapshot stack for the scenario editor.
 *
 * V1 (M4): snapshot-based (full nodes/edges arrays per push). Simpler than
 *           immer patches for our scale (typical scenario < 100 nodes).
 *           Capped at HISTORY_MAX entries to bound memory.
 * V2 (later): switch to immer Patch[] if performance becomes an issue.
 *
 * Push points (called by useUndoRedo + ParameterPanel + ScenarioCanvas):
 *   - Before any structural change: position, add/remove, parameter edit
 *
 * Design Ref: §11 M4 Module, §6.3 Component Diagram (3 stores)
 */

import { create } from "zustand";
import type { Edge, Node } from "reactflow";

import type { EditorNodeData } from "@/types/scenario";

const HISTORY_MAX = 50;

type Snapshot = {
  nodes: Node<EditorNodeData>[];
  edges: Edge[];
};

interface HistoryState {
  past: Snapshot[];
  future: Snapshot[];
  /** Push the *previous* state before applying a new change. */
  push: (prev: Snapshot) => void;
  /** Undo — returns the snapshot to apply, or null if nothing to undo. */
  undo: (current: Snapshot) => Snapshot | null;
  /** Redo — returns the snapshot to apply, or null if nothing to redo. */
  redo: (current: Snapshot) => Snapshot | null;
  /** Clear both stacks (e.g. on initial load or after explicit save). */
  reset: () => void;
  canUndo: () => boolean;
  canRedo: () => boolean;
}

export const useHistoryStore = create<HistoryState>((set, get) => ({
  past: [],
  future: [],

  push: (prev) =>
    set((state) => {
      const past = [...state.past, prev];
      if (past.length > HISTORY_MAX) past.shift();
      return { past, future: [] }; // any new edit invalidates redo
    }),

  undo: (current) => {
    const { past, future } = get();
    if (past.length === 0) return null;
    const previous = past[past.length - 1];
    set({
      past: past.slice(0, -1),
      future: [current, ...future],
    });
    return previous;
  },

  redo: (current) => {
    const { past, future } = get();
    if (future.length === 0) return null;
    const next = future[0];
    set({
      past: [...past, current],
      future: future.slice(1),
    });
    return next;
  },

  reset: () => set({ past: [], future: [] }),

  canUndo: () => get().past.length > 0,
  canRedo: () => get().future.length > 0,
}));
