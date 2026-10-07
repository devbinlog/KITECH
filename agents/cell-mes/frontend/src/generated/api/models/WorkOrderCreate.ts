/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Schema for creating a work order.
 */
export type WorkOrderCreate = {
    lot_no: string;
    product_id: number;
    scenario_id?: (number | null);
    target_qty: number;
    qty?: number;
    priority?: number;
    due_date?: (string | null);
    remarks?: (string | null);
};

