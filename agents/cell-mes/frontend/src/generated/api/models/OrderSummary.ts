/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Order summary data
 */
export type OrderSummary = {
    total: number;
    by_status: Record<string, number>;
    completed: number;
    in_progress: number;
    pending: number;
    error: number;
};

