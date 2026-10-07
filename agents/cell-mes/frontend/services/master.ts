import api from "@/lib/axios";
import {
  DtFileRef,
  DtProjectLookup,
  DtProjectSelect,
  DtProjectSummary,
  Product,
  ProcessRouting,
  Scenario,
  StdProcess,
} from "@/types";

// Standard Process Service
export const stdProcessService = {
  async getAll(): Promise<StdProcess[]> {
    const response = await api.get<StdProcess[]>("/api/v1/masters/std-processes");
    return response.data;
  },

  async getById(id: number): Promise<StdProcess> {
    const response = await api.get<StdProcess>(`/api/v1/masters/std-processes/${id}`);
    return response.data;
  },

  async create(data: {
    code: string;
    name: string;
    description?: string;
    process_category?: string | null;
    equipment_type?: string | null;
    required_machines?: string[] | null;
    cycle_time_sec?: number;
    setup_time_sec?: number;
  }): Promise<StdProcess> {
    const response = await api.post<StdProcess>("/api/v1/masters/std-processes", data);
    return response.data;
  },

  async update(
    id: number,
    data: Partial<{
      code: string;
      name: string;
      description: string;
      process_category: string | null;
      equipment_type: string | null;
      required_machines: string[] | null;
      cycle_time_sec: number;
      setup_time_sec: number;
    }>
  ): Promise<StdProcess> {
    const response = await api.patch<StdProcess>(`/api/v1/masters/std-processes/${id}`, data);
    return response.data;
  },

  async delete(id: number): Promise<void> {
    await api.delete(`/api/v1/masters/std-processes/${id}`);
  },
};

// Product Service
export const productService = {
  async getCells(id: number): Promise<{ product_id: number; cell_ids: number[] }> {
    return (await api.get(`/api/v1/masters/products/${id}/cells`)).data;
  },

  async saveCells(id: number, cellIds: number[]): Promise<{ product_id: number; cell_ids: number[] }> {
    return (await api.put(`/api/v1/masters/products/${id}/cells`, { cell_ids: cellIds })).data;
  },
  async getAll(includeDeleted: boolean = false): Promise<Product[]> {
    const response = await api.get<Product[]>("/api/v1/masters/products", {
      params: { include_deleted: includeDeleted },
    });
    return response.data;
  },

  async getById(id: number): Promise<Product> {
    const response = await api.get<Product>(`/api/v1/masters/products/${id}`);
    return response.data;
  },

  async create(data: {
    code: string;
    name: string;
    unit?: string;
    dt_project?: DtProjectSelect | null;
  }): Promise<Product> {
    const response = await api.post<Product>("/api/v1/masters/products", data);
    return response.data;
  },

  async update(
    id: number,
    data: Partial<{
      code: string;
      name: string;
      product_category: string | null;
      unit: string;
    }>
  ): Promise<Product> {
    const response = await api.patch<Product>(`/api/v1/masters/products/${id}`, data);
    return response.data;
  },

  async delete(id: number): Promise<void> {
    await api.delete(`/api/v1/masters/products/${id}`);
  },

  async getDtProject(id: number): Promise<{ product_id: number; dt_project: DtProjectSummary | null }> {
    const response = await api.get(`/api/v1/masters/products/${id}/dt-project`);
    return response.data;
  },

  async linkDtProject(id: number, data: DtProjectSelect): Promise<{ product_id: number; dt_project: DtProjectSummary | null }> {
    const response = await api.put(`/api/v1/masters/products/${id}/dt-project`, data);
    return response.data;
  },

  async unlinkDtProject(id: number): Promise<void> {
    await api.delete(`/api/v1/masters/products/${id}/dt-project`);
  },

  async getDtNcFiles(productId: number, workplanId?: string | null): Promise<DtFileRef[]> {
    const response = await api.get<DtFileRef[]>(`/api/v1/masters/products/${productId}/dt-nc-files`, {
      params: workplanId ? { workplan_id: workplanId } : {},
    });
    return response.data;
  },
};

