/**
 * useScenarioSaver — convert React Flow back to YAML and save.
 *
 * Flow:
 *   1. Apply editor edits onto the base workflow (utils/editorToWorkflow)
 *   2. POST /converters/n8n-to-yaml         — YAML text
 *   3. PUT /scenarios/{id}/content          — write to disk
 *   4. Update editor store (markClean, saveStatus)
 *
 * Design Ref: §11 Implementation Guide M1+M3, §2.2 Data Flow
 * Plan SC: #2 (편집/저장 동등)
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { Node } from "reactflow";

import { scenarioService } from "@/services/master";
import { n8nToYaml } from "../services/converters";
import { useEditorStore } from "../store/useEditorStore";
import { applyEditsToWorkflow } from "../utils/editorToWorkflow";
import type {
  EditorNodeData,
  N8nWorkflow,
  ScenarioContentSaveResponse,
} from "@/types/scenario";

export interface SaveArgs {
  scenarioId: number;
  /** Workflow loaded from server (used as the structural base). */
  baseWorkflow: N8nWorkflow;
  /** Current React Flow editor nodes (carry user edits). */
  nodes: Node<EditorNodeData>[];
}

export function useScenarioSaver() {
  const queryClient = useQueryClient();
  const setSaveStatus = useEditorStore((s) => s.setSaveStatus);
  const markClean = useEditorStore((s) => s.markClean);

  return useMutation<ScenarioContentSaveResponse, Error, SaveArgs>({
    mutationFn: async ({ scenarioId, baseWorkflow, nodes }) => {
      setSaveStatus({ kind: "saving" });
      const merged = applyEditsToWorkflow(baseWorkflow, nodes);
      const yamlText = await n8nToYaml(merged);
      return scenarioService.saveContent(scenarioId, yamlText);
    },
    onSuccess: (resp) => {
      markClean();
      queryClient.invalidateQueries({
        queryKey: ["scenario-content", resp.id],
      });
    },
    onError: (err) => {
      setSaveStatus({
        kind: "error",
        message: err?.message ?? "Save failed",
      });
    },
  });
}
