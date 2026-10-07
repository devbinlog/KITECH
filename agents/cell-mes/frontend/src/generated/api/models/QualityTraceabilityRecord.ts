/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { InspectionResultResponse } from './InspectionResultResponse';
import type { NonConformanceResponse } from './NonConformanceResponse';
/**
 * Quality traceability record.
 */
export type QualityTraceabilityRecord = {
    serial_no: string;
    work_order_id: number;
    lot_number?: (string | null);
    product_name: string;
    inspection_results?: Array<InspectionResultResponse>;
    ncr_records?: Array<NonConformanceResponse>;
    overall_status: string;
    quality_score?: (number | null);
    traced_at: string;
};

