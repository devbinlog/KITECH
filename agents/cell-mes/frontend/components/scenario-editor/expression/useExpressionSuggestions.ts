"use client";

/**
 * useExpressionSuggestions — derive a categorized suggestion list for the
 * expression autocomplete popup.
 *
 * Sources (V1):
 *   1. Acquire role tokens — {{acq.main}}, {{acq.sub1}}, ...
 *   2. Asset ids from the scenarioConfig node — {{assets.<id>}}
 *   3. Previous step ids — {{var.<stepId>.result}}
 *   4. Common variables — {{var.x}} / {{res}}
 *   5. Built-in functions from expressionFunctions.ts
 *
 * Design Ref: §11 M7 Module
 * Plan SC: #7 (expression suggestion)
 */

import { useMemo } from "react";
import type { Node } from "reactflow";

import type {
  EditorNodeData,
  ScenarioConfigData,
  ScenarioStepData,
} from "@/types/scenario";
import { EXPRESSION_FUNCTIONS } from "./expressionFunctions";

export interface Suggestion {
  /** Insert text — what gets typed when the user picks this entry. */
  insert: string;
  /** Display in the popup. */
  label: string;
  /** Tooltip / secondary line. */
  description?: string;
  category: string;
}

export function useExpressionSuggestions(
  nodes: Node<EditorNodeData>[]
): Suggestion[] {
  return useMemo(() => {
    const out: Suggestion[] = [];

    // 1. Acquire roles (always available)
    (["main", "sub1", "sub2", "sub3"] as const).forEach((role) => {
      out.push({
        insert: `{{acq.${role}}}`,
        label: `acq.${role}`,
        description: `획득된 ${role} 역할 자산 id`,
        category: "acquire",
      });
    });

    // 2. Assets from scenarioConfig node
    const config = nodes.find((n) => n.data?.kind === "scenarioConfig");
    if (config) {
      const cfg = config.data as ScenarioConfigData;
      cfg.assets.forEach((a) => {
        out.push({
          insert: `{{assets.${a.id}}}`,
          label: `assets.${a.id}`,
          description: a.name,
          category: "assets",
        });
      });
    }

    // 3. Step IDs (for routing references etc.)
    nodes.forEach((n) => {
      if (n.data?.kind !== "scenarioStep") return;
      const step = n.data as ScenarioStepData;
      out.push({
        insert: `{{var.${step.stepId}.result}}`,
        label: `var.${step.stepId}.result`,
        description: step.stepName || step.stepId,
        category: "step results",
      });
    });

    // 4. Common variables
    out.push(
      {
        insert: "{{res}}",
        label: "res",
        description: "직전 step 응답",
        category: "common",
      },
      {
        insert: "{{var.x}}",
        label: "var.x",
        description: "사용자 정의 변수 x",
        category: "common",
      }
    );

    // 5. Built-in functions
    EXPRESSION_FUNCTIONS.forEach((fn) => {
      out.push({
        insert: `{{${fn.signature}}}`,
        label: fn.signature,
        description: fn.description,
        category: `fn:${fn.category}`,
      });
    });

    return out;
  }, [nodes]);
}
