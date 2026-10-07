/**
 * Cell-MES converters API wrapper.
 *
 * Exposes:
 *   - yamlToN8n: YAML text -> n8n workflow JSON
 *   - n8nToYaml: n8n workflow JSON -> YAML text
 *
 * Backend: agents/cell-mes/src/app/api/v1/endpoints/converters.py
 * Design Ref: §4 API Specification
 */

import api from "@/lib/axios";

import type { N8nWorkflow } from "@/types/scenario";

/** Convert YAML text to n8n workflow JSON. */
export async function yamlToN8n(
  yamlText: string,
  options?: { aasPath?: string; baseUrl?: string }
): Promise<N8nWorkflow> {
  const aasPath = options?.aasPath ?? "/data/cell1_aas.json";
  const baseUrl = options?.baseUrl ?? "http://localhost:8080";

  const form = new FormData();
  // The backend handler reads `file.filename`; the actual filename only needs
  // to end with .yaml/.yml, contents are parsed regardless.
  form.append(
    "file",
    new Blob([yamlText], { type: "application/x-yaml" }),
    "scenario.yaml"
  );

  const response = await api.post<N8nWorkflow>(
    "/api/v1/converters/yaml-to-n8n",
    form,
    {
      params: { aas_path: aasPath, base_url: baseUrl },
      headers: { "Content-Type": "multipart/form-data" },
    }
  );
  return response.data;
}

/** Convert n8n workflow JSON to YAML text. */
export async function n8nToYaml(workflow: N8nWorkflow): Promise<string> {
  const form = new FormData();
  form.append(
    "file",
    new Blob([JSON.stringify(workflow)], { type: "application/json" }),
    "workflow.json"
  );

  const response = await api.post<string>(
    "/api/v1/converters/n8n-to-yaml",
    form,
    {
      headers: { "Content-Type": "multipart/form-data" },
      // Server returns plain text/yaml; coerce to string.
      responseType: "text",
      transformResponse: [(d) => d],
    }
  );
  return typeof response.data === "string"
    ? response.data
    : String(response.data);
}
