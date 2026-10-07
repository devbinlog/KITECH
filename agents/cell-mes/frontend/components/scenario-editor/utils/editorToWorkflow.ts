/**
 * editorToWorkflow — apply React Flow editor edits onto the base n8n workflow.
 *
 * V1 (M3) responsibility: per-node parameter patches and position updates.
 * Connections are kept from the base workflow (M5+M11 will handle full
 * structural rebuilds when nodes are added/removed via the editor).
 *
 * Design Ref: §11 M3 Implementation Guide, §3 Data Model (n8n parameters)
 */

import type { Node } from "reactflow";

import type {
  AcquireRoles,
  EditorNodeData,
  N8nNode,
  N8nWorkflow,
  ScenarioConfigData,
  ScenarioStepData,
  StickyNoteData,
  StickyColor,
} from "@/types/scenario";

const STICKY_NAME_TO_INT: Record<StickyColor, number> = {
  yellow: 3,
  blue: 4,
  green: 5,
  pink: 6,
};

/** Mirror of server-side acquire.roles shape: {main: "ANT,UR", sub1: "..."}. */
function rolesToCommaString(acquire: AcquireRoles): Record<string, string> {
  const out: Record<string, string> = {};
  (["main", "sub1", "sub2", "sub3"] as const).forEach((role) => {
    const ids = acquire[role] ?? [];
    if (ids.length > 0) out[role] = ids.join(",");
  });
  return out;
}

export function applyEditsToWorkflow(
  base: N8nWorkflow,
  editorNodes: Node<EditorNodeData>[]
): N8nWorkflow {
  const byId = new Map(editorNodes.map((n) => [n.id, n]));

  const updatedNodes: N8nNode[] = base.nodes.map((orig) => {
    const editor = byId.get(orig.id);
    if (!editor) return orig;

    const position: [number, number] = [
      Math.round(editor.position.x),
      Math.round(editor.position.y),
    ];
    const data = editor.data;
    if (!data) return { ...orig, position };

    switch (data.kind) {
      case "scenarioStep": {
        const d = data as ScenarioStepData;
        return {
          ...orig,
          position,
          parameters: {
            ...orig.parameters,
            stepId: d.stepId,
            stepName: d.stepName,
            action: d.action,
            paramsJson: d.paramsJson,
            acquire: { roles: rolesToCommaString(d.acquire) },
            routing: { values: d.routing.values },
          },
        };
      }
      case "scenarioConfig": {
        const d = data as ScenarioConfigData;
        return {
          ...orig,
          position,
          parameters: {
            ...orig.parameters,
            scenarioName: d.scenarioName,
            aasFilePath: d.aasFilePath,
            baseUrl: d.baseUrl,
            assets: { asset: d.assets },
          },
        };
      }
      case "stickyNote": {
        const d = data as StickyNoteData;
        return {
          ...orig,
          position,
          parameters: {
            ...orig.parameters,
            content: d.text,
            width: d.width,
            height: d.height,
            color: STICKY_NAME_TO_INT[d.color] ?? 3,
          },
        };
      }
      default:
        return { ...orig, position };
    }
  });

  return { ...base, nodes: updatedNodes };
}
