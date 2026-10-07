/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { InspectionType } from './InspectionType';
import type { SPCControlType } from './SPCControlType';
/**
 * Update inspection plan schema.
 */
export type InspectionPlanUpdate = {
    operation_id?: (number | null);
    characteristic?: (string | null);
    /**
     * Lower Spec Limit
     */
    lsl?: (number | null);
    /**
     * Upper Spec Limit
     */
    usl?: (number | null);
    /**
     * Target value
     */
    nominal?: (number | null);
    unit?: (string | null);
    inspection_type?: (InspectionType | null);
    sampling_plan?: (string | null);
    frequency?: (number | null);
    enable_spc?: (boolean | null);
    spc_control_type?: (SPCControlType | null);
    is_active?: (boolean | null);
};

