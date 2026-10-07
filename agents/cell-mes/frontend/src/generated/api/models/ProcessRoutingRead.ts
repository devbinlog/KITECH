/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ProcessRoutingFileRead } from './ProcessRoutingFileRead';
import type { StdProcessRead } from './StdProcessRead';
/**
 * Schema for reading a routing.
 */
export type ProcessRoutingRead = {
    std_process_id: number;
    sequence: number;
    remarks?: (string | null);
    id: number;
    product_id: number;
    files?: Array<ProcessRoutingFileRead>;
    std_process?: (StdProcessRead | null);
    created_at: string;
};

