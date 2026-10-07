"use client";

/**
 * NodeSearchPalette — Cmd+K modal for quick navigation / new step creation.
 *
 * V1 (M6) two sections:
 *   1. Existing steps in the current scenario (jump-to-select)
 *   2. Action catalog (insert new ScenarioStep with that action template)
 *
 * Selection (mouse or Enter):
 *   - On a step result -> select that node, close palette
 *   - On an action template -> create a new ScenarioStep node at viewport
 *     center, select it
 *
 * Design Ref: §5.4 Page UI Checklist > Search palette
 *             §11 M6 Module (Node Search Palette)
 */

import { useEffect, useMemo, useRef, useState } from "react";
import type { Node } from "reactflow";
import { useReactFlow } from "reactflow";
import { Search, Activity, Plus } from "lucide-react";

import type {
  ActionCatalogItem,
  EditorNodeData,
  ScenarioStepData,
} from "@/types/scenario";
import { useEditorStore } from "../store/useEditorStore";

interface PaletteProps {
  open: boolean;
  onClose: () => void;
  nodes: Node<EditorNodeData>[];
  setNodes: (
    updater:
      | Node<EditorNodeData>[]
      | ((nds: Node<EditorNodeData>[]) => Node<EditorNodeData>[])
  ) => void;
  actions: ActionCatalogItem[];
  pushSnapshot: () => void;
}

interface MatchEntry {
  kind: "step" | "action";
  id: string;
  primary: string;
  secondary?: string;
  raw: unknown;
}

function fuzzyMatch(query: string, text: string): boolean {
  if (!query) return true;
  return text.toLowerCase().includes(query.toLowerCase());
}

function freshId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `n-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 9)}`;
}

export function NodeSearchPalette({
  open,
  onClose,
  nodes,
  setNodes,
  actions,
  pushSnapshot,
}: PaletteProps) {
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const setSelectedNodeIds = useEditorStore((s) => s.setSelectedNodeIds);
  const markDirty = useEditorStore((s) => s.markDirty);
  const rf = useReactFlow();

  useEffect(() => {
    if (open) {
      setQuery("");
      setActiveIndex(0);
      // Defer focus to next tick after render.
      setTimeout(() => inputRef.current?.focus(), 0);
    }
  }, [open]);

  const matches = useMemo<MatchEntry[]>(() => {
    const out: MatchEntry[] = [];
    for (const n of nodes) {
      if (n.data?.kind !== "scenarioStep") continue;
      const d = n.data as ScenarioStepData;
      const txt = `${d.stepId} ${d.stepName ?? ""} ${d.action ?? ""}`;
      if (fuzzyMatch(query, txt)) {
        out.push({
          kind: "step",
          id: n.id,
          primary: `${d.stepId}  ${d.stepName ?? ""}`,
          secondary: d.action,
          raw: n,
        });
      }
    }
    for (const a of actions) {
      const txt = `${a.key} ${a.category} ${a.description}`;
      if (fuzzyMatch(query, txt)) {
        out.push({
          kind: "action",
          id: a.key,
          primary: a.description,
          secondary: `${a.category} • ${a.key}`,
          raw: a,
        });
      }
    }
    return out;
  }, [nodes, actions, query]);

  useEffect(() => {
    setActiveIndex(0);
  }, [matches.length]);

  const choose = (entry: MatchEntry) => {
    if (entry.kind === "step") {
      setSelectedNodeIds([entry.id]);
      // Center viewport on the picked node if possible.
      const n = entry.raw as Node<EditorNodeData>;
      try {
        rf.setCenter(n.position.x + 100, n.position.y + 50, {
          zoom: rf.getZoom(),
          duration: 300,
        });
      } catch {
        /* ignore */
      }
      onClose();
      return;
    }
    // Insert a new ScenarioStep at viewport center.
    const action = entry.raw as ActionCatalogItem;
    pushSnapshot();
    const center = (() => {
      try {
        const v = rf.getViewport();
        return rf.screenToFlowPosition({
          x: window.innerWidth / 2 - v.x,
          y: window.innerHeight / 2 - v.y,
        });
      } catch {
        return { x: 400, y: 400 };
      }
    })();
    const data: ScenarioStepData = {
      kind: "scenarioStep",
      stepId: nextStepId(nodes),
      stepName: action.description,
      action: action.key,
      paramsJson: "{}",
      acquire: {},
      routing: { values: [] },
    };
    const newNode: Node<EditorNodeData> = {
      id: freshId(),
      type: "scenarioStep",
      position: center,
      data,
    };
    setNodes((nds) => [...nds, newNode]);
    setSelectedNodeIds([newNode.id]);
    markDirty();
    onClose();
  };

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/30 pt-24"
      onClick={onClose}
    >
      <div
        className="w-[640px] max-w-[90vw] overflow-hidden rounded-lg bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-2 border-b border-gray-200 px-4 py-3">
          <Search className="h-4 w-4 text-gray-400" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Escape") onClose();
              if (e.key === "ArrowDown") {
                e.preventDefault();
                setActiveIndex((i) => Math.min(matches.length - 1, i + 1));
              }
              if (e.key === "ArrowUp") {
                e.preventDefault();
                setActiveIndex((i) => Math.max(0, i - 1));
              }
              if (e.key === "Enter") {
                if (matches[activeIndex]) {
                  e.preventDefault();
                  choose(matches[activeIndex]);
                }
              }
            }}
            placeholder="step ID, name, action 검색…"
            className="flex-1 text-sm outline-none"
          />
          <kbd className="rounded border border-gray-200 px-1 py-0.5 text-[10px] text-gray-500">
            Esc
          </kbd>
        </div>
        <div className="max-h-[60vh] overflow-y-auto">
          {matches.length === 0 && (
            <div className="px-4 py-8 text-center text-sm text-gray-500">
              결과 없음
            </div>
          )}
          {matches.map((m, i) => (
            <button
              key={`${m.kind}-${m.id}`}
              onClick={() => choose(m)}
              onMouseEnter={() => setActiveIndex(i)}
              className={`flex w-full items-start gap-2 px-4 py-2 text-left transition-colors ${
                i === activeIndex ? "bg-blue-50" : "hover:bg-gray-50"
              }`}
            >
              <span className="mt-0.5">
                {m.kind === "step" ? (
                  <Activity size={14} className="text-green-600" />
                ) : (
                  <Plus size={14} className="text-blue-600" />
                )}
              </span>
              <span className="min-w-0 flex-1">
                <span className="block truncate text-sm font-medium text-gray-900">
                  {m.primary}
                </span>
                {m.secondary && (
                  <span className="block truncate font-mono text-[11px] text-gray-500">
                    {m.secondary}
                  </span>
                )}
              </span>
              <span className="self-center text-[10px] uppercase tracking-wider text-gray-400">
                {m.kind === "step" ? "Jump" : "Insert"}
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function nextStepId(nodes: Node<EditorNodeData>[]): string {
  const used = new Set<string>();
  for (const n of nodes) {
    if (n.data?.kind === "scenarioStep") {
      used.add((n.data as ScenarioStepData).stepId);
    }
  }
  let i = used.size + 1;
  while (used.has(`step-${i}`)) i++;
  return `step-${i}`;
}
