/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { SchedulingRequestParams } from '../models/SchedulingRequestParams';
import type { SchedulingResultRequest } from '../models/SchedulingResultRequest';
import type { SolveScheduleParams } from '../models/SolveScheduleParams';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class SchedulerIntegrationService {
    /**
     * Get Current Schedule
     * 현재 스케줄된 작업지시 현황 조회 (간트 차트용)
     *
     * Args:
     * date: 조회할 날짜 (YYYY-MM-DD), 기본값 오늘
     * include_running: 진행중인 작업지시 포함 여부
     *
     * Returns:
     * - date: 조회 날짜
     * - availability: 설비별 스케줄 슬롯 배열
     * - summary: 전체 통계
     * @param date
     * @param includeRunning
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getCurrentScheduleApiV1SchedulerCurrentScheduleGet(
        date?: (string | null),
        includeRunning: boolean = true,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/scheduler/current-schedule',
            query: {
                'date': date,
                'include_running': includeRunning,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Equipment Availability
     * Get equipment availability for cell-scheduler
     *
     * Returns equipment data in cell-scheduler compatible format:
     * - machine_id, machine_name, machine_type
     * - status, available_from
     * - setup information
     * @param equipmentIds
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getEquipmentAvailabilityApiV1SchedulerEquipmentAvailabilityGet(
        equipmentIds?: (string | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/scheduler/equipment-availability',
            query: {
                'equipment_ids': equipmentIds,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Work Orders For Scheduling
     * Get work orders for cell-scheduler
     *
     * Returns work orders in cell-scheduler compatible format with:
     * - wo_id, product info, quantity
     * - due_date, priority, release_date
     * - jobs with operations
     * @param status
     * @param limit
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getWorkOrdersForSchedulingApiV1SchedulerWorkOrdersGet(
        status?: (string | null),
        limit: number = 100,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/scheduler/work-orders',
            query: {
                'status': status,
                'limit': limit,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Scheduling Request
     * Create a complete scheduling request for cell-scheduler
     *
     * Returns a ready-to-use scheduling request with:
     * - Scheduling horizon
     * - Machines data
     * - Work orders data
     * - Machine type parameters
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createSchedulingRequestApiV1SchedulerCreateRequestPost(
        requestBody: SchedulingRequestParams,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/scheduler/create-request',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Process Scheduling Result
     * Process scheduling result from cell-scheduler
     *
     * Updates work orders with scheduled times and machine assignments.
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static processSchedulingResultApiV1SchedulerProcessResultPost(
        requestBody: SchedulingResultRequest,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/scheduler/process-result',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Machine Type Params
     * Get machine type parameters for cell-scheduler
     *
     * Returns loading types, transport quantities, and timing parameters
     * for each machine type.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getMachineTypeParamsApiV1SchedulerMachineTypeParamsGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/scheduler/machine-type-params',
        });
    }
    /**
     * Solve Schedule
     * Execute scheduling via external cell-scheduler service
     *
     * Creates a scheduling request, calls the scheduler service,
     * and optionally processes the result to update work orders.
     *
     * Params:
     * solver_type: OR_TOOLS (default), GA, SA, TABU, ALNS
     * time_limit_sec: Maximum solve time in seconds
     * include_scheduled: If False (default), exclude already-scheduled work orders to prevent drift
     * auto_apply: If True, immediately update work orders with results
     * If False, only return results for review (default)
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static solveScheduleApiV1SchedulerSolvePost(
        requestBody: SolveScheduleParams,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/scheduler/solve',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
