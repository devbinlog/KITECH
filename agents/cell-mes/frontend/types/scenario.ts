/**
 * Scenario domain types for the n8n YAML editor.
 *
 * Design Ref: §3 Data Model
 * Plan SC: #1 (YAML 로드 → 캔버스 정확 표시)
 */

import type { Node, Edge } from "reactflow";

// ===========================================================================
// Scenario YAML domain (server-side schema, 1:1 with scenario_converter.py)
// ===========================================================================

export type AcquireRoles = Partial<
  Record<"main" | "sub1" | "sub2" | "sub3", string[]>
>;

export type StickyColor = "yellow" | "blue" | "pink" | "green";

export interface ScenarioAsset {
  id: string;
  name: string;
}

export type ThenAction =
  | { next: string }
  | { alarm: string }
  | Record<string, unknown>;

export interface RoutingRule {
  when: string | null;
  then: ThenAction[];
}

export interface ScenarioStep {
  id: string;
  name?: string;
  acquire?: AcquireRoles;
  action?: string;
  params?: Record<string, unknown>;
  routing?: RoutingRule[];
}

export interface ScenarioStickyNote {
  x: number;
  y: number;
  w: number;
  h: number;
  text: string;
  color: StickyColor;
}

export interface ScenarioYaml {
  name: string;
  desc?: string;
  assets: ScenarioAsset[];
  steps: ScenarioStep[];
  /** V1 — extension for editor sticky notes. Optional, backward-compat. */
  notes?: ScenarioStickyNote[];
}

// ===========================================================================
// n8n workflow JSON shape (subset we care about)
// ===========================================================================

export interface N8nNode {
  id: string;
  name: string;
  type: string;
  typeVersion: number;
  position: [number, number];
  parameters: Record<string, unknown>;
}

export interface N8nConnections {
  [sourceName: string]: {
    main: Array<Array<{ node: string; type: string; index: number }>>;
  };
}

export interface N8nWorkflow {
  name: string;
  nodes: N8nNode[];
  connections: N8nConnections;
  active?: boolean;
  settings?: Record<string, unknown>;
  id?: string;
  meta?: Record<string, unknown>;
}

// ===========================================================================
// Editor — React Flow node data shapes
// ===========================================================================

export const NODE_TYPES = {
  ManualTrigger: "manualTrigger",
  ScenarioConfig: "scenarioConfig",
  ScenarioStep: "scenarioStep",
  StickyNote: "stickyNote",
} as const;

export type EditorNodeKind =
  (typeof NODE_TYPES)[keyof typeof NODE_TYPES];

export interface ManualTriggerData {
  kind: "manualTrigger";
}

export interface ScenarioConfigData {
  kind: "scenarioConfig";
  scenarioName: string;
  aasFilePath: string;
  baseUrl: string;
  assets: ScenarioAsset[];
}

export interface ScenarioStepData {
  kind: "scenarioStep";
  stepId: string;
  stepName: string;
  action: string;
  /** Stored as string for Monaco editor; parse on save. */
  paramsJson: string;
  acquire: AcquireRoles;
  routing: { values: RoutingValue[] };
  /** Validation errors aggregated by validate.ts (filled later in M3/M5). */
  errors?: ValidationError[];
}

export interface StickyNoteData {
  kind: "stickyNote";
  text: string;
  width: number;
  height: number;
  color: StickyColor;
}

export type EditorNodeData =
  | ManualTriggerData
  | ScenarioConfigData
  | ScenarioStepData
  | StickyNoteData;

export type EditorNode = Node<EditorNodeData>;
export type EditorEdge = Edge;

export interface RoutingValue {
  label: string;
  when: string;
  thenJson: string;
}

export interface ValidationError {
  field: string;
  message: string;
  severity?: "error" | "warning";
}

// ===========================================================================
// API response shapes (M0 contracts)
// ===========================================================================

export interface ScenarioContentSaveResponse {
  id: number;
  file_path: string;
  size_bytes: number;
  saved_at: string;
  backup_created: boolean;
}

export interface ActionCatalogItem {
  key: string;
  category: string;
  description: string;
}

export interface ActionCatalogResponse {
  data: ActionCatalogItem[];
}
