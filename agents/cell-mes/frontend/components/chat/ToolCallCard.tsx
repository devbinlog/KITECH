'use client';

/**
 * ToolCallCard
 * Displays a tool call event from the AI agent as a collapsible card.
 * Yellow background, monospace font, collapsed by default.
 */

import { useState } from 'react';
import { ChevronDown, ChevronRight, Wrench } from 'lucide-react';

export interface ToolCallData {
  tool_name: string;
  input?: unknown;
  output?: unknown;
}

interface ToolCallCardProps {
  toolCall: ToolCallData;
}

function JsonBlock({ value }: { value: unknown }) {
  const text =
    typeof value === 'string' ? value : JSON.stringify(value, null, 2);
  return (
    <pre className="text-xs font-mono bg-yellow-50 border border-yellow-200 rounded p-2 overflow-x-auto whitespace-pre-wrap break-words max-h-48 text-yellow-900">
      {text}
    </pre>
  );
}

function Section({
  label,
  value,
}: {
  label: string;
  value: unknown;
}) {
  const [open, setOpen] = useState(false);
  const isEmpty = value === undefined || value === null;

  return (
    <div className="mt-1.5">
      <button
        onClick={() => setOpen((v) => !v)}
        disabled={isEmpty}
        className="flex items-center gap-1 text-xs font-semibold text-yellow-800 hover:text-yellow-900 disabled:opacity-40 disabled:cursor-default"
      >
        {open ? (
          <ChevronDown className="h-3 w-3" />
        ) : (
          <ChevronRight className="h-3 w-3" />
        )}
        {label}
        {isEmpty && <span className="font-normal text-yellow-600">(none)</span>}
      </button>
      {open && !isEmpty && (
        <div className="mt-1">
          <JsonBlock value={value} />
        </div>
      )}
    </div>
  );
}

export function ToolCallCard({ toolCall }: ToolCallCardProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="my-1 rounded-lg border border-yellow-300 bg-yellow-50 px-3 py-2 text-xs">
      {/* Header row — always visible */}
      <button
        onClick={() => setExpanded((v) => !v)}
        className="flex items-center gap-2 w-full text-left"
      >
        <span className="flex-shrink-0 w-5 h-5 bg-yellow-400 rounded flex items-center justify-center">
          <Wrench className="h-3 w-3 text-yellow-900" />
        </span>
        <span className="font-mono font-semibold text-yellow-900 truncate flex-1">
          {toolCall.tool_name}
        </span>
        <span className="flex-shrink-0 text-yellow-600">
          {expanded ? (
            <ChevronDown className="h-3.5 w-3.5" />
          ) : (
            <ChevronRight className="h-3.5 w-3.5" />
          )}
        </span>
      </button>

      {/* Expanded detail */}
      {expanded && (
        <div className="mt-2 border-t border-yellow-200 pt-2">
          <Section label="Input" value={toolCall.input} />
          <Section label="Output" value={toolCall.output} />
        </div>
      )}
    </div>
  );
}

export default ToolCallCard;
