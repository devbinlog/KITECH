/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * SPC capability analysis result.
 */
export type SPCCapabilityAnalysis = {
    characteristic: string;
    sample_count: number;
    mean: number;
    std_deviation: number;
    cp?: (number | null);
    cpk?: (number | null);
    pp?: (number | null);
    ppk?: (number | null);
    specification_min?: (number | null);
    specification_max?: (number | null);
    target_value?: (number | null);
    analysis_date: string;
};

