"use client";

/**
 * ExecutionDataViewer — JSON pretty-print of selected node's run input/output.
 *
 * Design Ref: §5.4 Execution Panel (per-node input/output)
 */

import type { NodeRunState } from "../store/useExecutionStore";

interface Props {
  state: NodeRunState | undefined;
}

export function ExecutionDataViewer({ state }: Props) {
  if (!state) {
    return (
      <div className="px-3 py-2 text-xs text-gray-500">
        실행 정보 없음
      </div>
    );
  }
  return (
    <div className="space-y-3 p-3 text-xs">
      <Row label="Status" value={state.status} />
      {state.durationMs != null && (
        <Row label="Duration" value={`${state.durationMs}ms`} />
      )}
      {state.error && <Row label="Error" value={state.error} kind="error" />}
      <Section label="Input" payload={state.input} />
      <Section label="Output" payload={state.output} />
    </div>
  );
}

function Row({
  label,
  value,
  kind,
}: {
  label: string;
  value: string;
  kind?: "error";
}) {
  return (
    <div className="flex items-baseline gap-2">
      <span className="w-16 text-[10px] font-semibold uppercase tracking-wider text-gray-500">
        {label}
      </span>
      <span
        className={
          kind === "error" ? "text-red-700" : "font-mono text-[11px] text-gray-900"
        }
      >
        {value}
      </span>
    </div>
  );
}

function Section({ label, payload }: { label: string; payload: unknown }) {
  if (payload === undefined || payload === null) return null;
  return (
    <div>
      <div className="mb-0.5 text-[10px] font-semibold uppercase tracking-wider text-gray-500">
        {label}
      </div>
      <pre className="max-h-48 overflow-auto rounded border border-gray-200 bg-gray-50 p-2 font-mono text-[10px] leading-tight text-gray-800">
        {JSON.stringify(payload, null, 2)}
      </pre>
    </div>
  );
}
