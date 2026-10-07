/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Equipment status summary
 */
export type EquipmentSummary = {
    total: number;
    by_status: Record<string, number>;
    running: number;
    idle: number;
    error: number;
};