// Routing Service
export const routingService = {
  async getByProduct(productId: number): Promise<ProcessRouting[]> {
    const response = await api.get<ProcessRouting[]>(`/api/v1/masters/products/${productId}/routings`);
    return response.data;
  },

  async save(
    productId: number,
    routings: Array<{
      std_process_id: number;
      sequence: number;
      revision?: string;
      setup_id?: string | null;
      dt_workplan_id?: number | null;
      required_machines?: string[] | null;
      cycle_time_sec?: number | null;
      cycle_time_breakdown?: Record<string, any> | null;
      remarks?: string;
      files?: Array<{
        file_type: string;
        file_path: string;
        original_filename?: string | null;
        source_type?: "LOCAL_UPLOAD" | "DTP";
        dt_file_ref_id?: number | null;
        compatible_machines?: string[] | null;
        sort_order: number;
      }>;
    }>
  ): Promise<ProcessRouting[]> {
    const response = await api.put<ProcessRouting[]>(
      `/api/v1/masters/products/${productId}/routings`,
      routings
    );
    return response.data;
  },

  async uploadRoutingFile(file: File): Promise<{ status: string; file_path: string; original_filename: string }> {
    const formData = new FormData();
    formData.append("file", file);
    const response = await api.post("/api/v1/masters/files/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return response.data;
  },
};

// Digital Thread Platform lookup service
export const dtpService = {
  async getProjects(keyword?: string): Promise<DtProjectLookup[]> {
    const response = await api.get<DtProjectLookup[]>("/api/v1/integrations/dtp/projects", {
      params: keyword ? { keyword } : {},
    });
    return response.data;
  },

  async getProjectTree(assetGlobalId: string, assetId: string): Promise<Record<string, any>> {
    const response = await api.get("/api/v1/integrations/dtp/projects/tree", {
      params: { asset_global_id: assetGlobalId, asset_id: assetId },
    });
    return response.data;
  },
};

// Scenario Service
export const scenarioService = {
  async getAll(productId?: number, activeOnly: boolean = true): Promise<Scenario[]> {
    const response = await api.get<Scenario[]>("/api/v1/masters/scenarios", {
      params: { product_id: productId, active_only: activeOnly },
    });
    return response.data;
  },

  async getById(id: number): Promise<Scenario> {
    const response = await api.get<Scenario>(`/api/v1/masters/scenarios/${id}`);
    return response.data;
  },

  async create(data: {
    code?: string;
    name: string;
    file_path: string;
    product_id?: number;
    is_active?: boolean;
  }): Promise<Scenario> {
    const response = await api.post<Scenario>("/api/v1/masters/scenarios", data);
    return response.data;
  },

  async update(
    id: number,
    data: Partial<{
      code: string;
      name: string;
      file_path: string;
      product_id: number | null;
      is_active: boolean;
    }>
  ): Promise<Scenario> {
    const response = await api.patch<Scenario>(`/api/v1/masters/scenarios/${id}`, data);
    return response.data;
  },

  async toggleActive(id: number, isActive: boolean): Promise<Scenario> {
    const response = await api.patch<Scenario>(`/api/v1/masters/scenarios/${id}/active`, null, {
      params: { is_active: isActive },
    });
    return response.data;
  },

  async delete(id: number): Promise<void> {
    await api.delete(`/api/v1/masters/scenarios/${id}`);
  },

  async getContent(id: number): Promise<{
    scenario_id?: number;
    scenario_name?: string;
    file_path: string;
    content?: any;
    error?: string;
  }> {
    const response = await api.get(`/api/v1/masters/scenarios/${id}/content`);
    return response.data;
  },

  // -------- M0/M1: n8n YAML editor integration --------

  /** Save scenario YAML text to disk. Server validates with yaml.safe_load. */
  async saveContent(
    id: number,
    content: string
  ): Promise<{
    id: number;
    file_path: string;
    size_bytes: number;
    saved_at: string;
    backup_created: boolean;
  }> {
    const response = await api.put(
      `/api/v1/masters/scenarios/${id}/content`,
      { content }
    );
    return response.data;
  },

  /** Static action template catalog for ScenarioStep dropdown / autocomplete. */
  async getActions(): Promise<{
    data: Array<{ key: string; category: string; description: string }>;
  }> {
    const response = await api.get("/api/v1/masters/scenarios/actions");
    return response.data;
  },
};
