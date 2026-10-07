/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Single equipment utilization data
 */
export type UtilizationItem = {
    equipment_id: number;
    equipment_name: string;
    equipment_type: string;
    current_status: string;
    utilization_rate: number;
    run_time_hours: number;
    job_count: number;
    total_ok_qty: number;
    total_ng_qty: number;
    yield_rate: number;
};

