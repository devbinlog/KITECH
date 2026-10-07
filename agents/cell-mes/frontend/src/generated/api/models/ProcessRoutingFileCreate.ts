/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Schema for creating a routing file.
 */
export type ProcessRoutingFileCreate = {
    file_type?: string;
    file_path: string;
    original_filename?: (string | null);
    compatible_machines?: (Array<string> | null);
    sort_order?: number;
};
