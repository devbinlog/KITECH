/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { PaginatedResponse_ProdResultRead_ } from '../models/PaginatedResponse_ProdResultRead_';
import type { PaginatedResponse_WorkOrderRead_ } from '../models/PaginatedResponse_WorkOrderRead_';
import type { ProdResultCreate } from '../models/ProdResultCreate';
import type { ProdResultRead } from '../models/ProdResultRead';
import type { WorkInfoPayload } from '../models/WorkInfoPayload';
import type { WorkOrderCreate } from '../models/WorkOrderCreate';
import type { WorkOrderRead } from '../models/WorkOrderRead';
import type { WorkOrderStatusUpdate } from '../models/WorkOrderStatusUpdate';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ProductionService {
    /**
     * List Work Orders
     * List work orders with pagination and filtering.
     *
     * View presets:
     * - today: 오늘 계획된 작업 (진행중/대기)
     * - upcoming: 미래 계획 + 미스케줄 작업
     * - active: 진행중/일시정지 작업
     * - all: 전체 작업
     * @param status
     * @param page 페이지 번호
     * @param limit 페이지당 항목 수
     * @param view 뷰 프리셋: today, upcoming, active, all
     * @param dateFrom 시작 날짜
     * @param dateTo 종료 날짜
     * @param sortBy 정렬 기준: start_time, due_date, priority, created_at
     * @param sortOrder 정렬 순서: asc, desc
     * @param xInternalServiceKey
     * @returns PaginatedResponse_WorkOrderRead_ Successful Response
     * @throws ApiError
     */
    public static listWorkOrdersApiV1ProductionOrdersGet(
        status?: (string | null),
        page: number = 1,
        limit: number = 30,
        view?: (string | null),
        dateFrom?: (string | null),
        dateTo?: (string | null),
        sortBy: string = 'start_time',
        sortOrder: string = 'asc',
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<PaginatedResponse_WorkOrderRead_> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/production/orders',
            headers: {
                'X-Internal-Service-Key': xInternalServiceKey,
            },
            query: {
                'status': status,
                'page': page,
                'limit': limit,
                'view': view,
                'date_from': dateFrom,
                'date_to': dateTo,
                'sort_by': sortBy,
                'sort_order': sortOrder,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Work Order
     * Create a new work order.
     * @param requestBody
     * @param xInternalServiceKey
     * @returns WorkOrderRead Successful Response
     * @throws ApiError
     */
    public static createWorkOrderApiV1ProductionOrdersPost(
        requestBody: WorkOrderCreate,
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<WorkOrderRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/production/orders',
            headers: {
                'X-Internal-Service-Key': xInternalServiceKey,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Work Order
     * Get a work order by ID.
     * @param orderId
     * @param xInternalServiceKey
     * @returns WorkOrderRead Successful Response
     * @throws ApiError
     */
    public static getWorkOrderApiV1ProductionOrdersOrderIdGet(
        orderId: number,
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<WorkOrderRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/production/orders/{order_id}',
            path: {
                'order_id': orderId,
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
     * Update Work Order Status
     * Update work order status (state machine).
     * @param orderId
     * @param requestBody
     * @param xInternalServiceKey
     * @returns WorkOrderRead Successful Response
     * @throws ApiError
     */
    public static updateWorkOrderStatusApiV1ProductionOrdersOrderIdStatusPatch(
        orderId: number,
        requestBody: WorkOrderStatusUpdate,
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<WorkOrderRead> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/production/orders/{order_id}/status',
            path: {
                'order_id': orderId,
            },
            headers: {
                'X-Internal-Service-Key': xInternalServiceKey,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Work Info
     * Get unified work info payload for middleware.
     *
     * Assembles routing + files + scenario into a single payload.
     * @param lotNo
     * @param xInternalServiceKey
     * @returns WorkInfoPayload Successful Response
     * @throws ApiError
     */
    public static getWorkInfoApiV1ProductionMiddlewareWorkInfoGet(
        lotNo: string,
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<WorkInfoPayload> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/production/middleware/work-info',
            headers: {
                'X-Internal-Service-Key': xInternalServiceKey,
            },
            query: {
                'lot_no': lotNo,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Production Results
     * List production results with pagination.
     * @param workOrderId
     * @param page 페이지 번호
     * @param limit 페이지당 항목 수
     * @param xInternalServiceKey
     * @returns PaginatedResponse_ProdResultRead_ Successful Response
     * @throws ApiError
     */
    public static listProductionResultsApiV1ProductionResultsGet(
        workOrderId?: (number | null),
        page: number = 1,
        limit: number = 30,
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<PaginatedResponse_ProdResultRead_> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/production/results',
            headers: {
                'X-Internal-Service-Key': xInternalServiceKey,
            },
            query: {
                'work_order_id': workOrderId,
                'page': page,
                'limit': limit,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Production Result
     * Record a production result.
     * @param requestBody
     * @param xInternalServiceKey
     * @returns ProdResultRead Successful Response
     * @throws ApiError
     */
    public static createProductionResultApiV1ProductionResultsPost(
        requestBody: ProdResultCreate,
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<ProdResultRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/production/results',
            headers: {
                'X-Internal-Service-Key': xInternalServiceKey,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
