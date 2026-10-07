/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ProcessRoutingCreate } from '../models/ProcessRoutingCreate';
import type { ProcessRoutingRead } from '../models/ProcessRoutingRead';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class RoutingsService {
    /**
     * Get Product Routings
     * Get all routings for a product.
     * @param productId
     * @param xInternalServiceKey
     * @returns ProcessRoutingRead Successful Response
     * @throws ApiError
     */
    public static getProductRoutingsApiV1MastersProductsProductIdRoutingsGet(
        productId: number,
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<Array<ProcessRoutingRead>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/masters/products/{product_id}/routings',
            path: {
                'product_id': productId,
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
     * Save Product Routings
     * Save/replace all routings for a product (transactional).
     *
     * This endpoint replaces all existing routings with the new ones.
     * All operations are performed in a single transaction.
     * @param productId
     * @param requestBody
     * @param xInternalServiceKey
     * @returns ProcessRoutingRead Successful Response
     * @throws ApiError
     */
    public static saveProductRoutingsApiV1MastersProductsProductIdRoutingsPut(
        productId: number,
        requestBody: Array<ProcessRoutingCreate>,
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<Array<ProcessRoutingRead>> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/masters/products/{product_id}/routings',
            path: {
                'product_id': productId,
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
}
