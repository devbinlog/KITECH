/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { SPCCapabilityAnalysis } from './SPCCapabilityAnalysis';
import type { SPCViolationRule } from './SPCViolationRule';
/**
 * Comprehensive SPC analysis result.
 */
export type SPCAnalysisResult = {
    chart_id: number;
    characteristic: string;
    total_points: number;
    out_of_control_points: number;
    capability_analysis?: (SPCCapabilityAnalysis | null);
    violated_rules?: Array<SPCViolationRule>;
    trend_analysis?: Record<string, any>;
    recommendations?: Array<string>;
    analysis_date: string;
};

