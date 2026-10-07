/**
 * workflowToEditor — n8n workflow JSON -> React Flow editor state.
 *
 * Shared between useScenarioLoader (initial load) and the M11 import flow
 * so both produce identical editor state for the same workflow JSON.
 *
 * Design Ref: §3 Data Model, §11 M2/M11 Modules
 */

import type { Edge } from "reactflow";

import type {
  AcquireRoles,
  EditorEdge,
  EditorNode,
  N8nNode,
  N8nWorkflow,
  RoutingValue,
  ScenarioAsset,
  ScenarioConfigData,
  ScenarioStepData,
  StickyColor,
  StickyNoteData,
} from "@/types/scenario";

const STICKY_INT_TO_COLOR: Record<number, StickyColor> = {
  3: "yellow",
  4: "blue",
  5: "green",
  6: "pink",
};

export interface EditorState {
  nodes: EditorNode[];
  edges: EditorEdge[];
}

export function workflowToEditor(workflow: N8nWorkflow): EditorState {
  const nodes: EditorNode[] = workflow.nodes.map(buildEditorNode);
  const byName = new Map(workflow.nodes.map((n) => [n.name, n]));

  const edges: EditorEdge[] = [];
  Object.entries(workflow.connections ?? {}).forEach(([sourceName, conn]) => {
    const sourceNode = byName.get(sourceName);
    if (!sourceNode) return;
    const sourceRoutes =
      ((sourceNode.parameters?.routing as { values?: RoutingValue[] })
        ?.values as RoutingValue[] | undefined) ?? [];
    const buckets = conn?.main ?? [];
    buckets.forEach((bucket, outputIndex) => {
      const when = sourceRoutes[outputIndex]?.when ?? null;
      bucket.forEach((target, ti) => {
        const targetNode = byName.get(target.node);
        if (!targetNode) return;
        const e: Edge = {
          id: `e-${sourceNode.id}-${outputIndex}-${targetNode.id}-${ti}`,
          source: sourceNode.id,
          target: targetNode.id,
          sourceHandle: String(outputIndex),
          targetHandle: "in",
          type: "routing",
          data: { when },
        };
        edges.push(e);
      });
    });
  });

  return { nodes, edges };
}

function buildEditorNode(n: N8nNode): EditorNode {
  const kind = mapN8nTypeToEditorKind(n.type);
  const position = { x: n.position[0], y: n.position[1] };

  switch (kind) {
    case "manualTrigger":
      return {
        id: n.id,
        type: "manualTrigger",
        position,
        data: { kind: "manualTrigger" },
      };

    case "scenarioConfig": {
      const params = n.parameters ?? {};
      const assetsRaw = (params.assets as { asset?: ScenarioAsset[] })?.asset;
      const data: ScenarioConfigData = {
        kind: "scenarioConfig",
        scenarioName: String(params.scenarioName ?? ""),
        aasFilePath: String(params.aasFilePath ?? ""),
        baseUrl: String(params.baseUrl ?? ""),
        assets: Array.isArray(assetsRaw)
          ? assetsRaw.map((a) => ({
              id: String(a?.id ?? ""),
              name: String(a?.name ?? ""),
            }))
          : [],
      };
      return { id: n.id, type: "scenarioConfig", position, data };
    }

    case "scenarioStep": {
      const params = n.parameters ?? {};
      const acquireRoles =
        ((params.acquire as { roles?: Record<string, string> })?.roles as
          | Record<string, string>
          | undefined) ?? {};
      const acquire: AcquireRoles = {};
      (["main", "sub1", "sub2", "sub3"] as const).forEach((role) => {
        const v = acquireRoles[role];
        if (v) {
          acquire[role] = v
            .split(",")
            .map((s) => s.trim())
            .filter(Boolean);
        }
      });
      const routingValues =
        ((params.routing as { values?: RoutingValue[] })?.values as
          | RoutingValue[]
          | undefined) ?? [];
      const data: ScenarioStepData = {
        kind: "scenarioStep",
        stepId: String(params.stepId ?? ""),
        stepName: String(params.stepName ?? ""),
        action: String(params.action ?? ""),
        paramsJson: String(params.paramsJson ?? "{}"),
        acquire,
        routing: { values: routingValues },
      };
      return { id: n.id, type: "scenarioStep", position, data };
    }

    case "stickyNote": {
      const params = n.parameters ?? {};
      const colorInt = Number(params.color ?? 3);
      const color: StickyColor = STICKY_INT_TO_COLOR[colorInt] ?? "yellow";
      const data: StickyNoteData = {
        kind: "stickyNote",
        text: String(params.content ?? ""),
        width: Number(params.width ?? 240),
        height: Number(params.height ?? 180),
        color,
      };
      return { id: n.id, type: "stickyNote", position, data };
    }
  }
}

export function mapN8nTypeToEditorKind(
  type: string
):
  | "manualTrigger"
  | "scenarioConfig"
  | "scenarioStep"
  | "stickyNote" {
  if (type === "n8n-nodes-base.manualTrigger") return "manualTrigger";
  if (type === "n8n-nodes-scenario.scenarioConfig") return "scenarioConfig";
  if (type === "n8n-nodes-scenario.scenarioStep") return "scenarioStep";
  if (type === "n8n-nodes-base.stickyNote") return "stickyNote";
  return "scenarioStep";
}
