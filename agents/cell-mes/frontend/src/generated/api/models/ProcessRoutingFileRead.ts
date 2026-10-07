/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Schema for reading a routing file.
 */
export type ProcessRoutingFileRead = {
    file_type?: string;
    file_path: string;
    original_filename?: (string | null);
    compatible_machines?: (Array<string> | null);
    sort_order?: number;
    id: number;
    process_routing_id: number;
    created_at: string;
};
