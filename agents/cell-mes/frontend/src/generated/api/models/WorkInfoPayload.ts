/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { LogisticsInfo } from './LogisticsInfo';
import type { ProcessingStep } from './ProcessingStep';
/**
 * Unified work info payload for middleware.
 */
export type WorkInfoPayload = {
    job_id: string;
    product_code: string;
    product_name: string;
    target_qty: number;
    logistics?: (LogisticsInfo | null);
    processing_steps?: Array<ProcessingStep>;
};

