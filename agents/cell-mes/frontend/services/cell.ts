import api from "@/lib/axios";
import type { Equipment } from "@/types";

export interface CellInput {
  code: string;
  name: string;
  location: string | null;
}

export interface Cell extends CellInput {
  id: number;
  created_at: string;
}

export const cellService = {
  async getAll(): Promise<Cell[]> {
    return (await api.get<Cell[]>("/api/v1/masters/cells")).data;
  },
  async create(data: CellInput): Promise<Cell> {
    return (await api.post<Cell>("/api/v1/masters/cells", data)).data;
  },
  async update(id: number, data: CellInput): Promise<Cell> {
    return (await api.put<Cell>(`/api/v1/masters/cells/${id}`, data)).data;
  },
  async delete(id: number): Promise<void> {
    await api.delete(`/api/v1/masters/cells/${id}`);
  },
  async assign(equipment: Equipment, cellId: number | null): Promise<Equipment> {
    return (await api.patch<Equipment>(`/api/v1/masters/equipments/${equipment.id}/cell`, {
      cell_id: cellId,
      expected_cell_id: equipment.cell_id,
    })).data;
  },
};
