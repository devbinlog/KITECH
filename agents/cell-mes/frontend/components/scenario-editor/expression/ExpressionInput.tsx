"use client";

/**
 * ExpressionInput — input/textarea with floating expression suggestion popup.
 *
 * Triggers when the user types `{{` (anywhere in the value). Shows up to
 * MAX_VISIBLE filtered suggestions; arrow keys / Enter / Esc to choose;
 * mouse click also works.
 *
 * V1 (M7): no Monaco dependency. The popup is positioned near the cursor by
 * approximating with caret position via a hidden mirror element. For a
 * minimal implementation we simply pin it under the input — good enough
 * UX for now.
 *
 * Design Ref: §11 M7 Module
 * Plan SC: #7 (paramsJson `{{$` 입력 시 expression suggestion)
 */

import { useEffect, useMemo, useRef, useState } from "react";

import type { Suggestion } from "./useExpressionSuggestions";

interface Props {
  value: string;
  onChange: (next: string) => void;
  suggestions: Suggestion[];
  multiline?: boolean;
  rows?: number;
  placeholder?: string;
  className?: string;
  /** Optional — called on focus change for dirty/save coordination. */
  onBlur?: () => void;
}

const MAX_VISIBLE = 8;
const TRIGGER = "{{";

export function ExpressionInput({
  value,
  onChange,
  suggestions,
  multiline = false,
  rows = 3,
  placeholder,
  className,
  onBlur,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement | HTMLTextAreaElement>(null);
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);
  const [triggerStart, setTriggerStart] = useState<number | null>(null);

  // Detect when caret is inside an open `{{...` token; capture the partial
  // identifier the user has typed so far so we can filter suggestions.
  const updateContext = (text: string, caret: number) => {
    const before = text.slice(0, caret);
    const lastTrigger = before.lastIndexOf(TRIGGER);
    const lastClose = before.lastIndexOf("}}");
    if (lastTrigger >= 0 && lastTrigger > lastClose) {
      const partial = before.slice(lastTrigger + TRIGGER.length);
      // Don't auto-open if there's a newline or space already (likely text).
      if (!partial.includes("\n")) {
        setOpen(true);
        setQuery(partial.trim());
        setTriggerStart(lastTrigger);
        setActiveIndex(0);
        return;
      }
    }
    setOpen(false);
    setQuery("");
    setTriggerStart(null);
  };

  const filtered = useMemo(() => {
    const q = query.toLowerCase();
    if (!q) return suggestions.slice(0, MAX_VISIBLE);
    return suggestions
      .filter(
        (s) =>
          s.label.toLowerCase().includes(q) ||
          s.insert.toLowerCase().includes(q) ||
          (s.description?.toLowerCase().includes(q) ?? false)
      )
      .slice(0, MAX_VISIBLE);
  }, [suggestions, query]);

  const apply = (s: Suggestion) => {
    const el = inputRef.current;
    if (!el) return;
    const caret = el.selectionStart ?? value.length;
    const ts = triggerStart ?? caret;
    // Replace from `{{` start through the typed partial up to caret.
    const next = value.slice(0, ts) + s.insert + value.slice(caret);
    onChange(next);
    setOpen(false);
    setQuery("");
    setTriggerStart(null);
    // Move caret to end of inserted text on the next tick.
    setTimeout(() => {
      const target = ts + s.insert.length;
      try {
        el.setSelectionRange(target, target);
        el.focus();
      } catch {
        /* ignore */
      }
    }, 0);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    onChange(e.target.value);
    updateContext(e.target.value, e.target.selectionStart ?? 0);
  };

  const handleKey = (e: React.KeyboardEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    if (!open) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex((i) => Math.min(filtered.length - 1, i + 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((i) => Math.max(0, i - 1));
    } else if (e.key === "Enter" || e.key === "Tab") {
      if (filtered[activeIndex]) {
        e.preventDefault();
        apply(filtered[activeIndex]);
      }
    } else if (e.key === "Escape") {
      e.preventDefault();
      setOpen(false);
    }
  };

  // Close popup on outside click.
  useEffect(() => {
    if (!open) return;
    const onDocClick = (ev: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(ev.target as Node)
      ) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, [open]);

  return (
    <div ref={containerRef} className="relative">
      {multiline ? (
        <textarea
          ref={inputRef as React.RefObject<HTMLTextAreaElement>}
          rows={rows}
          value={value}
          onChange={handleChange}
          onKeyDown={handleKey}
          onBlur={onBlur}
          placeholder={placeholder}
          className={
            className ??
            "w-full rounded border border-gray-300 px-2 py-1 font-mono text-xs focus:border-blue-500 focus:outline-none"
          }
        />
      ) : (
        <input
          ref={inputRef as React.RefObject<HTMLInputElement>}
          type="text"
          value={value}
          onChange={handleChange}
          onKeyDown={handleKey}
          onBlur={onBlur}
          placeholder={placeholder}
          className={
            className ??
            "w-full rounded border border-gray-300 px-2 py-1 font-mono text-xs focus:border-blue-500 focus:outline-none"
          }
        />
      )}
      {open && filtered.length > 0 && (
        <div className="absolute left-0 right-0 top-full z-30 mt-1 max-h-60 overflow-y-auto rounded-md border border-gray-200 bg-white shadow-lg">
          {filtered.map((s, i) => (
            <button
              key={`${s.category}-${s.label}`}
              onClick={(e) => {
                e.preventDefault();
                apply(s);
              }}
              onMouseEnter={() => setActiveIndex(i)}
              onMouseDown={(e) => e.preventDefault()}
              className={`flex w-full items-start justify-between gap-2 px-2 py-1 text-left ${
                i === activeIndex ? "bg-blue-50" : "hover:bg-gray-50"
              }`}
            >
              <span className="min-w-0 flex-1">
                <span className="block font-mono text-[11px] text-gray-900">
                  {s.label}
                </span>
                {s.description && (
                  <span className="block truncate text-[10px] text-gray-500">
                    {s.description}
                  </span>
                )}
              </span>
              <span className="self-center text-[9px] uppercase tracking-wider text-gray-400">
                {s.category}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
