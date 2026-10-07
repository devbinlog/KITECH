"use client";

/**
 * YamlPreviewModal — non-destructive preview of the YAML that would be
 * persisted on save.
 *
 * Triggered from the toolbar button. Calls /converters/n8n-to-yaml with
 * the current merged workflow and shows the result; user can copy to
 * clipboard or close.
 *
 * Design Ref: §11 M11 Module
 */

import { useEffect, useState } from "react";
import { Copy, X, Loader2 } from "lucide-react";

import type { N8nWorkflow } from "@/types/scenario";
import { previewYaml } from "../utils/yamlPreview";

interface Props {
  open: boolean;
  onClose: () => void;
  workflow: N8nWorkflow | null;
}

export function YamlPreviewModal({ open, onClose, workflow }: Props) {
  const [yaml, setYaml] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!open || !workflow) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    setYaml("");
    previewYaml(workflow)
      .then((text) => {
        if (!cancelled) setYaml(text);
      })
      .catch((e: Error) => {
        if (!cancelled) setError(e.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [open, workflow]);

  if (!open) return null;

  const onCopy = async () => {
    try {
      await navigator.clipboard.writeText(yaml);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* ignore */
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      onClick={onClose}
    >
      <div
        className="flex h-[80vh] w-[760px] max-w-[95vw] flex-col overflow-hidden rounded-lg bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
          <h2 className="text-sm font-semibold text-gray-900">
            YAML 미리보기
          </h2>
          <div className="flex items-center gap-1">
            <button
              onClick={onCopy}
              disabled={loading || !!error || !yaml}
              className="inline-flex items-center gap-1 rounded border border-gray-300 px-2 py-1 text-xs hover:bg-gray-100 disabled:opacity-50"
            >
              <Copy size={12} /> {copied ? "복사됨!" : "복사"}
            </button>
            <button
              onClick={onClose}
              className="rounded p-1 text-gray-500 hover:bg-gray-100"
              title="닫기"
            >
              <X size={16} />
            </button>
          </div>
        </div>
        <div className="flex-1 overflow-auto bg-gray-50 p-3 font-mono text-[11px] leading-tight text-gray-800">
          {loading && (
            <div className="flex h-full items-center justify-center">
              <Loader2 className="h-5 w-5 animate-spin text-gray-400" />
            </div>
          )}
          {error && (
            <div className="rounded border border-red-200 bg-red-50 p-3 text-xs text-red-700">
              {error}
            </div>
          )}
          {!loading && !error && yaml && (
            <pre className="whitespace-pre-wrap">{yaml}</pre>
          )}
        </div>
      </div>
    </div>
  );
}
