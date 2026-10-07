/**
 * useExecutionStore — Test Execution state for the editor.
 *
 * Mirrors the server's TestRunStatusResponse shape:
 *   - executionId
 *   - status: idle / queued / running / success / error / cancelled
 *   - nodes: { [nodeId]: { status, input?, output?, error?, durationMs? } }
 *
 * Design Ref: §6.3 Component Diagram (3 stores), §11 M10 Module
 */

import { create } from "zustand";

export type RunStatus =
  | "idle"
  | "queued"
  | "running"
  | "success"
  | "error"
  | "cancelled";

export interface NodeRunState {
  status: "pending" | "running" | "success" | "error";
  input?: unknown;
  output?: unknown;
  error?: string;
  durationMs?: number;
}

interface ExecutionState {
  executionId: string | null;
  status: RunStatus;
  startedAt: number | null;
  finishedAt: number | null;
  nodes: Record<string, NodeRunState>;
  /** Node ids whose output should be reused as mock on the next run. */
  pinned: Set<string>;

  begin: (executionId: string) => void;
  ingestStatus: (payload: {
    status: RunStatus;
    nodes: Record<string, NodeRunState>;
    startedAt?: number;
    finishedAt?: number;
  }) => void;
  cancel: () => void;
  reset: () => void;

  togglePin: (nodeId: string) => void;
  isPinned: (nodeId: string) => boolean;
}

export const useExecutionStore = create<ExecutionState>((set, get) => ({
  executionId: null,
  status: "idle",
  startedAt: null,
  finishedAt: null,
  nodes: {},
  pinned: new Set<string>(),

  begin: (executionId) =>
    set({
      executionId,
      status: "queued",
      startedAt: Date.now(),
      finishedAt: null,
      nodes: {},
    }),

  ingestStatus: ({ status, nodes, startedAt, finishedAt }) =>
    set((state) => ({
      status,
      nodes,
      startedAt: startedAt ?? state.startedAt,
      finishedAt: finishedAt ?? state.finishedAt,
    })),

  cancel: () =>
    set((state) => ({
      status: state.status === "idle" ? "idle" : "cancelled",
      finishedAt: Date.now(),
    })),

  reset: () =>
    set({
      executionId: null,
      status: "idle",
      startedAt: null,
      finishedAt: null,
      nodes: {},
    }),

  togglePin: (nodeId) =>
    set((state) => {
      const next = new Set(state.pinned);
      if (next.has(nodeId)) next.delete(nodeId);
      else next.add(nodeId);
      return { pinned: next };
    }),

  isPinned: (nodeId) => get().pinned.has(nodeId),
}));
