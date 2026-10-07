/**
 * Unit tests for editorToWorkflow — applyEditsToWorkflow()
 *
 * applyEditsToWorkflow(base, editorNodes) is a pure function:
 *   - N8nWorkflow + ReactFlow Node<EditorNodeData>[] → N8nWorkflow
 *   - No I/O, no side effects.  No mocks required.
 */

import { describe, it, expect } from "vitest";
import type { Node } from "reactflow";
import { applyEditsToWorkflow } from "@/components/scenario-editor/utils/editorToWorkflow";
import type {
  N8nWorkflow,
  N8nNode,
  EditorNodeData,
  ManualTriggerData,
  ScenarioConfigData,
  ScenarioStepData,
  StickyNoteData,
} from "@/types/scenario";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeWorkflow(nodes: N8nNode[] = []): N8nWorkflow {
  return {
    name: "test-workflow",
    nodes,
    connections: {},
    active: false,
  };
}

function makeN8nNode(overrides: Partial<N8nNode> = {}): N8nNode {
  return {
    id: "node-1",
    name: "Node 1",
    type: "n8n-nodes-base.manualTrigger",
    typeVersion: 1,
    position: [0, 0],
    parameters: {},
    ...overrides,
  };
}

function makeEditorNode<T extends EditorNodeData>(
  id: string,
  data: T,
  position = { x: 100, y: 200 }
): Node<T> {
  return {
    id,
    type: data.kind,
    position,
    data,
  };
}

// ---------------------------------------------------------------------------
// Empty canvas
// ---------------------------------------------------------------------------

describe("applyEditsToWorkflow — empty canvas", () => {
  it("returns a workflow with the same name when given no editor nodes", () => {
    const base = makeWorkflow([]);
    const result = applyEditsToWorkflow(base, []);
    expect(result.name).toBe("test-workflow");
  });

  it("returns an empty nodes array when base has no nodes and editor has no nodes", () => {
    const base = makeWorkflow([]);
    const result = applyEditsToWorkflow(base, []);
    expect(result.nodes).toEqual([]);
  });

  it("preserves connections when base has connections and editor is empty", () => {
    const base: N8nWorkflow = {
      name: "w",
      nodes: [],
      connections: {
        "Node A": { main: [[{ node: "Node B", type: "main", index: 0 }]] },
      },
    };
    const result = applyEditsToWorkflow(base, []);
    expect(result.connections).toEqual(base.connections);
  });

  it("returns a new object (does not mutate the base workflow)", () => {
    const base = makeWorkflow([]);
    const result = applyEditsToWorkflow(base, []);
    expect(result).not.toBe(base);
  });
});

// ---------------------------------------------------------------------------
// Node with no matching editor node — passthrough
// ---------------------------------------------------------------------------

describe("applyEditsToWorkflow — node not in editor nodes", () => {
  it("returns the original node unchanged when no editor node matches its id", () => {
    const orig = makeN8nNode({ id: "n1", position: [10, 20] });
    const base = makeWorkflow([orig]);
    const result = applyEditsToWorkflow(base, []);
    expect(result.nodes[0]).toBe(orig); // same reference — untouched
  });
});

// ---------------------------------------------------------------------------
// ManualTrigger node
// ---------------------------------------------------------------------------

