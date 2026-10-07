/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Equipment status response.
 */
export type EquipmentStatus = {
    id: number;
    aas_id: (string | null);
    eq_name: string;
    equipment_type: string;
    current_status: string;
    last_data: Record<string, any>;
    last_connected_at: (string | null);
};

