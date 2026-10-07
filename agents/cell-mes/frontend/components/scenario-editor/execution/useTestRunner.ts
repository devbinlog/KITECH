"use client";

/**
 * useTestRunner — start / poll / cancel test execution against cell-mes.
 *
 * Flow (driven by user clicking the Run button):
 *   1. POST /scenarios/{id}/test-runs with the current workflow JSON
 *   2. Poll GET /scenarios/test-runs/{exec_id} every 1s up to 120s
 *   3. Surface per-node statuses through useExecutionStore so node cards
 *      and the bottom panel can react.
 *
 * Cancellation is cooperative — POST .../cancel toggles the server signal,
 * polling sees status='cancelled', stops.
 *
 * Design Ref: §11 M10 Module, §2.2 Data Flow (Test Run)
 * Plan SC: #10 (Test Run -> 노드별 success/error)
 */

import { useCallback, useEffect, useRef } from "react";

import api from "@/lib/axios";
import {
  useExecutionStore,
  type RunStatus,
  type NodeRunState,
} from "../store/useExecutionStore";
import type { N8nWorkflow } from "@/types/scenario";

const POLL_INTERVAL_MS = 1000;
const POLL_MAX_TICKS = 120; // 2 min

interface CreateResp {
  execution_id: string;
  status: RunStatus;
}

interface StatusResp {
  execution_id: string;
  status: RunStatus;
  started_at: string | null;
  finished_at: string | null;
  /** Server uses snake_case keys per node: status / input / output / error / duration_ms */
  nodes: Record<
    string,
    {
      status: NodeRunState["status"];
      input?: unknown;
      output?: unknown;
      error?: string;
      duration_ms?: number;
    }
  >;
}

function normalizeNodes(
  raw: StatusResp["nodes"]
): Record<string, NodeRunState> {
  const out: Record<string, NodeRunState> = {};
  for (const [k, v] of Object.entries(raw ?? {})) {
    out[k] = {
      status: v.status,
      input: v.input,
      output: v.output,
      error: v.error,
      durationMs: v.duration_ms,
    };
  }
  return out;
}

export function useTestRunner(scenarioId: number) {
  const begin = useExecutionStore((s) => s.begin);
  const ingest = useExecutionStore((s) => s.ingestStatus);
  const reset = useExecutionStore((s) => s.reset);

  const pollTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const ticksRef = useRef(0);
  const cancelledRef = useRef(false);

  const stopPolling = useCallback(() => {
    if (pollTimer.current) {
      clearInterval(pollTimer.current);
      pollTimer.current = null;
    }
  }, []);

  useEffect(() => () => stopPolling(), [stopPolling]);

  const start = useCallback(
    async (workflow: N8nWorkflow) => {
      reset();
      cancelledRef.current = false;
      ticksRef.current = 0;

      const create = await api.post<CreateResp>(
        `/api/v1/masters/scenarios/${scenarioId}/test-runs`,
        { workflow }
      );
      const executionId = create.data.execution_id;
      begin(executionId);

      stopPolling();
      pollTimer.current = setInterval(async () => {
        if (cancelledRef.current) {
          stopPolling();
          return;
        }
        ticksRef.current += 1;
        if (ticksRef.current > POLL_MAX_TICKS) {
          stopPolling();
          ingest({
            status: "error",
            nodes: useExecutionStore.getState().nodes,
            finishedAt: Date.now(),
          });
          return;
        }
        try {
          const r = await api.get<StatusResp>(
            `/api/v1/masters/scenarios/test-runs/${executionId}`
          );
          const data = r.data;
          ingest({
            status: data.status,
            nodes: normalizeNodes(data.nodes),
            startedAt: data.started_at
              ? Date.parse(data.started_at)
              : undefined,
            finishedAt: data.finished_at
              ? Date.parse(data.finished_at)
              : undefined,
          });
          if (
            data.status === "success" ||
            data.status === "error" ||
            data.status === "cancelled"
          ) {
            stopPolling();
          }
        } catch {
          // Network blip — keep polling until max ticks.
        }
      }, POLL_INTERVAL_MS);

      return executionId;
    },
    [scenarioId, begin, ingest, reset, stopPolling]
  );

  const cancel = useCallback(async () => {
    const executionId = useExecutionStore.getState().executionId;
    if (!executionId) return;
    cancelledRef.current = true;
    try {
      await api.post(
        `/api/v1/masters/scenarios/test-runs/${executionId}/cancel`
      );
    } catch {
      /* server may have already finished */
    }
    stopPolling();
    ingest({
      status: "cancelled",
      nodes: useExecutionStore.getState().nodes,
      finishedAt: Date.now(),
    });
  }, [ingest, stopPolling]);

  return { start, cancel };
}
