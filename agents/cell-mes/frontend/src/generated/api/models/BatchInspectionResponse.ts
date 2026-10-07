/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { InspectionResultResponse } from './InspectionResultResponse';
/**
 * Batch inspection result response.
 */
export type BatchInspectionResponse = {
    created_count: number;
    failed_count: number;
    created_results?: Array<InspectionResultResponse>;
    errors?: Array<string>;
};

