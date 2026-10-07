/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { UtilizationItem } from './UtilizationItem';
import type { UtilizationSummary } from './UtilizationSummary';
/**
 * Equipment utilization response
 */
export type UtilizationResponse = {
    period: Record<string, any>;
    equipment_utilization: Array<UtilizationItem>;
    summary: UtilizationSummary;
    errors?: Array<Record<string, string>>;
    partial?: boolean;
};

