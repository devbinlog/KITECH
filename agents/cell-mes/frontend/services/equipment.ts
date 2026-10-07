import api from "@/lib/axios";
import {
  Equipment,
  EquipmentStatus,
  EquipmentSync,
  EquipmentVirtualCopyRequest,
  EquipmentVirtualCopyResult,
} from "@/types";

export const equipmentService = {
  async getAll(includeDeleted: boolean = false): Promise<Equipment[]> {
    const response = await api.get<Equipment[]>("/api/v1/masters/equipments", {
      params: { include_deleted: includeDeleted },
    });
    return response.data;
  },

  async getById(id: number): Promise<Equipment> {
    const response = await api.get<Equipment>(`/api/v1/masters/equipments/${id}`);
    return response.data;
  },

  async getStatus(id: number, refresh: boolean = false): Promise<EquipmentStatus> {
    const response = await api.get<EquipmentStatus>(`/api/v1/masters/equipments/${id}/status`, {
      params: { refresh },
    });
    return response.data;
  },

  async sync(deleteOrphans: boolean = false): Promise<EquipmentSync> {
    const response = await api.post<EquipmentSync>("/api/v1/masters/equipments/sync", null, {
      params: { delete_orphans: deleteOrphans },
    });
    return response.data;
  },

  async create(data: Partial<Equipment>): Promise<Equipment> {
    const response = await api.post<Equipment>("/api/v1/masters/equipments", data);
    return response.data;
  },

  async delete(id: number): Promise<void> {
    await api.delete(`/api/v1/masters/equipments/${id}`);
  },

  async createVirtualCopies(
    equipmentId: number,
    data: EquipmentVirtualCopyRequest
  ): Promise<EquipmentVirtualCopyResult> {
    const response = await api.post<EquipmentVirtualCopyResult>(
      `/api/v1/masters/equipments/${equipmentId}/virtual-copies`,
      data
    );
    return response.data;
  },

  async checkMiddlewareHealth(): Promise<{
    status: "connected" | "disconnected" | "error";
    url: string;
    message: string;
    error?: string;
  }> {
    const response = await api.get("/api/v1/masters/equipments/middleware-health");
    return response.data;
  },

  async getStatusHistory(
    equipmentId: number,
    limit: number = 50
  ): Promise<Array<{
    id: number;
    equipment_id: number;
    status: string;
    changed_at: string;
    duration_sec: number | null;
    remarks: string | null;
  }>> {
    const response = await api.get(`/api/v1/masters/equipments/${equipmentId}/status-history`, {
      params: { limit },
    });
    return response.data;
  },
};
