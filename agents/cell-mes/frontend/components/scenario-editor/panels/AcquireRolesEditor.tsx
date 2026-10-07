"use client";

/**
 * AcquireRolesEditor — chip-style editor for acquire.{main,sub1,sub2,sub3}.
 *
 * Each role is a list of asset ids (strings). Editing UX:
 *   - One row per role
 *   - Inside each row, a comma-separated text input (add/remove implicitly)
 *   - Empty role -> not stored on save (handled elsewhere)
 *
 * Design Ref: §5.4 Page UI Checklist > Parameter Panel (Acquire roles)
 */

import type { AcquireRoles } from "@/types/scenario";

const ROLE_LABELS: Record<keyof AcquireRoles, string> = {
  main: "Main",
  sub1: "Sub 1",
  sub2: "Sub 2",
  sub3: "Sub 3",
};

interface Props {
  value: AcquireRoles;
  onChange: (next: AcquireRoles) => void;
}

export function AcquireRolesEditor({ value, onChange }: Props) {
  const setRole = (
    role: keyof AcquireRoles,
    text: string
  ) => {
    const next: AcquireRoles = { ...value };
    const ids = text
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    if (ids.length === 0) {
      delete next[role];
    } else {
      next[role] = ids;
    }
    onChange(next);
  };

  return (
    <div className="space-y-1.5">
      {(Object.keys(ROLE_LABELS) as Array<keyof AcquireRoles>).map((role) => (
        <div key={role} className="flex items-center gap-2">
          <label className="w-12 text-xs font-medium text-gray-600">
            {ROLE_LABELS[role]}
          </label>
          <input
            type="text"
            value={(value[role] ?? []).join(", ")}
            onChange={(e) => setRole(role, e.target.value)}
            placeholder="asset ids, comma-separated (예: ANT, UR)"
            className="flex-1 rounded border border-gray-300 px-2 py-1 font-mono text-xs focus:border-blue-500 focus:outline-none"
          />
        </div>
      ))}
    </div>
  );
}
