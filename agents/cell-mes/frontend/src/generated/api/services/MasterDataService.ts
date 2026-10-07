/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ProductCreate } from '../models/ProductCreate';
import type { ProductRead } from '../models/ProductRead';
import type { StdProcessCreate } from '../models/StdProcessCreate';
import type { StdProcessRead } from '../models/StdProcessRead';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class MasterDataService {
    /**
     * List Std Processes
     * List all standard processes.
     * @param xInternalServiceKey
     * @returns StdProcessRead Successful Response
     * @throws ApiError
     */
    public static listStdProcessesApiV1MastersStdProcessesGet(
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<Array<StdProcessRead>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/masters/std-processes',
            headers: {
                'X-Internal-Service-Key': xInternalServiceKey,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Std Process
     * Create a new standard process.
     * @param requestBody
     * @param xInternalServiceKey
     * @returns StdProcessRead Successful Response
     * @throws ApiError
     */
    public static createStdProcessApiV1MastersStdProcessesPost(
        requestBody: StdProcessCreate,
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<StdProcessRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/masters/std-processes',
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
     * Get Std Process
     * Get a standard process by ID.
     * @param processId
     * @param xInternalServiceKey
     * @returns StdProcessRead Successful Response
     * @throws ApiError
     */
    public static getStdProcessApiV1MastersStdProcessesProcessIdGet(
        processId: number,
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<StdProcessRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/masters/std-processes/{process_id}',
            path: {
                'process_id': processId,
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
     * Delete Std Process
     * Delete a standard process.
     * @param processId
     * @param xInternalServiceKey
     * @returns void
     * @throws ApiError
     */
    public static deleteStdProcessApiV1MastersStdProcessesProcessIdDelete(
        processId: number,
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/masters/std-processes/{process_id}',
            path: {
                'process_id': processId,
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
     * List Products
     * List all products.
     * @param includeDeleted
     * @param xInternalServiceKey
     * @returns ProductRead Successful Response
     * @throws ApiError
     */
    public static listProductsApiV1MastersProductsGet(
        includeDeleted: boolean = false,
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<Array<ProductRead>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/masters/products',
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
     * Create Product
     * Create a new product.
     * @param requestBody
     * @param xInternalServiceKey
     * @returns ProductRead Successful Response
     * @throws ApiError
     */
    public static createProductApiV1MastersProductsPost(
        requestBody: ProductCreate,
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<ProductRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/masters/products',
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
     * Get Product
     * Get a product by ID.
     * @param productId
     * @param xInternalServiceKey
     * @returns ProductRead Successful Response
     * @throws ApiError
     */
    public static getProductApiV1MastersProductsProductIdGet(
        productId: number,
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<ProductRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/masters/products/{product_id}',
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
     * Delete Product
     * Soft delete a product.
     * @param productId
     * @param xInternalServiceKey
     * @returns void
     * @throws ApiError
     */
    public static deleteProductApiV1MastersProductsProductIdDelete(
        productId: number,
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/masters/products/{product_id}',
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
}
