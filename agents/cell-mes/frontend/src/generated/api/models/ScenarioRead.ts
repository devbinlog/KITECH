/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Schema for reading a scenario.
 */
export type ScenarioRead = {
    name: string;
    file_path: string;
    is_active?: boolean;
    id: number;
    product_id: (number | null);
    created_at: string;
};

