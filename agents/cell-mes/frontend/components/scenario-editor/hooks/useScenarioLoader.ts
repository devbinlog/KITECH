/**
 * useScenarioLoader — load existing scenario YAML and convert to React Flow.
 *
 * Flow:
 *   1. GET /scenarios/{id}                — scenario meta
 *   2. GET /scenarios/{id}/content        — current YAML or parsed content
 *   3. POST /converters/yaml-to-n8n       — workflow JSON
 *   4. Map workflow nodes/connections to React Flow Node[]/Edge[]
 *
 * Design Ref: §11 Implementation Guide M1+M2, §2.2 Data Flow
 * Plan SC: #1 (YAML 로드 → 캔버스 정확 표시)
 */

import { useQuery } from "@tanstack/react-query";

import { scenarioService } from "@/services/master";
import { yamlToN8n } from "../services/converters";
import { workflowToEditor } from "../utils/workflowToEditor";
import type { Scenario } from "@/types";
import type {
  EditorEdge,
  EditorNode,
  N8nWorkflow,
} from "@/types/scenario";

// JSON is a strict subset of YAML 1.2, so JSON.stringify produces valid YAML
// for the server's yaml.safe_load. M1 keeps this minimal; a proper structured
// YAML dump (preserving comments, flow-style for params) lands in M11/M12.
function dumpToYamlText(value: unknown): string {
  return JSON.stringify(value, null, 2);
}

export interface LoadedScenario {
  scenarioId: number;
  scenarioName: string;
  filePath: string;
  yamlText: string;
  workflow: N8nWorkflow;
  nodes: EditorNode[];
  edges: EditorEdge[];
}

async function loadScenario(scenarioId: number): Promise<LoadedScenario> {
  // 1. Meta
  const scenario: Scenario = await scenarioService.getById(scenarioId);

  // 2. Content (server returns { content: <parsed dict> })
  const contentResp = await scenarioService.getContent(scenarioId);
  const parsed = contentResp.content;
  if (!parsed) {
    throw new Error(
      contentResp.error ?? "Scenario file not found or empty content"
    );
  }
  const yamlText = dumpToYamlText(parsed);

  // 3. YAML -> n8n workflow JSON
  const workflow = await yamlToN8n(yamlText);

  // 4. Map to React Flow nodes/edges with typed data per kind (shared util).
  const { nodes, edges } = workflowToEditor(workflow);

  return {
    scenarioId,
    scenarioName: scenario.name,
    filePath: scenario.file_path,
    yamlText,
    workflow,
    nodes,
    edges,
  };
}

export function useScenarioLoader(scenarioId: number | null) {
  return useQuery<LoadedScenario, Error>({
    queryKey: ["scenario-content", scenarioId],
    queryFn: () => loadScenario(scenarioId as number),
    enabled: scenarioId != null,
    staleTime: Infinity,
    retry: 1,
  });
}