describe("applyEditsToWorkflow — ManualTrigger node", () => {
  it("updates position from editor node", () => {
    const orig = makeN8nNode({ id: "trigger-1", position: [0, 0] });
    const base = makeWorkflow([orig]);
    const data: ManualTriggerData = { kind: "manualTrigger" };
    const editorNode = makeEditorNode("trigger-1", data, { x: 150.7, y: 250.3 });

    const result = applyEditsToWorkflow(base, [editorNode]);
    expect(result.nodes[0].position).toEqual([151, 250]);
  });

  it("rounds fractional positions to integers", () => {
    const orig = makeN8nNode({ id: "t1" });
    const base = makeWorkflow([orig]);
    const data: ManualTriggerData = { kind: "manualTrigger" };
    const editorNode = makeEditorNode("t1", data, { x: 0.4, y: 0.6 });

    const result = applyEditsToWorkflow(base, [editorNode]);
    expect(result.nodes[0].position[0]).toBe(0);
    expect(result.nodes[0].position[1]).toBe(1);
  });

  it("preserves original node id, name, type, and typeVersion", () => {
    const orig = makeN8nNode({
      id: "t1",
      name: "Manual Trigger",
      type: "n8n-nodes-base.manualTrigger",
      typeVersion: 2,
    });
    const base = makeWorkflow([orig]);
    const data: ManualTriggerData = { kind: "manualTrigger" };
    const editorNode = makeEditorNode("t1", data, { x: 50, y: 50 });

    const result = applyEditsToWorkflow(base, [editorNode]);
    const node = result.nodes[0];
    expect(node.id).toBe("t1");
    expect(node.name).toBe("Manual Trigger");
    expect(node.type).toBe("n8n-nodes-base.manualTrigger");
    expect(node.typeVersion).toBe(2);
  });
});

// ---------------------------------------------------------------------------
// ScenarioConfig node
// ---------------------------------------------------------------------------

describe("applyEditsToWorkflow — ScenarioConfig node", () => {
  it("writes scenarioConfig parameters into the output node", () => {
    const orig = makeN8nNode({ id: "cfg-1", parameters: {} });
    const base = makeWorkflow([orig]);
    const data: ScenarioConfigData = {
      kind: "scenarioConfig",
      scenarioName: "My Scenario",
      aasFilePath: "/aas/file.yaml",
      baseUrl: "http://localhost:8000",
      assets: [{ id: "a1", name: "Asset 1" }],
    };
    const editorNode = makeEditorNode("cfg-1", data, { x: 0, y: 0 });

    const result = applyEditsToWorkflow(base, [editorNode]);
    const params = result.nodes[0].parameters as Record<string, unknown>;

    expect(params.scenarioName).toBe("My Scenario");
    expect(params.aasFilePath).toBe("/aas/file.yaml");
    expect(params.baseUrl).toBe("http://localhost:8000");
    expect(params.assets).toEqual({ asset: [{ id: "a1", name: "Asset 1" }] });
  });

  it("wraps assets array inside { asset: [...] } envelope", () => {
    const orig = makeN8nNode({ id: "cfg-1" });
    const base = makeWorkflow([orig]);
    const data: ScenarioConfigData = {
      kind: "scenarioConfig",
      scenarioName: "S",
      aasFilePath: "",
      baseUrl: "",
      assets: [],
    };
    const result = applyEditsToWorkflow(base, [makeEditorNode("cfg-1", data)]);
    expect((result.nodes[0].parameters as Record<string, unknown>).assets).toEqual({ asset: [] });
  });

  it("preserves existing parameters not overwritten by the config kind", () => {
    const orig = makeN8nNode({
      id: "cfg-1",
      parameters: { existingParam: "keep-me" },
    });
    const base = makeWorkflow([orig]);
    const data: ScenarioConfigData = {
      kind: "scenarioConfig",
      scenarioName: "S",
      aasFilePath: "",
      baseUrl: "",
      assets: [],
    };
    const result = applyEditsToWorkflow(base, [makeEditorNode("cfg-1", data)]);
    const params = result.nodes[0].parameters as Record<string, unknown>;
    expect(params.existingParam).toBe("keep-me");
  });
});

// ---------------------------------------------------------------------------
// ScenarioStep node
// ---------------------------------------------------------------------------

