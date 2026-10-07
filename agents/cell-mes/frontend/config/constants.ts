/**
 * Application-wide constants for the Cell-MES frontend.
 *
 * Centralizes polling intervals, stale times, timeouts, and pagination limits
 * to avoid magic numbers scattered across components.
 */

/** Polling intervals for React Query refetchInterval (milliseconds). */
export const POLLING = {
  /** Real-time data: dashboard, equipment list, production orders */
  FAST: 5_000,
  /** Lot trace updates */
  LOT_TRACE: 10_000,
  /** Analytics, health checks, quality dashboard */
  NORMAL: 30_000,
  /** Resource utilization, quality connection, quota status */
  SLOW: 60_000,
} as const;

/** Stale time for React Query (milliseconds). */
export const STALE_TIME = {
  /** Default (5 seconds) */
  DEFAULT: 5_000,
  /** Short-lived data: quota status (30 seconds) */
  SHORT: 30_000,
  /** Medium: query history, product connections (5 minutes) */
  MEDIUM: 5 * 60 * 1_000,
  /** Long: favorites (10 minutes) */
  LONG: 10 * 60 * 1_000,
} as const;

/** API request timeouts (milliseconds). */
export const API_TIMEOUT = {
  /** Default for LLM calls */
  LLM: 30_000,
} as const;

/** Pagination defaults. */
export const PAGE_SIZE = {
  /** Default list limit */
  DEFAULT: 20,
  /** Query history, NLM history */
  HISTORY: 50,
  /** Work orders list */
  WORK_ORDERS: 100,
  /** Dashboard: fetch all orders for stats */
  ALL_ORDERS: 1_000,
} as const;
