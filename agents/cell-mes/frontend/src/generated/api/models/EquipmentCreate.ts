/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Schema for creating equipment.
 */
export type EquipmentCreate = {
    eq_name: string;
    model_name?: (string | null);
    equipment_type?: string;
    aas_id?: (string | null);
    connection_config?: Record<string, any>;
    spec_data?: Record<string, any>;
};

