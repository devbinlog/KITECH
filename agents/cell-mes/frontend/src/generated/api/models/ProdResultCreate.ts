/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Schema for creating a production result.
 */
export type ProdResultCreate = {
    process_routing_id?: (number | null);
    target_equipment_id?: (number | null);
    equipment_id?: (number | null);
    ok_qty?: number;
    ng_qty?: number;
    work_order_id: number;
    start_time?: (string | null);
    end_time?: (string | null);
};

