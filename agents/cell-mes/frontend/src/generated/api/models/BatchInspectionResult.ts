/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Batch inspection result creation.
 */
export type BatchInspectionResult = {
    inspection_plan_id: number;
    work_order_id: number;
    equipment_id?: (number | null);
    results: Array<Record<string, any>>;
    inspector_name?: (string | null);
    measurement_method?: (string | null);
};

