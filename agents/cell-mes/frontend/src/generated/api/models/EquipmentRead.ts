/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Schema for reading equipment.
 */
export type EquipmentRead = {
    eq_name: string;
    model_name?: (string | null);
    equipment_type?: string;
    id: number;
    aas_id: (string | null);
    connection_config: Record<string, any>;
    spec_data: Record<string, any>;
    last_data: Record<string, any>;
    current_status: string;
    updated_at: string;
    last_connected_at: (string | null);
    is_deleted: boolean;
};

