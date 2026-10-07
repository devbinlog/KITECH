/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ScenarioCreate } from '../models/ScenarioCreate';
import type { ScenarioRead } from '../models/ScenarioRead';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ScenariosService {
    /**
     * List Scenarios
     * List scenarios, optionally filtered by product.
     * @param productId
     * @param activeOnly
     * @param xInternalServiceKey
     * @returns ScenarioRead Successful Response
     * @throws ApiError
     */
    public static listScenariosApiV1MastersScenariosGet(
        productId?: number,
        activeOnly: boolean = true,
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<Array<ScenarioRead>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/masters/scenarios',
            headers: {
                'X-Internal-Service-Key': xInternalServiceKey,
            },
            query: {
                'product_id': productId,
                'active_only': activeOnly,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Scenario
     * Create a new scenario.
     * @param requestBody
     * @param xInternalServiceKey
     * @returns ScenarioRead Successful Response
     * @throws ApiError
     */
    public static createScenarioApiV1MastersScenariosPost(
        requestBody: ScenarioCreate,
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<ScenarioRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/masters/scenarios',
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
     * Get Scenario
     * Get a scenario by ID.
     * @param scenarioId
     * @param xInternalServiceKey
     * @returns ScenarioRead Successful Response
     * @throws ApiError
     */
    public static getScenarioApiV1MastersScenariosScenarioIdGet(
        scenarioId: number,
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<ScenarioRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/masters/scenarios/{scenario_id}',
            path: {
                'scenario_id': scenarioId,
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
     * Delete Scenario
     * Delete a scenario.
     * @param scenarioId
     * @param xInternalServiceKey
     * @returns void
     * @throws ApiError
     */
    public static deleteScenarioApiV1MastersScenariosScenarioIdDelete(
        scenarioId: number,
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/masters/scenarios/{scenario_id}',
            path: {
                'scenario_id': scenarioId,
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
     * Get Scenario Content
     * Get scenario control file content (JSON).
     * @param scenarioId
     * @param xInternalServiceKey
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getScenarioContentApiV1MastersScenariosScenarioIdContentGet(
        scenarioId: number,
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/masters/scenarios/{scenario_id}/content',
            path: {
                'scenario_id': scenarioId,
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
     * Toggle Scenario Active
     * Toggle scenario active status.
     * @param scenarioId
     * @param isActive
     * @param xInternalServiceKey
     * @returns ScenarioRead Successful Response
     * @throws ApiError
     */
    public static toggleScenarioActiveApiV1MastersScenariosScenarioIdActivePatch(
        scenarioId: number,
        isActive: boolean,
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<ScenarioRead> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/masters/scenarios/{scenario_id}/active',
            path: {
                'scenario_id': scenarioId,
            },
            headers: {
                'X-Internal-Service-Key': xInternalServiceKey,
            },
            query: {
                'is_active': isActive,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
