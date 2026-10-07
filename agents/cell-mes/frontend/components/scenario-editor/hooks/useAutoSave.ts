"use client";

/**
 * useAutoSave — debounced auto-save when dirty.
 *
 * V1 (M4): debounce DEFAULT_DELAY_MS after the last change. Cancels any
 * pending save when component unmounts or args change. Skips when:
 *   - dirty is false (nothing to save)
 *   - a manual save is in flight (saver.isPending)
 *   - last save was just successful (avoid bouncing)
 *
 * Design Ref: §11 M4 Module, §5.4 SaveStatusIndicator
 * Plan SC: #12 (Autosave 2s debounce)
 */

import { useEffect, useRef } from "react";

const DEFAULT_DELAY_MS = 2000;

interface Args {
  enabled: boolean;
  dirty: boolean;
  delayMs?: number;
  /** Imperative save trigger; should be safe to call repeatedly. */
  save: () => void;
}

export function useAutoSave({
  enabled,
  dirty,
  delayMs = DEFAULT_DELAY_MS,
  save,
}: Args) {
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const saveRef = useRef(save);
  saveRef.current = save;

  useEffect(() => {
    if (!enabled || !dirty) return;
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => {
      saveRef.current();
    }, delayMs);
    return () => {
      if (timer.current) clearTimeout(timer.current);
    };
  }, [enabled, dirty, delayMs]);
}
