/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Inspection result response schema.
 */
export type InspectionResultResponse = {
    inspection_plan_id: number;
    work_order_id: number;
    equipment_id?: (number | null);
    lot_no?: (string | null);
    /**
     * 개별 추적
     */
    serial_no?: (string | null);
    nc_program_id?: (string | null);
    /**
     * OMM, EQUATOR, CMM, MANUAL
     */
    source?: string;
    /**
     * 측정 장비 ID
     */
    device_id?: (number | null);
    measured_value: number;
    /**
     * 기준값 대비 편차
     */
    deviation?: (number | null);
    /**
     * inspector, method, conditions 등
     */
    measurement_metadata?: (Record<string, any> | null);
    id: number;
    is_conforming: boolean;
    deviation_from_target?: (number | null);
    measured_at: string;
    created_at: string;
};

