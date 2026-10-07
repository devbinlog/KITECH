/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ProcessRoutingFileCreate } from './ProcessRoutingFileCreate';
/**
 * Schema for creating a routing with files.
 */
export type ProcessRoutingCreate = {
    std_process_id: number;
    sequence: number;
    remarks?: (string | null);
    files?: Array<ProcessRoutingFileCreate>;
};

