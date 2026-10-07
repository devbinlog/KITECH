/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { TraceabilitySummary } from './TraceabilitySummary';
import type { TraceabilityTimelineItem } from './TraceabilityTimelineItem';
/**
 * LOT traceability response
 */
export type TraceabilityResponse = {
    lot_no: string;
    work_order: Record<string, any>;
    product: Record<string, any>;
    scenario: (Record<string, any> | null);
    routing: Array<Record<string, any>>;
    timeline: Array<TraceabilityTimelineItem>;
    summary: TraceabilitySummary;
    errors?: Array<Record<string, string>>;
    partial?: boolean;
};

