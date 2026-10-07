"use client";

/**
 * StickyNoteNode — workflow annotation note.
 *
 * V1 (M2) — fixed size from data, color background.
 * V2 (M8) — NodeResizer for drag-resize, double-click inline edit, drag
 *           updates sticky width/height via onResizeEnd.
 *
 * Design Ref: §3 Data Model (StickyNote), §5.4 Page UI Checklist > Nodes,
 *             §11 M8 Module
 */

import { useState } from "react";
import {
  NodeResizer,
  type NodeProps,
  useReactFlow,
  type ResizeParams,
} from "reactflow";

import type { StickyColor, StickyNoteData } from "@/types/scenario";
import { useEditorStore } from "../store/useEditorStore";

const COLOR_CLASSES: Record<StickyColor, string> = {
  yellow: "bg-yellow-100 border-yellow-300 text-yellow-950",
  blue: "bg-blue-100 border-blue-300 text-blue-950",
  pink: "bg-pink-100 border-pink-300 text-pink-950",
  green: "bg-green-100 border-green-300 text-green-950",
};

export function StickyNoteNode({
  id,
  data,
  selected,
}: NodeProps<StickyNoteData>) {
  const colorClass = COLOR_CLASSES[data.color] ?? COLOR_CLASSES.yellow;
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(data.text);
  const { setNodes } = useReactFlow();
  const markDirty = useEditorStore((s) => s.markDirty);

  const commitEdit = () => {
    setEditing(false);
    if (draft !== data.text) {
      setNodes((nds) =>
        nds.map((n) =>
          n.id === id
            ? { ...n, data: { ...n.data, text: draft } }
            : n
        )
      );
      markDirty();
    }
  };

  const onResizeEnd = (_e: unknown, params: ResizeParams) => {
    setNodes((nds) =>
      nds.map((n) =>
        n.id === id
          ? {
              ...n,
              data: {
                ...n.data,
                width: Math.round(params.width),
                height: Math.round(params.height),
              },
            }
          : n
      )
    );
    markDirty();
  };

  return (
    <>
      {/* React Flow's resizer handles — only visible when selected. */}
      <NodeResizer
        isVisible={!!selected}
        minWidth={120}
        minHeight={80}
        onResizeEnd={onResizeEnd}
        lineClassName="!border-blue-400"
        handleClassName="!h-2 !w-2 !border-blue-500 !bg-white"
      />
      <div
        style={{ width: data.width, height: data.height }}
        onDoubleClick={() => {
          setDraft(data.text);
          setEditing(true);
        }}
        className={`overflow-auto whitespace-pre-wrap rounded-md border-2 px-3 py-2 text-xs shadow-sm ${colorClass} ${
          selected ? "ring-2 ring-blue-500" : ""
        }`}
      >
        {editing ? (
          <textarea
            autoFocus
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onBlur={commitEdit}
            onKeyDown={(e) => {
              if (e.key === "Escape") {
                setEditing(false);
                setDraft(data.text);
              }
              if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                commitEdit();
              }
            }}
            className="h-full w-full resize-none bg-transparent text-xs outline-none"
            placeholder="(empty note)"
          />
        ) : data.text ? (
          data.text
        ) : (
          <span className="italic opacity-50">(empty note — 더블클릭으로 편집)</span>
        )}
      </div>
    </>
  );
}
