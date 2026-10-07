/**
 * yamlPreview — call cell-mes /converters/n8n-to-yaml to get the YAML text
 * that would be written to disk for the current workflow.
 *
 * Used by:
 *   - YamlPreviewModal (M11) to show a non-destructive preview before save.
 *
 * Design Ref: §4 API Spec, §11 M11 Module
 */

import { n8nToYaml } from "../services/converters";
import type { N8nWorkflow } from "@/types/scenario";

export async function previewYaml(workflow: N8nWorkflow): Promise<string> {
  return n8nToYaml(workflow);
}
