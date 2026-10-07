/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Create non-conformance schema.
 */
export type NonConformanceCreate = {
    work_order_id?: (number | null);
    lot_no?: (string | null);
    serial_no?: (string | null);
    machine_id?: (number | null);
    inspection_result_id?: (number | null);
    /**
     * DIMENSION, SURFACE, MATERIAL
     */
    defect_type: string;
    /**
     * 어떤 항목
     */
    characteristic: string;
    specified_value?: (number | null);
    actual_value?: (number | null);
    /**
     * REWORK, SCRAP, USE_AS_IS, RETURN
     */
    disposition?: string;
    description: string;
    /**
     * 5 Why 분석
     */
    root_cause?: (string | null);
    corrective_action?: (string | null);
    reported_by: string;
    assigned_to?: (string | null);
    due_date?: (string | null);
};

