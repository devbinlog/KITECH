/**
 * n8nJsonIO — export the current canvas state to an n8n workflow JSON file
 * and import an n8n workflow JSON back into the editor.
 *
 * Export: downloads the merged workflow (base + editor edits) as a .json
 * file via the user's browser.
 *
 * Import: reads a user-supplied .json file, validates the minimum n8n shape
 * (nodes[]/connections), replaces the canvas with the imported workflow.
 *
 * Design Ref: §11 M11 Module
 */

import type { N8nWorkflow } from "@/types/scenario";

export function exportWorkflowAsJson(
  workflow: N8nWorkflow,
  baseFilename = "scenario"
): void {
  const json = JSON.stringify(workflow, null, 2);
  const blob = new Blob([json], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  // Sanitize filename — strip path separators / quotes.
  const safe = baseFilename.replace(/[\\/"<>:|*?]+/g, "_");
  a.download = `${safe}.workflow.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export class WorkflowImportError extends Error {}

/**
 * Read a File (from <input type=file>) and parse to N8nWorkflow with
 * minimum shape validation (nodes/connections).
 */
export async function importWorkflowFromFile(
  file: File
): Promise<N8nWorkflow> {
  const text = await file.text();
  let parsed: unknown;
  try {
    parsed = JSON.parse(text);
  } catch (e) {
    throw new WorkflowImportError(`JSON 파싱 실패: ${(e as Error).message}`);
  }
  if (!parsed || typeof parsed !== "object") {
    throw new WorkflowImportError("JSON 루트가 객체가 아닙니다");
  }
  const wf = parsed as Record<string, unknown>;
  if (!Array.isArray(wf.nodes)) {
    throw new WorkflowImportError("workflow.nodes 배열이 없습니다");
  }
  if (typeof wf.connections !== "object" || wf.connections === null) {
    // Connections-less workflow is technically allowed; substitute empty {}
    wf.connections = {};
  }
  if (typeof wf.name !== "string") {
    wf.name = "imported";
  }
  return wf as unknown as N8nWorkflow;
}
