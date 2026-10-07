/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { BatchInspectionResponse } from '../models/BatchInspectionResponse';
import type { BatchInspectionResult } from '../models/BatchInspectionResult';
import type { InspectionPlanCreate } from '../models/InspectionPlanCreate';
import type { InspectionPlanResponse } from '../models/InspectionPlanResponse';
import type { InspectionPlanUpdate } from '../models/InspectionPlanUpdate';
import type { InspectionPlanWithResults } from '../models/InspectionPlanWithResults';
import type { InspectionResultCreate } from '../models/InspectionResultCreate';
import type { InspectionResultResponse } from '../models/InspectionResultResponse';
import type { NCRStatus } from '../models/NCRStatus';
import type { NonConformanceCreate } from '../models/NonConformanceCreate';
import type { NonConformanceResponse } from '../models/NonConformanceResponse';
import type { NonConformanceUpdate } from '../models/NonConformanceUpdate';
import type { QualityTraceabilityRecord } from '../models/QualityTraceabilityRecord';
import type { SPCAnalysisResult } from '../models/SPCAnalysisResult';
import type { SPCCapabilityAnalysis } from '../models/SPCCapabilityAnalysis';
import type { SPCChartWithDataPoints } from '../models/SPCChartWithDataPoints';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class QualityService {
    /**
     * Create Inspection Plan
     * Create a new inspection plan.
     * @param requestBody
     * @returns InspectionPlanResponse Successful Response
     * @throws ApiError
     */
    public static createInspectionPlanApiV1QualityInspectionPlansPost(
        requestBody: InspectionPlanCreate,
    ): CancelablePromise<InspectionPlanResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/quality/inspection-plans',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Inspection Plans By Product
     * Get inspection plans for a specific product.
     * @param productId Product ID
     * @param includeInactive Include inactive plans
     * @returns InspectionPlanWithResults Successful Response
     * @throws ApiError
     */
    public static getInspectionPlansByProductApiV1QualityInspectionPlansProductIdGet(
        productId: number,
        includeInactive: boolean = false,
    ): CancelablePromise<Array<InspectionPlanWithResults>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/quality/inspection-plans/{product_id}',
            path: {
                'product_id': productId,
            },
            query: {
                'include_inactive': includeInactive,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Inspection Plan
     * Update an inspection plan.
     * @param planId Inspection plan ID
     * @param requestBody
     * @returns InspectionPlanResponse Successful Response
     * @throws ApiError
     */
    public static updateInspectionPlanApiV1QualityInspectionPlansPlanIdPut(
        planId: number,
        requestBody: InspectionPlanUpdate,
    ): CancelablePromise<InspectionPlanResponse> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/quality/inspection-plans/{plan_id}',
            path: {
                'plan_id': planId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Inspection Result
     * Create a new inspection result.
     * @param requestBody
     * @returns InspectionResultResponse Successful Response
     * @throws ApiError
     */
    public static createInspectionResultApiV1QualityInspectionResultsPost(
        requestBody: InspectionResultCreate,
    ): CancelablePromise<InspectionResultResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/quality/inspection-results',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Inspection Results
     * Get inspection results with optional filtering.
     * @param workOrderId Filter by work order ID
     * @param inspectionPlanId Filter by inspection plan ID
     * @param serialNo Filter by serial number
     * @param limit Number of results to return
     * @param offset Number of results to skip
     * @returns InspectionResultResponse Successful Response
     * @throws ApiError
     */
    public static getInspectionResultsApiV1QualityInspectionResultsGet(
        workOrderId?: (number | null),
        inspectionPlanId?: (number | null),
        serialNo?: (string | null),
        limit: number = 100,
        offset?: number,
    ): CancelablePromise<Array<InspectionResultResponse>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/quality/inspection-results',
            query: {
                'work_order_id': workOrderId,
                'inspection_plan_id': inspectionPlanId,
                'serial_no': serialNo,
                'limit': limit,
                'offset': offset,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Batch Inspection Results
     * Create multiple inspection results in batch.
     * @param requestBody
     * @returns BatchInspectionResponse Successful Response
     * @throws ApiError
     */
    public static createBatchInspectionResultsApiV1QualityInspectionResultsBatchPost(
        requestBody: BatchInspectionResult,
    ): CancelablePromise<BatchInspectionResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/quality/inspection-results/batch',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Ncr
     * Create a new non-conformance report.
     * @param requestBody
     * @returns NonConformanceResponse Successful Response
     * @throws ApiError
     */
    public static createNcrApiV1QualityNcrPost(
        requestBody: NonConformanceCreate,
    ): CancelablePromise<NonConformanceResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/quality/ncr',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Ncrs
     * Get non-conformance reports with optional filtering.
     * @param status Filter by status
     * @param workOrderId Filter by work order ID
     * @param equipmentId Filter by equipment ID
     * @param assignedTo Filter by assignee
     * @param limit Number of results to return
     * @param offset Number of results to skip
     * @returns NonConformanceResponse Successful Response
     * @throws ApiError
     */
    public static getNcrsApiV1QualityNcrGet(
        status?: (NCRStatus | null),
        workOrderId?: (number | null),
        equipmentId?: (number | null),
        assignedTo?: (string | null),
        limit: number = 100,
        offset?: number,
    ): CancelablePromise<Array<NonConformanceResponse>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/quality/ncr',
            query: {
                'status': status,
                'work_order_id': workOrderId,
                'equipment_id': equipmentId,
                'assigned_to': assignedTo,
                'limit': limit,
                'offset': offset,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Ncr
     * Update a non-conformance report.
     * @param ncrId NCR ID
     * @param requestBody
     * @returns NonConformanceResponse Successful Response
     * @throws ApiError
     */
    public static updateNcrApiV1QualityNcrNcrIdPut(
        ncrId: number,
        requestBody: NonConformanceUpdate,
    ): CancelablePromise<NonConformanceResponse> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/quality/ncr/{ncr_id}',
            path: {
                'ncr_id': ncrId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Spc Charts By Characteristic
     * Get SPC charts for a specific characteristic.
     * @param characteristic Characteristic name
     * @param productId Filter by product ID
     * @returns SPCChartWithDataPoints Successful Response
     * @throws ApiError
     */
    public static getSpcChartsByCharacteristicApiV1QualitySpcChartsCharacteristicGet(
        characteristic: string,
        productId?: (number | null),
    ): CancelablePromise<Array<SPCChartWithDataPoints>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/quality/spc/charts/{characteristic}',
            path: {
                'characteristic': characteristic,
            },
            query: {
                'product_id': productId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Spc Capability Analysis
     * Get SPC capability analysis (Cp, Cpk, Pp, Ppk).
     * @param productId Filter by product ID
     * @param characteristic Filter by characteristic name
     * @returns SPCCapabilityAnalysis Successful Response
     * @throws ApiError
     */
    public static getSpcCapabilityAnalysisApiV1QualitySpcCapabilityGet(
        productId?: (number | null),
        characteristic?: (string | null),
    ): CancelablePromise<Array<SPCCapabilityAnalysis>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/quality/spc/capability',
            query: {
                'product_id': productId,
                'characteristic': characteristic,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Analyze Spc Chart
     * Perform comprehensive SPC analysis including Western Electric Rules.
     * @param chartId SPC chart ID
     * @param recentPoints Number of recent points to analyze
     * @returns SPCAnalysisResult Successful Response
     * @throws ApiError
     */
    public static analyzeSpcChartApiV1QualitySpcChartsChartIdAnalyzePost(
        chartId: number,
        recentPoints: number = 20,
    ): CancelablePromise<SPCAnalysisResult> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/quality/spc/charts/{chart_id}/analyze',
            path: {
                'chart_id': chartId,
            },
            query: {
                'recent_points': recentPoints,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Quality Traceability
     * Get complete quality traceability for a serial number.
     * @param serialNo Serial number to trace
     * @returns QualityTraceabilityRecord Successful Response
     * @throws ApiError
     */
    public static getQualityTraceabilityApiV1QualityTraceabilitySerialNoGet(
        serialNo: string,
    ): CancelablePromise<QualityTraceabilityRecord> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/quality/traceability/{serial_no}',
            path: {
                'serial_no': serialNo,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Quality Dashboard Summary
     * Get quality dashboard summary statistics.
     * @param days Number of days to analyze
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getQualityDashboardSummaryApiV1QualityDashboardSummaryGet(
        days: number = 7,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/quality/dashboard/summary',
            query: {
                'days': days,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
