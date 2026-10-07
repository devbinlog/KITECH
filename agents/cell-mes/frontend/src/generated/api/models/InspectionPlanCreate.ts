/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { InspectionType } from './InspectionType';
import type { SPCControlType } from './SPCControlType';
/**
 * Create inspection plan schema.
 */
export type InspectionPlanCreate = {
    product_id: number;
    operation_id?: (number | null);
    /**
     * STEP file path
     */
    pmi_source?: (string | null);
    /**
     * PMI Feature ID
     */
    feature_id?: (string | null);
    /**
     * 외경, 깊이, 위치도 등
     */
    characteristic: string;
    /**
     * 기준값
     */
    nominal?: (number | null);
    /**
     * Upper Spec Limit
     */
    usl?: (number | null);
    /**
     * Lower Spec Limit
     */
    lsl?: (number | null);
    unit?: string;
    inspection_type?: InspectionType;
    /**
     * FIRST_ARTICLE, PERIODIC, 100%
     */
    sampling_plan?: string;
    /**
     * n개당 1회
     */
    frequency?: (number | null);
    enable_spc?: boolean;
    spc_control_type?: SPCControlType;
    is_active?: boolean;
};

