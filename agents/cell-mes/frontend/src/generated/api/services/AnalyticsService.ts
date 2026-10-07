/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DailyStatusResponse } from '../models/DailyStatusResponse';
import type { KPIDashboardResponse } from '../models/KPIDashboardResponse';
import type { TraceabilityResponse } from '../models/TraceabilityResponse';
import type { UtilizationResponse } from '../models/UtilizationResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class AnalyticsService {
    /**
     * Get Kpi Summary
     * KPI summary with OEE metrics for the analytics dashboard.
     * @param dateFrom
     * @param dateTo
     * @param xInternalServiceKey
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getKpiSummaryApiV1AnalyticsKpiSummaryGet(
        dateFrom?: (string | null),
        dateTo?: (string | null),
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/analytics/kpi/summary',
            headers: {
                'X-Internal-Service-Key': xInternalServiceKey,
            },
            query: {
                'date_from': dateFrom,
                'date_to': dateTo,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Equipment Utilization Frontend
     * Equipment utilization list for the equipment analytics page.
     * @param equipmentId
     * @param dateFrom
     * @param dateTo
     * @param period
     * @param xInternalServiceKey
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getEquipmentUtilizationFrontendApiV1AnalyticsEquipmentUtilizationGet(
        equipmentId?: (number | null),
        dateFrom?: (string | null),
        dateTo?: (string | null),
        period: string = 'daily',
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/analytics/equipment/utilization',
            headers: {
                'X-Internal-Service-Key': xInternalServiceKey,
            },
            query: {
                'equipment_id': equipmentId,
                'date_from': dateFrom,
                'date_to': dateTo,
                'period': period,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Equipment Efficiency
     * Individual equipment efficiency details.
     * @param equipmentId
     * @param dateFrom
     * @param dateTo
     * @param xInternalServiceKey
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getEquipmentEfficiencyApiV1AnalyticsEquipmentEfficiencyGet(
        equipmentId?: (number | null),
        dateFrom?: (string | null),
        dateTo?: (string | null),
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/analytics/equipment/efficiency',
            headers: {
                'X-Internal-Service-Key': xInternalServiceKey,
            },
            query: {
                'equipment_id': equipmentId,
                'date_from': dateFrom,
                'date_to': dateTo,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Production Trends Frontend
     * Production trends for the analytics dashboard charts.
     * @param dateFrom
     * @param dateTo
     * @param period
     * @param xInternalServiceKey
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getProductionTrendsFrontendApiV1AnalyticsProductionTrendsGet(
        dateFrom?: (string | null),
        dateTo?: (string | null),
        period: string = 'daily',
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/analytics/production/trends',
            headers: {
                'X-Internal-Service-Key': xInternalServiceKey,
            },
            query: {
                'date_from': dateFrom,
                'date_to': dateTo,
                'period': period,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Resource Utilization
     * Resource utilization for the analytics dashboard.
     * @param dateFrom
     * @param dateTo
     * @param xInternalServiceKey
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getResourceUtilizationApiV1AnalyticsResourcesGet(
        dateFrom?: (string | null),
        dateTo?: (string | null),
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/analytics/resources',
            headers: {
                'X-Internal-Service-Key': xInternalServiceKey,
            },
            query: {
                'date_from': dateFrom,
                'date_to': dateTo,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Lot Traces
     * Paginated lot trace list.
     * @param dateFrom
     * @param dateTo
     * @param page
     * @param limit
     * @param xInternalServiceKey
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listLotTracesApiV1AnalyticsLotTraceGet(
        dateFrom?: (string | null),
        dateTo?: (string | null),
        page: number = 1,
        limit: number = 20,
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/analytics/lot-trace',
            headers: {
                'X-Internal-Service-Key': xInternalServiceKey,
            },
            query: {
                'date_from': dateFrom,
                'date_to': dateTo,
                'page': page,
                'limit': limit,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Lot Trace Detail
     * Single lot trace detail.
     * @param lotNo
     * @param xInternalServiceKey
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getLotTraceDetailApiV1AnalyticsLotTraceLotNoGet(
        lotNo: string,
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/analytics/lot-trace/{lot_no}',
            path: {
                'lot_no': lotNo,
            },
            headers: {
                'X-Internal-Service-Key': xInternalServiceKey,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Lot Trace History
     * Lot processing history with quality checkpoints.
     * @param lotNo
     * @param xInternalServiceKey
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getLotTraceHistoryApiV1AnalyticsLotTraceLotNoHistoryGet(
        lotNo: string,
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/analytics/lot-trace/{lot_no}/history',
            path: {
                'lot_no': lotNo,
            },
            headers: {
                'X-Internal-Service-Key': xInternalServiceKey,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Daily Status
     * Get aggregated daily production status.
     *
     * Combines data from:
     * - Work orders (status distribution, counts)
     * - Production results (quantities, yield rate)
     * - Equipment status (running, idle, error counts)
     *
     * Returns KPIs including completion rate, yield rate, and equipment utilization.
     * @param targetDate Target date in YYYY-MM-DD format (default: today)
     * @param xInternalServiceKey
     * @returns DailyStatusResponse Successful Response
     * @throws ApiError
     */
    public static getDailyStatusApiV1AnalyticsDailyStatusGet(
        targetDate?: (string | null),
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<DailyStatusResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/analytics/daily-status',
            headers: {
                'X-Internal-Service-Key': xInternalServiceKey,
            },
            query: {
                'target_date': targetDate,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Equipment Utilization
     * Get equipment utilization metrics.
     *
     * Calculates utilization rate, run time, and yield for each equipment
     * over the specified period.
     *
     * Includes:
     * - Per-equipment utilization metrics
     * - Summary with top performer and bottleneck identification
     * @param equipmentIds Comma-separated equipment IDs to filter
     * @param days Number of days to analyze (1-90)
     * @param xInternalServiceKey
     * @returns UtilizationResponse Successful Response
     * @throws ApiError
     */
    public static getEquipmentUtilizationApiV1AnalyticsEquipmentUtilizationGet(
        equipmentIds?: (string | null),
        days: number = 7,
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<UtilizationResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/analytics/equipment-utilization',
            headers: {
                'X-Internal-Service-Key': xInternalServiceKey,
            },
            query: {
                'equipment_ids': equipmentIds,
                'days': days,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Kpi Dashboard
     * Get aggregated KPIs for dashboard display.
     *
     * Returns:
     * - Today's KPIs (completion rate, yield rate, production qty)
     * - Weekly trends (average utilization, top/bottom performers)
     * - Current status (active orders, equipment health)
     * @param xInternalServiceKey
     * @returns KPIDashboardResponse Successful Response
     * @throws ApiError
     */
    public static getKpiDashboardApiV1AnalyticsKpisGet(
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<KPIDashboardResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/analytics/kpis',
            headers: {
                'X-Internal-Service-Key': xInternalServiceKey,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Lot Traceability
     * Get full traceability history for a LOT.
     *
     * Combines:
     * - Work order details (status, target quantity)
     * - Product information (name, code)
     * - Process routing (sequence of operations)
     * - Production timeline (results with equipment used)
     * - Summary (yield, equipment list)
     *
     * Use this for quality tracing and production history lookup.
     * @param lotNo
     * @param xInternalServiceKey
     * @returns TraceabilityResponse Successful Response
     * @throws ApiError
     */
    public static getLotTraceabilityApiV1AnalyticsTraceabilityLotNoGet(
        lotNo: string,
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<TraceabilityResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/analytics/traceability/{lot_no}',
            path: {
                'lot_no': lotNo,
            },
            headers: {
                'X-Internal-Service-Key': xInternalServiceKey,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Production Trends
     * Get trend data for charts.
     *
     * Supports multiple metrics and grouping options for
     * flexible chart rendering.
     * @param metric Metric to trend: yield, production, utilization
     * @param days Number of days (1-30)
     * @param groupBy Group by: equipment, product, day
     * @param xInternalServiceKey
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getProductionTrendsApiV1AnalyticsTrendsGet(
        metric: string = 'yield',
        days: number = 7,
        groupBy?: (string | null),
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/analytics/trends',
            headers: {
                'X-Internal-Service-Key': xInternalServiceKey,
            },
            query: {
                'metric': metric,
                'days': days,
                'group_by': groupBy,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
