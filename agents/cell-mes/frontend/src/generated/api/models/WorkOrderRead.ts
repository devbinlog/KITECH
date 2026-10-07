/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ProductEmbedded } from './ProductEmbedded';
/**
 * Schema for reading a work order.
 */
export type WorkOrderRead = {
    lot_no: string;
    product_id: number;
    scenario_id?: (number | null);
    target_qty: number;
    qty?: number;
    priority?: number;
    due_date?: (string | null);
    remarks?: (string | null);
    id: number;
    status: string;
    completed_qty?: number;
    current_process?: (string | null);
    start_time?: (string | null);
    end_time?: (string | null);
    created_at: string;
    product?: (ProductEmbedded | null);
};

