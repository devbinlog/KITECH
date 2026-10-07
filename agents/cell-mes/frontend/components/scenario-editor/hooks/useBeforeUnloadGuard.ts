"use client";

/**
 * useBeforeUnloadGuard — browser-level dirty warning on close/refresh.
 *
 * Pairs with the in-app `confirmCancel` modal (which handles in-SPA navigation).
 * `beforeunload` covers reload/close/external navigation.
 *
 * Design Ref: §5.4 Dirty/Navigation, Plan SC #11
 */

import { useEffect } from "react";

export function useBeforeUnloadGuard(active: boolean) {
  useEffect(() => {
    if (!active) return;
    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      // Modern browsers ignore the message but require returnValue.
      e.returnValue = "";
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [active]);
}
