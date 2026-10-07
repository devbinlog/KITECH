import api from "@/lib/axios";
import {
  Downtime,
  DowntimeReason,
  DowntimeFilters,
  DowntimeSummary,
} from "@/types";

// Downtime Reason Service
export const downtimeReasonService = {
  async getAll(activeOnly: boolean = true): Promise<DowntimeReason[]> {
    const response = await api.get<DowntimeReason[]>("/api/v1/downtime/reasons", {
      params: { active_only: activeOnly },
    });
    return response.data;
  },

  async getById(id: number): Promise<DowntimeReason> {
    const response = await api.get<DowntimeReason>(`/api/v1/downtime/reasons/${id}`);
    return response.data;
  },

  async create(data: {
    category: string;
    code: string;
    name: string;
    description?: string;
    is_active?: boolean;
  }): Promise<DowntimeReason> {
    const response = await api.post<DowntimeReason>("/api/v1/downtime/reasons", data);
    return response.data;
  },

  async update(
    id: number,
    data: Partial<{
      category: string;
      code: string;
      name: string;
      description: string;
      is_active: boolean;
    }>
  ): Promise<DowntimeReason> {
    const response = await api.patch<DowntimeReason>(`/api/v1/downtime/reasons/${id}`, data);
    return response.data;
  },

  async delete(id: number): Promise<void> {
    await api.delete(`/api/v1/downtime/reasons/${id}`);
  },
};

// Downtime Service
export const downtimeService = {
  async getAll(filters?: DowntimeFilters): Promise<Downtime[]> {
    const response = await api.get<Downtime[]>("/api/v1/downtime", {
      params: filters,
    });
    return response.data;
  },

  async getActive(): Promise<Downtime[]> {
    const response = await api.get<Downtime[]>("/api/v1/downtime", {
      params: { status: "ACTIVE", limit: 100 },
    });
    const data = response.data;
    return Array.isArray(data) ? data : [];
  },

  async getById(id: number): Promise<Downtime> {
    const response = await api.get<Downtime>(`/api/v1/downtime/${id}`);
    return response.data;
  },

  async start(data: {
    equipment_id: number;
    reason_id: number;
    start_time?: string;
    remarks?: string;
  }): Promise<Downtime> {
    const response = await api.post<Downtime>("/api/v1/downtime", data);
    return response.data;
  },

  async end(id: number, data?: { end_time?: string; remarks?: string }): Promise<Downtime> {
    const response = await api.post<Downtime>(`/api/v1/downtime/${id}/end`, data);
    return response.data;
  },

  async update(
    id: number,
    data: Partial<{
      reason_id: number;
      start_time: string;
      end_time: string;
      remarks: string;
    }>
  ): Promise<Downtime> {
    const response = await api.patch<Downtime>(`/api/v1/downtime/${id}`, data);
    return response.data;
  },

  async delete(id: number): Promise<void> {
    await api.delete(`/api/v1/downtime/${id}`);
  },

  async getSummary(filters?: {
    date_from?: string;
    date_to?: string;
    equipment_id?: number;
  }): Promise<DowntimeSummary[]> {
    const response = await api.get<any>("/api/v1/downtime/summary", {
      params: filters,
    });
    const data = response.data;
    // Backend returns { by_category: {...}, total_count, total_minutes }
    // Transform nested object to array format expected by frontend
    if (data?.by_category) {
      return Object.entries(data.by_category).map(([category, info]: [string, any]) => ({
        category,
        count: info.count || 0,
        total_duration_sec: (info.total_minutes || 0) * 60,
      }));
    }
    return Array.isArray(data) ? data : [];
  },
};
