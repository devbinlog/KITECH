/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { EquipmentCreate } from '../models/EquipmentCreate';
import type { EquipmentRead } from '../models/EquipmentRead';
import type { EquipmentStatus } from '../models/EquipmentStatus';
import type { EquipmentSync } from '../models/EquipmentSync';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class EquipmentsService {
    /**
     * List Equipments
     * List all equipments.
     * @param includeDeleted
     * @param xInternalServiceKey
     * @returns EquipmentRead Successful Response
     * @throws ApiError
     */
    public static listEquipmentsApiV1MastersEquipmentsGet(
        includeDeleted: boolean = false,
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<Array<EquipmentRead>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/masters/equipments',
            headers: {
                'X-Internal-Service-Key': xInternalServiceKey,
            },
            query: {
                'include_deleted': includeDeleted,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Equipment
     * Create a new equipment manually.
     * @param requestBody
     * @param xInternalServiceKey
     * @returns EquipmentRead Successful Response
     * @throws ApiError
     */
    public static createEquipmentApiV1MastersEquipmentsPost(
        requestBody: EquipmentCreate,
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<EquipmentRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/masters/equipments',
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
     * Sync Equipments
     * Synchronize equipment from middleware (AAS Asset Discovery).
     * @param xInternalServiceKey
     * @returns EquipmentSync Successful Response
     * @throws ApiError
     */
    public static syncEquipmentsApiV1MastersEquipmentsSyncPost(
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<EquipmentSync> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/masters/equipments/sync',
            headers: {
                'X-Internal-Service-Key': xInternalServiceKey,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Check Middleware Health
     * Check middleware connection status.
     * @param xInternalServiceKey
     * @returns any Successful Response
     * @throws ApiError
     */
    public static checkMiddlewareHealthApiV1MastersEquipmentsMiddlewareHealthGet(
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/masters/equipments/middleware-health',
            headers: {
                'X-Internal-Service-Key': xInternalServiceKey,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Equipment
     * Get an equipment by ID.
     * @param equipmentId
     * @param xInternalServiceKey
     * @returns EquipmentRead Successful Response
     * @throws ApiError
     */
    public static getEquipmentApiV1MastersEquipmentsEquipmentIdGet(
        equipmentId: number,
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<EquipmentRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/masters/equipments/{equipment_id}',
            path: {
                'equipment_id': equipmentId,
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
     * Delete Equipment
     * Soft delete an equipment.
     * @param equipmentId
     * @param xInternalServiceKey
     * @returns void
     * @throws ApiError
     */
    public static deleteEquipmentApiV1MastersEquipmentsEquipmentIdDelete(
        equipmentId: number,
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/masters/equipments/{equipment_id}',
            path: {
                'equipment_id': equipmentId,
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
     * Get Equipment Status
     * Get equipment status, optionally refreshing from middleware.
     * @param equipmentId
     * @param refresh
     * @param xInternalServiceKey
     * @returns EquipmentStatus Successful Response
     * @throws ApiError
     */
    public static getEquipmentStatusApiV1MastersEquipmentsEquipmentIdStatusGet(
        equipmentId: number,
        refresh: boolean = false,
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<EquipmentStatus> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/masters/equipments/{equipment_id}/status',
            path: {
                'equipment_id': equipmentId,
            },
            headers: {
                'X-Internal-Service-Key': xInternalServiceKey,
            },
            query: {
                'refresh': refresh,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