describe("applyEditsToWorkflow — ScenarioStep node", () => {
  it("writes all ScenarioStep parameters into the output node", () => {
    const orig = makeN8nNode({ id: "step-1", parameters: {} });
    const base = makeWorkflow([orig]);
    const data: ScenarioStepData = {
      kind: "scenarioStep",
      stepId: "step_001",
      stepName: "Pick Part",
      action: "robot.pick",
      paramsJson: '{"speed": 100}',
      acquire: { main: ["ANT", "UR"] },
      routing: { values: [{ label: "ok", when: "true", thenJson: '{"next":"step_002"}' }] },
    };
    const editorNode = makeEditorNode("step-1", data, { x: 300, y: 400 });

    const result = applyEditsToWorkflow(base, [editorNode]);
    const params = result.nodes[0].parameters as Record<string, unknown>;

    expect(params.stepId).toBe("step_001");
    expect(params.stepName).toBe("Pick Part");
    expect(params.action).toBe("robot.pick");
    expect(params.paramsJson).toBe('{"speed": 100}');
  });

  it("converts acquire.main string array to comma-separated string", () => {
    const orig = makeN8nNode({ id: "step-1" });
    const base = makeWorkflow([orig]);
    const data: ScenarioStepData = {
      kind: "scenarioStep",
      stepId: "s1",
      stepName: "",
      action: "",
      paramsJson: "",
      acquire: { main: ["ANT", "UR", "ROBOT"] },
      routing: { values: [] },
    };
    const result = applyEditsToWorkflow(base, [makeEditorNode("step-1", data)]);
    const acquire = (result.nodes[0].parameters as Record<string, unknown>).acquire as Record<string, unknown>;
    expect(acquire.roles).toEqual({ main: "ANT,UR,ROBOT" });
  });

  it("omits acquire role keys with empty arrays", () => {
    const orig = makeN8nNode({ id: "step-1" });
    const base = makeWorkflow([orig]);
    const data: ScenarioStepData = {
      kind: "scenarioStep",
      stepId: "s1",
      stepName: "",
      action: "",
      paramsJson: "",
      acquire: { main: ["ANT"], sub1: [] },
      routing: { values: [] },
    };
    const result = applyEditsToWorkflow(base, [makeEditorNode("step-1", data)]);
    const acquire = (result.nodes[0].parameters as Record<string, unknown>).acquire as Record<string, unknown>;
    const roles = acquire.roles as Record<string, string>;
    expect(roles.main).toBe("ANT");
    expect(roles.sub1).toBeUndefined();
  });

  it("wraps routing values inside { values: [...] } envelope", () => {
    const orig = makeN8nNode({ id: "step-1" });
    const base = makeWorkflow([orig]);
    const routingValues = [{ label: "ok", when: "res==200", thenJson: "{}" }];
    const data: ScenarioStepData = {
      kind: "scenarioStep",
      stepId: "s1",
      stepName: "",
      action: "",
      paramsJson: "",
      acquire: {},
      routing: { values: routingValues },
    };
    const result = applyEditsToWorkflow(base, [makeEditorNode("step-1", data)]);
    const params = result.nodes[0].parameters as Record<string, unknown>;
    expect(params.routing).toEqual({ values: routingValues });
  });

  it("handles empty acquire object (no role keys)", () => {
    const orig = makeN8nNode({ id: "step-1" });
    const base = makeWorkflow([orig]);
    const data: ScenarioStepData = {
      kind: "scenarioStep",
      stepId: "s1",
      stepName: "",
      action: "",
      paramsJson: "",
      acquire: {},
      routing: { values: [] },
    };
    const result = applyEditsToWorkflow(base, [makeEditorNode("step-1", data)]);
    const acquire = (result.nodes[0].parameters as Record<string, unknown>).acquire as Record<string, unknown>;
    expect(acquire.roles).toEqual({});
  });
});

// ---------------------------------------------------------------------------
// StickyNote node
// ---------------------------------------------------------------------------

