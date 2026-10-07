/**
 * validate — derive validation errors per editor node.
 *
 * V1 (M12) checks:
 *   - ScenarioStep
 *     · stepId required + unique across the canvas
 *     · stepName recommended (warning)
 *     · action required (error)
 *     · paramsJson must be parseable JSON when non-empty (error)
 *     · routing.then[].next must reference a step id that exists (error)
 *     · acquire roles reference assets defined in scenarioConfig (warning)
 *   - ScenarioConfig
 *     · scenarioName required (warning)
 *     · assets[].id must be unique (error)
 *
 * Returns a map keyed by editor node id; the page.tsx wires this into
 * each node's `data.errors` so NodeBadge renders the badge.
 *
 * Design Ref: §11 M12 Module, §5.4 Page UI Checklist (validation badge)
 * Plan SC: #8 (validation badge + 토스트 응답)
 */

import type { Node } from "reactflow";

import type {
  EditorNodeData,
  RoutingValue,
  ScenarioConfigData,
  ScenarioStepData,
  ValidationError,
} from "@/types/scenario";

export function validateAll(
  nodes: Node<EditorNodeData>[]
): Record<string, ValidationError[]> {
  const out: Record<string, ValidationError[]> = {};

  // Pre-pass: collect step ids + asset ids for cross-checks.
  const stepIds = new Set<string>();
  const stepIdCounts = new Map<string, number>();
  const assetIds = new Set<string>();

  for (const n of nodes) {
    const d = n.data;
    if (!d) continue;
    if (d.kind === "scenarioStep") {
      const sd = d as ScenarioStepData;
      if (sd.stepId) {
        stepIds.add(sd.stepId);
        stepIdCounts.set(sd.stepId, (stepIdCounts.get(sd.stepId) ?? 0) + 1);
      }
    } else if (d.kind === "scenarioConfig") {
      const cd = d as ScenarioConfigData;
      cd.assets.forEach((a) => {
        if (a.id) assetIds.add(a.id);
      });
    }
  }

  for (const n of nodes) {
    const errs: ValidationError[] = [];
    const d = n.data;
    if (!d) {
      out[n.id] = errs;
      continue;
    }

    if (d.kind === "scenarioStep") {
      const sd = d as ScenarioStepData;

      if (!sd.stepId) {
        errs.push({
          field: "stepId",
          message: "Step ID는 필수입니다",
          severity: "error",
        });
      } else if ((stepIdCounts.get(sd.stepId) ?? 0) > 1) {
        errs.push({
          field: "stepId",
          message: `중복된 Step ID: ${sd.stepId}`,
          severity: "error",
        });
      }

      if (!sd.stepName) {
        errs.push({
          field: "stepName",
          message: "Step name이 비어 있습니다",
          severity: "warning",
        });
      }

      if (!sd.action) {
        errs.push({
          field: "action",
          message: "Action은 필수입니다",
          severity: "error",
        });
      }

      if (sd.paramsJson && sd.paramsJson.trim()) {
        try {
          const parsed = JSON.parse(sd.paramsJson);
          if (
            parsed === null ||
            typeof parsed !== "object" ||
            Array.isArray(parsed)
          ) {
            errs.push({
              field: "paramsJson",
              message: "params는 객체여야 합니다",
              severity: "error",
            });
          }
        } catch (e) {
          errs.push({
            field: "paramsJson",
            message: `JSON 파싱 실패: ${(e as Error).message}`,
            severity: "error",
          });
        }
      }

      // routing.then[].next references
      (sd.routing?.values ?? []).forEach((r: RoutingValue, ri) => {
        try {
          const actions = JSON.parse(r.thenJson || "[]");
          if (!Array.isArray(actions)) return;
          for (const a of actions) {
            if (a && typeof a === "object" && "next" in a) {
              const tgt = String((a as { next: unknown }).next);
              if (tgt && !stepIds.has(tgt)) {
                errs.push({
                  field: `routing[${ri}].then.next`,
                  message: `존재하지 않는 step id 참조: "${tgt}"`,
                  severity: "error",
                });
              }
            }
          }
        } catch {
          errs.push({
            field: `routing[${ri}].thenJson`,
            message: "thenJson 파싱 실패",
            severity: "error",
          });
        }
      });

      // acquire roles vs assets
      if (assetIds.size > 0) {
        (["main", "sub1", "sub2", "sub3"] as const).forEach((role) => {
          const ids = sd.acquire[role] ?? [];
          for (const id of ids) {
            if (!assetIds.has(id)) {
              errs.push({
                field: `acquire.${role}`,
                message: `정의되지 않은 asset id: "${id}"`,
                severity: "warning",
              });
            }
          }
        });
      }
    } else if (d.kind === "scenarioConfig") {
      const cd = d as ScenarioConfigData;

      if (!cd.scenarioName) {
        errs.push({
          field: "scenarioName",
          message: "Scenario name이 비어 있습니다",
          severity: "warning",
        });
      }

      const seen = new Set<string>();
      const dupes = new Set<string>();
      for (const a of cd.assets) {
        if (!a.id) {
          errs.push({
            field: "assets",
            message: "asset id가 비어 있습니다",
            severity: "error",
          });
          continue;
        }
        if (seen.has(a.id)) {
          dupes.add(a.id);
        } else {
          seen.add(a.id);
        }
      }
      dupes.forEach((id) =>
        errs.push({
          field: "assets",
          message: `중복된 asset id: ${id}`,
          severity: "error",
        })
      );
    }

    out[n.id] = errs;
  }

  return out;
}
