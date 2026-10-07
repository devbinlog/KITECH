/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { QueryRequest } from '../models/QueryRequest';
import type { QueryResult } from '../models/QueryResult';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class NlmAiAssistantService {
    /**
     * Process Query
     * Process natural language query with enhanced intent detection.
     * @param requestBody
     * @param xInternalServiceKey
     * @returns QueryResult Successful Response
     * @throws ApiError
     */
    public static processQueryApiV1NlmQueryPost(
        requestBody: QueryRequest,
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<QueryResult> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/nlm/query',
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
     * Get Query History
     * @param limit
     * @param xInternalServiceKey
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getQueryHistoryApiV1NlmHistoryGet(
        limit: number = 50,
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/nlm/history',
            headers: {
                'X-Internal-Service-Key': xInternalServiceKey,
            },
            query: {
                'limit': limit,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Add Favorite
     * @param requestBody
     * @param xInternalServiceKey
     * @returns string Successful Response
     * @throws ApiError
     */
    public static addFavoriteApiV1NlmFavoritesPost(
        requestBody: QueryRequest,
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<Record<string, string>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/nlm/favorites',
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
     * Remove Favorite
     * @param requestBody
     * @param xInternalServiceKey
     * @returns string Successful Response
     * @throws ApiError
     */
    public static removeFavoriteApiV1NlmFavoritesDelete(
        requestBody: QueryRequest,
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<Record<string, string>> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/nlm/favorites',
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
     * Get Favorites
     * @param xInternalServiceKey
     * @returns string Successful Response
     * @throws ApiError
     */
    public static getFavoritesApiV1NlmFavoritesGet(
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<Record<string, Array<string>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/nlm/favorites',
            headers: {
                'X-Internal-Service-Key': xInternalServiceKey,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Quota Status
     * @param xInternalServiceKey
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getQuotaStatusApiV1NlmQuotaGet(
        xInternalServiceKey?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/nlm/quota',
            headers: {
                'X-Internal-Service-Key': xInternalServiceKey,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
