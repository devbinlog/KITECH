/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { SPCControlType } from './SPCControlType';
import type { SPCDataPointResponse } from './SPCDataPointResponse';
/**
 * SPC chart with data points.
 */
export type SPCChartWithDataPoints = {
    inspection_plan_id: number;
    center_line: number;
    upper_control_limit: number;
    lower_control_limit: number;
    upper_warning_limit?: (number | null);
    lower_warning_limit?: (number | null);
    range_center_line?: (number | null);
    range_upper_control_limit?: (number | null);
    range_lower_control_limit?: (number | null);
    chart_type: SPCControlType;
    is_active?: boolean;
    id: number;
    sample_count: number;
    last_calculation_date?: (string | null);
    revision: number;
    created_at: string;
    updated_at: string;
    data_points?: Array<SPCDataPointResponse>;
};

