import api from "@/lib/axios";
import {
  WorkOrder,
  ProdResult,
  PaginatedResponse,
  OrderFilters,
  ResultFilters,
  MiddlewareResumeMode,
  OrderMiddlewareState,
} from "@/types";

export const productionService = {
  // Work Orders
  async getOrders(filters: OrderFilters = {}): Promise<PaginatedResponse<WorkOrder>> {
    const response = await api.get<PaginatedResponse<WorkOrder>>("/api/v1/production/orders", {
      params: {
        status: filters.status,
        view: filters.view,
        date_from: filters.dateFrom,
        date_to: filters.dateTo,
        page: filters.page || 1,
        limit: filters.limit || 30,
        sort_by: filters.sortBy || "plan_start",
        sort_order: filters.sortOrder || "asc",
      },
    });
    return response.data;
  },

  async getOrderById(id: number): Promise<WorkOrder> {
    const response = await api.get<WorkOrder>(`/api/v1/production/orders/${id}`);
    return response.data;
  },

  async createOrder(data: {
    lot_no: string;
    product_id: number;
    scenario_id?: number;
    target_qty: number;
    qty?: number;
    priority?: number;
    due_date?: string;
    plan_start?: string;
    plan_end?: string;
    remarks?: string;
  }): Promise<WorkOrder> {
    const response = await api.post<WorkOrder>("/api/v1/production/orders", data);
    return response.data;
  },

  async updateOrderStatus(id: number, status: string): Promise<WorkOrder> {
    const response = await api.patch<WorkOrder>(`/api/v1/production/orders/${id}/status`, {
      status,
    });
    return response.data;
  },

  async startOrder(id: number): Promise<WorkOrder> {
    const response = await api.post<WorkOrder>(`/api/v1/production/orders/${id}/start`);
    return response.data;
  },

  async deleteOrder(id: number): Promise<void> {
    await api.delete(`/api/v1/production/orders/${id}`);
  },

  // Monitoring & Control (Middleware Integration)
  async getMonitoring(id: number): Promise<any> {
    const response = await api.get(`/api/v1/production/orders/${id}/monitoring`);
    return response.data;
  },

  async getMiddlewareState(id: number): Promise<OrderMiddlewareState> {
    const response = await api.get<OrderMiddlewareState>(`/api/v1/production/orders/${id}/middleware-state`);
    return response.data;
  },

  async commandMiddlewareUnit(id: number, unitNo: string | number, action: string): Promise<any> {
    const response = await api.post(`/api/v1/production/orders/${id}/middleware/units/${unitNo}/commands/${action}`);
    return response.data;
  },

  async resumeMiddlewareUnit(
    id: number,
    unitNo: string | number,
    data: {
      mode: MiddlewareResumeMode;
      resume_step_id?: string | null;
      clear_retry?: boolean;
    }
  ): Promise<any> {
    const response = await api.post(`/api/v1/production/orders/${id}/middleware/units/${unitNo}/resume`, data);
    return response.data;
  },

  async clearUnitAlarm(id: number, unitId: number): Promise<any> {
    const response = await api.post(`/api/v1/production/orders/${id}/units/${unitId}/clear-alarm`);
    return response.data;
  },

  async stopUnit(id: number, unitId: number): Promise<any> {
    const response = await api.post(`/api/v1/production/orders/${id}/units/${unitId}/stop`);
    return response.data;
  },

  async resumeUnit(id: number, unitId: number): Promise<any> {
    const response = await api.post(`/api/v1/production/orders/${id}/units/${unitId}/resume`);
    return response.data;
  },

  // Production Results
  async getResults(filters: ResultFilters = {}): Promise<PaginatedResponse<ProdResult>> {
    const response = await api.get<PaginatedResponse<ProdResult>>("/api/v1/production/results", {
      params: {
        work_order_id: filters.workOrderId,
        page: filters.page || 1,
        limit: filters.limit || 30,
      },
    });
    return response.data;
  },

  async createResult(data: {
    work_order_id: number;
    process_routing_id?: number;
    equipment_id?: number;
    ok_qty: number;
    ng_qty: number;
  }): Promise<ProdResult> {
    const response = await api.post<ProdResult>("/api/v1/production/results", data);
    return response.data;
  },

  // Work Info (for middleware)
  async getWorkInfo(lotNo: string): Promise<any> {
    const response = await api.get("/api/v1/production/middleware/work-info", {
      params: { lot_no: lotNo },
    });
    return response.data;
  },

  async updateScenario(orderId: number, scenarioId: number): Promise<any> {
    const response = await api.patch(`/api/v1/production/orders/${orderId}/scenario`, {
      scenario_id: scenarioId,
    });
    return response.data;
  },

  async getUnitsForOrder(orderId: number): Promise<any> {
    const response = await api.get(`/api/v1/production/orders/${orderId}/units`);
    return response.data;
  },

  async holdUnitScenario(orderId: number, unitId: number): Promise<any> {
    const response = await api.post(`/api/v1/production/orders/${orderId}/units/${unitId}/scenario-hold`);
    return response.data;
  },

  async updateUnitScenario(orderId: number, unitId: number, scenarioId: number): Promise<any> {
    const response = await api.patch(`/api/v1/production/orders/${orderId}/units/${unitId}/scenario`, {
      scenario_id: scenarioId,
    });
    return response.data;
  },

  async releaseUnitScenarioHold(orderId: number, unitId: number): Promise<any> {
    const response = await api.post(`/api/v1/production/orders/${orderId}/units/${unitId}/scenario-release`);
    return response.data;
  },
};
