/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * SPC data point response schema.
 */
export type SPCDataPointResponse = {
    spc_chart_id: number;
    subgroup_number: number;
    mean_value: number;
    range_value?: (number | null);
    standard_deviation?: (number | null);
    sample_size: number;
    raw_values?: (Array<number> | null);
    work_order_id?: (number | null);
    lot_number?: (string | null);
    id: number;
    is_out_of_control: boolean;
    violation_rules?: (Array<string> | null);
    created_at: string;
};