describe("applyEditsToWorkflow — StickyNote node", () => {
  it("writes content, width, height into parameters", () => {
    const orig = makeN8nNode({ id: "sticky-1", parameters: {} });
    const base = makeWorkflow([orig]);
    const data: StickyNoteData = {
      kind: "stickyNote",
      text: "Remember to check routing",
      width: 400,
      height: 200,
      color: "yellow",
    };
    const result = applyEditsToWorkflow(base, [makeEditorNode("sticky-1", data)]);
    const params = result.nodes[0].parameters as Record<string, unknown>;

    expect(params.content).toBe("Remember to check routing");
    expect(params.width).toBe(400);
    expect(params.height).toBe(200);
  });

  it("maps color 'yellow' to integer 3", () => {
    const orig = makeN8nNode({ id: "sticky-1" });
    const base = makeWorkflow([orig]);
    const data: StickyNoteData = { kind: "stickyNote", text: "", width: 100, height: 100, color: "yellow" };
    const result = applyEditsToWorkflow(base, [makeEditorNode("sticky-1", data)]);
    expect((result.nodes[0].parameters as Record<string, unknown>).color).toBe(3);
  });

  it("maps color 'blue' to integer 4", () => {
    const orig = makeN8nNode({ id: "sticky-1" });
    const base = makeWorkflow([orig]);
    const data: StickyNoteData = { kind: "stickyNote", text: "", width: 100, height: 100, color: "blue" };
    const result = applyEditsToWorkflow(base, [makeEditorNode("sticky-1", data)]);
    expect((result.nodes[0].parameters as Record<string, unknown>).color).toBe(4);
  });

  it("maps color 'green' to integer 5", () => {
    const orig = makeN8nNode({ id: "sticky-1" });
    const base = makeWorkflow([orig]);
    const data: StickyNoteData = { kind: "stickyNote", text: "", width: 100, height: 100, color: "green" };
    const result = applyEditsToWorkflow(base, [makeEditorNode("sticky-1", data)]);
    expect((result.nodes[0].parameters as Record<string, unknown>).color).toBe(5);
  });

  it("maps color 'pink' to integer 6", () => {
    const orig = makeN8nNode({ id: "sticky-1" });
    const base = makeWorkflow([orig]);
    const data: StickyNoteData = { kind: "stickyNote", text: "", width: 100, height: 100, color: "pink" };
    const result = applyEditsToWorkflow(base, [makeEditorNode("sticky-1", data)]);
    expect((result.nodes[0].parameters as Record<string, unknown>).color).toBe(6);
  });

  it("preserves sticky note position from editor", () => {
    const orig = makeN8nNode({ id: "sticky-1", position: [0, 0] });
    const base = makeWorkflow([orig]);
    const data: StickyNoteData = { kind: "stickyNote", text: "", width: 200, height: 150, color: "pink" };
    const result = applyEditsToWorkflow(base, [makeEditorNode("sticky-1", data, { x: 600, y: 800 })]);
    expect(result.nodes[0].position).toEqual([600, 800]);
  });
});

// ---------------------------------------------------------------------------
// Multi-node workflow
// ---------------------------------------------------------------------------

describe("applyEditsToWorkflow — multi-node workflow", () => {
  it("updates only the nodes that have matching editor nodes", () => {
    const n1 = makeN8nNode({ id: "n1", position: [0, 0] });
    const n2 = makeN8nNode({ id: "n2", position: [100, 100] });
    const base = makeWorkflow([n1, n2]);

    const data: ManualTriggerData = { kind: "manualTrigger" };
    // Only n1 has an editor node
    const result = applyEditsToWorkflow(base, [
      makeEditorNode("n1", data, { x: 999, y: 999 }),
    ]);

    expect(result.nodes[0].position).toEqual([999, 999]); // updated
    expect(result.nodes[1]).toBe(n2);                      // untouched reference
  });

  it("returns correct node count matching the base workflow", () => {
    const nodes = [
      makeN8nNode({ id: "a" }),
      makeN8nNode({ id: "b" }),
      makeN8nNode({ id: "c" }),
    ];
    const base = makeWorkflow(nodes);
    const result = applyEditsToWorkflow(base, []);
    expect(result.nodes.length).toBe(3);
  });

  it("preserves connections untouched when nodes are updated", () => {
    const orig = makeN8nNode({ id: "n1" });
    const base: N8nWorkflow = {
      name: "w",
      nodes: [orig],
      connections: {
        "n1": { main: [[{ node: "n2", type: "main", index: 0 }]] },
      },
    };
    const data: ManualTriggerData = { kind: "manualTrigger" };
    const result = applyEditsToWorkflow(base, [makeEditorNode("n1", data)]);
    expect(result.connections).toEqual(base.connections);
  });
});
