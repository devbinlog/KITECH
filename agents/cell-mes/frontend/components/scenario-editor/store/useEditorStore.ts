/**
 * useEditorStore — Zustand store for scenario editor local state.
 *
 * V1 (M1) responsibilities:
 *   - selection (selected node ids)
 *   - dirty flag (any unsaved change)
 *   - save status (idle / saving / saved / error)
 *
 * Future (M4-M7):
 *   - clipboard, errors, search palette state
 *
 * Design Ref: §6.3 Component Diagram (Zustand 3 stores), §11 Implementation Guide
 */

import { create } from "zustand";

import type { ValidationError } from "@/types/scenario";

export type SaveStatus =
  | { kind: "idle" }
  | { kind: "saving" }
  | { kind: "saved"; at: number }
  | { kind: "error"; message: string };

interface EditorState {
  // Selection
  selectedNodeIds: string[];
  setSelectedNodeIds: (ids: string[]) => void;
  toggleSelected: (id: string, additive: boolean) => void;
  clearSelection: () => void;

  // Dirty tracking
  dirty: boolean;
  markDirty: () => void;
  markClean: () => void;

  // Save status
  saveStatus: SaveStatus;
  setSaveStatus: (status: SaveStatus) => void;

  // Validation — derived externally from nodes; stored here so NodeBadge
  // can read without prop-drilling. Empty map = no errors.
  errorsByNodeId: Record<string, ValidationError[]>;
  setErrorsByNodeId: (next: Record<string, ValidationError[]>) => void;
}

export const useEditorStore = create<EditorState>((set) => ({
  selectedNodeIds: [],
  setSelectedNodeIds: (ids) => set({ selectedNodeIds: ids }),
  toggleSelected: (id, additive) =>
    set((state) => {
      if (!additive) {
        return { selectedNodeIds: [id] };
      }
      const exists = state.selectedNodeIds.includes(id);
      return {
        selectedNodeIds: exists
          ? state.selectedNodeIds.filter((x) => x !== id)
          : [...state.selectedNodeIds, id],
      };
    }),
  clearSelection: () => set({ selectedNodeIds: [] }),

  dirty: false,
  markDirty: () => set({ dirty: true }),
  markClean: () =>
    set({ dirty: false, saveStatus: { kind: "saved", at: Date.now() } }),

  saveStatus: { kind: "idle" },
  setSaveStatus: (status) => set({ saveStatus: status }),

  errorsByNodeId: {},
  setErrorsByNodeId: (next) => set({ errorsByNodeId: next }),
}));

/** Convenience selector — single selected node (or null when 0/multi). */
export const useSingleSelected = (): string | null => {
  return useEditorStore((s) =>
    s.selectedNodeIds.length === 1 ? s.selectedNodeIds[0] : null
  );
};
