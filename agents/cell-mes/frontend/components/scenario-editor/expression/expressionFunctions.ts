/**
 * expressionFunctions — built-in helpers exposed in expressions.
 *
 * Mirrors the n8n custom node runtime (see agents/n8n-yaml/custom-nodes/
 * n8n-nodes-scenario/) which evaluates `{{ ... }}` templates with these
 * common functions. Keeping this list in sync with the runtime is critical
 * for autocomplete fidelity.
 *
 * Design Ref: §11 M7 Module
 * Plan SC: #7 (paramsJson `{{$` 입력 시 expression suggestion)
 */

export interface ExpressionFunction {
  signature: string;
  description: string;
  category: "time" | "id" | "string" | "math" | "json";
}

export const EXPRESSION_FUNCTIONS: ExpressionFunction[] = [
  // Time
  {
    signature: "now()",
    description: "현재 시각 (ISO 8601 문자열)",
    category: "time",
  },
  {
    signature: "today()",
    description: "오늘 날짜 (YYYY-MM-DD)",
    category: "time",
  },
  {
    signature: "timestamp()",
    description: "Unix epoch (ms)",
    category: "time",
  },
  // ID
  {
    signature: "uuid()",
    description: "UUID v4 생성",
    category: "id",
  },
  {
    signature: "shortId(n)",
    description: "짧은 랜덤 ID (n자, 기본 8)",
    category: "id",
  },
  // String
  {
    signature: "upper(s)",
    description: "대문자 변환",
    category: "string",
  },
  {
    signature: "lower(s)",
    description: "소문자 변환",
    category: "string",
  },
  {
    signature: "format(template, ...args)",
    description: "%s/%d 자리표시 포매팅",
    category: "string",
  },
  // Math
  {
    signature: "min(a, b)",
    description: "최솟값",
    category: "math",
  },
  {
    signature: "max(a, b)",
    description: "최댓값",
    category: "math",
  },
  {
    signature: "round(x)",
    description: "정수 반올림",
    category: "math",
  },
  // JSON
  {
    signature: "json(value)",
    description: "JSON 문자열로 직렬화",
    category: "json",
  },
];
