/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { NCRStatus } from './NCRStatus';
/**
 * Update non-conformance schema.
 */
export type NonConformanceUpdate = {
    title?: (string | null);
    description?: (string | null);
    root_cause?: (string | null);
    corrective_action?: (string | null);
    severity?: (string | null);
    category?: (string | null);
    status?: (NCRStatus | null);
    assigned_to?: (string | null);
    due_date?: (string | null);
};

