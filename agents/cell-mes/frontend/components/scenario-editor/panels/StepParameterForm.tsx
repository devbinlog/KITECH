"use client";

/**
 * StepParameterForm — edit ScenarioStepData fields.
 *
 * V1 (M3) fields: stepId, stepName, action, acquire, paramsJson, routing.
 * V2 (M7): action and paramsJson use ExpressionInput (autocomplete on `{{`).
 *
 * Design Ref: §5.4 Page UI Checklist > Parameter Panel (StepParameterForm)
 */

import type { Node } from "reactflow";

import type { EditorNodeData, ScenarioStepData } from "@/types/scenario";

import { AcquireRolesEditor } from "./AcquireRolesEditor";
import { RoutingRulesEditor } from "./RoutingRulesEditor";
import { ExpressionInput } from "../expression/ExpressionInput";
import { useExpressionSuggestions } from "../expression/useExpressionSuggestions";

interface Props {
  data: ScenarioStepData;
  onChange: (patch: Partial<ScenarioStepData>) => void;
  /** All current canvas nodes — used to derive expression suggestions. */
  allNodes?: Node<EditorNodeData>[];
}

export function StepParameterForm({ data, onChange, allNodes }: Props) {
  const suggestions = useExpressionSuggestions(allNodes ?? []);

  return (
    <div className="space-y-3">
      <FieldRow label="Step ID">
        <input
          type="text"
          value={data.stepId}
          onChange={(e) => onChange({ stepId: e.target.value })}
          placeholder="예: 1-1"
          className="w-full rounded border border-gray-300 px-2 py-1 font-mono text-xs focus:border-blue-500 focus:outline-none"
        />
      </FieldRow>

      <FieldRow label="Step Name">
        <input
          type="text"
          value={data.stepName}
          onChange={(e) => onChange({ stepName: e.target.value })}
          placeholder="예: 소재공급기: 소재 공급"
          className="w-full rounded border border-gray-300 px-2 py-1 text-xs focus:border-blue-500 focus:outline-none"
        />
      </FieldRow>

      <FieldRow label="Action">
        <ExpressionInput
          value={data.action}
          onChange={(action) => onChange({ action })}
          suggestions={suggestions}
          placeholder="예: {{acq.main}}/robotGateway/commands/move"
        />
      </FieldRow>

      <FieldRow label="Acquire">
        <AcquireRolesEditor
          value={data.acquire}
          onChange={(acquire) => onChange({ acquire })}
        />
      </FieldRow>

      <FieldRow label="Params (JSON)">
        <ExpressionInput
          value={data.paramsJson}
          onChange={(paramsJson) => onChange({ paramsJson })}
          suggestions={suggestions}
          multiline
          rows={4}
          placeholder='{"key": "value"}'
        />
      </FieldRow>

      <FieldRow label="Routing">
        <RoutingRulesEditor
          value={data.routing.values}
          onChange={(values) => onChange({ routing: { values } })}
        />
      </FieldRow>
    </div>
  );
}

function FieldRow({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="mb-1 block text-[11px] font-semibold uppercase tracking-wider text-gray-700">
        {label}
      </label>
      {children}
    </div>
  );
}
