import api from "@/lib/axios";
import {
  Alarm,
  AlarmDefinition,
  AlarmFilters,
  AlarmSummary,
} from "@/types";

// Alarm Definition Service
export const alarmDefinitionService = {
  async getAll(activeOnly: boolean = true): Promise<AlarmDefinition[]> {
    const response = await api.get<AlarmDefinition[]>("/api/v1/alarms/definitions", {
      params: { active_only: activeOnly },
    });
    return response.data;
  },

  async getById(id: number): Promise<AlarmDefinition> {
    const response = await api.get<AlarmDefinition>(`/api/v1/alarms/definitions/${id}`);
    return response.data;
  },

  async create(data: {
    equipment_type?: string;
    alarm_code: string;
    name: string;
    description?: string;
    severity: string;
    recommended_action?: string;
    is_active?: boolean;
  }): Promise<AlarmDefinition> {
    const response = await api.post<AlarmDefinition>("/api/v1/alarms/definitions", data);
    return response.data;
  },

  async update(
    id: number,
    data: Partial<{
      equipment_type: string;
      alarm_code: string;
      name: string;
      description: string;
      severity: string;
      recommended_action: string;
      is_active: boolean;
    }>
  ): Promise<AlarmDefinition> {
    const response = await api.patch<AlarmDefinition>(`/api/v1/alarms/definitions/${id}`, data);
    return response.data;
  },

  async delete(id: number): Promise<void> {
    await api.delete(`/api/v1/alarms/definitions/${id}`);
  },
};

// Alarm Service
export const alarmService = {
  async getAll(filters?: AlarmFilters): Promise<Alarm[]> {
    const response = await api.get<Alarm[]>("/api/v1/alarms", {
      params: filters,
    });
    return response.data;
  },

  async getActive(): Promise<Alarm[]> {
    const response = await api.get<Alarm[]>("/api/v1/alarms/active");
    return response.data;
  },

  async getById(id: number): Promise<Alarm> {
    const response = await api.get<Alarm>(`/api/v1/alarms/${id}`);
    return response.data;
  },

  async create(data: {
    equipment_id: number;
    alarm_code: string;
    severity: string;
    message: string;
    alarm_definition_id?: number;
  }): Promise<Alarm> {
    const response = await api.post<Alarm>("/api/v1/alarms", data);
    return response.data;
  },

  async acknowledge(id: number, acknowledgedBy: string = "admin"): Promise<Alarm> {
    const response = await api.post<Alarm>(`/api/v1/alarms/${id}/acknowledge`, {
      acknowledged_by: acknowledgedBy,
    });
    return response.data;
  },

  async clear(id: number, resolvedBy: string = "admin", remarks?: string): Promise<Alarm> {
    const response = await api.post<Alarm>(`/api/v1/alarms/${id}/resolve`, {
      resolved_by: resolvedBy,
      resolution_note: remarks || null,
    });
    return response.data;
  },

  async delete(id: number): Promise<void> {
    await api.delete(`/api/v1/alarms/${id}`);
  },

  async getSummary(filters?: {
    date_from?: string;
    date_to?: string;
    equipment_id?: number;
  }): Promise<AlarmSummary[]> {
    const response = await api.get<any>("/api/v1/alarms/active/summary", {
      params: filters,
    });
    const data = response.data;
    // Backend returns { total, by_severity, by_equipment }
    // Transform single object to array format expected by frontend
    if (data?.by_severity) {
      return Object.entries(data.by_severity).map(([severity, count]: [string, any]) => ({
        severity,
        count: count || 0,
        equipment_counts: data.by_equipment || {},
      }));
    }
    return Array.isArray(data) ? data : [];
  },
};
