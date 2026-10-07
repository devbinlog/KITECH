/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { EquipmentSummary } from './EquipmentSummary';
import type { KPIResponse } from './KPIResponse';
import type { OrderSummary } from './OrderSummary';
import type { ResultsSummary } from './ResultsSummary';
/**
 * Daily production status response
 */
export type DailyStatusResponse = {
    date: string;
    orders: OrderSummary;
    results: ResultsSummary;
    equipment: EquipmentSummary;
    kpis: KPIResponse;
    errors?: Array<Record<string, string>>;
    partial?: boolean;
};

