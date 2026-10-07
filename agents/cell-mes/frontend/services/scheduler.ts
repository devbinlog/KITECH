import api from "@/lib/axios";

export interface MachineForScheduler {
  machine_id: string;
  machine_name: string;
  machine_type: string;
  status: string;
  available_from: string;
  current_setup_id: string | null;
  setup_change_time_min: number;
  mes_equipment_id: number;
  aas_id: string;
  location: string;
}

export interface ScheduledTask {
  wo_id: string;
  op_id: string;
  machine_id: string;
  start_time: number;
  end_time: number;
  quantity: number;
  setup_time?: number;
}


export interface SchedulingStatistics {
  total_tasks: number;
  makespan_seconds: number;
  makespan_hours: number;
  machine_utilization: Record<string, number>;
  bottleneck_machines: string[];
  solve_time_sec: number;
  objective_value: number;
  // Lexicographic 목적함수 컴포넌트 (납기 → 우선순위 → makespan → 셋업)
  weighted_tardiness_sec?: number;
  weighted_completion_sec?: number;
  total_setup_sec?: number;
}

export interface SchedulingRequestParams {
  horizon_hours: number;
  include_running: boolean;
}

export interface SchedulingRequest {
  request: {
    scheduling_request: {
      request_id: string;
      request_time: string;
      scheduling_horizon: {
        start: string;
        end: string;
      };
      options: {
        solver_time_limit_sec: number;
        optimization_goal: string;
      };
    };
  };
  work_orders: any[];
  machines: MachineForScheduler[];
  machine_type_params: Record<string, any>;
}

export interface SchedulingResult {
  status: string;
  scheduled_tasks: ScheduledTask[];
  statistics: SchedulingStatistics;
  quality_metrics?: Record<string, any>;
  gantt_data?: {
    tasks: any[];
    resources: string[];
    start: string;
    end: string;
  };
}

// Types for current schedule (Gantt chart)
export interface ScheduleSlot {
  slot_start: string | null;
  slot_end: string | null;
  status: "READY" | "RUNNING" | "PAUSE" | "DONE" | "ERROR" | "AVAILABLE" | "MAINTENANCE" | "OFFLINE" | "SCHEDULED";
  work_order_id?: number;
  lot_no?: string;
  product?: string;
}

export interface EquipmentAvailability {
  equipment_id: string;
  equipment_name: string;
  equipment_type?: string;
  schedule?: ScheduleSlot[];
  summary?: {
    total_slots?: number;
    running_slots?: number;
    utilization?: number;
  };
}

export interface CurrentScheduleResponse {
  date: string;
  availability: EquipmentAvailability[];
  summary: {
    total_equipments: number;
    total_scheduled_orders: number;
    running_orders: number;
  };
}

export const schedulerService = {
  // Get current schedule for Gantt chart
  async getCurrentSchedule(params: {
    date?: string;
    includeRunning?: boolean;
  }): Promise<CurrentScheduleResponse> {
    const response = await api.get("/api/v1/scheduler/current-schedule", {
      params: {
        date: params.date,
        include_running: params.includeRunning ?? true,
      },
    });
    return response.data;
  },

  // Get equipment availability for scheduler
  async getEquipmentAvailability(equipmentIds?: number[]): Promise<{
    machines: MachineForScheduler[];
    count: number;
  }> {
    const params = equipmentIds ? { equipment_ids: equipmentIds.join(",") } : {};
    const response = await api.get("/api/v1/scheduler/equipment-availability", { params });
    return response.data;
  },

  // Get work orders for scheduling
  async getWorkOrdersForScheduling(
    status: string = "READY",
    limit: number = 100
  ): Promise<{
    work_orders: any[];
    count: number;
  }> {
    const response = await api.get("/api/v1/scheduler/work-orders", {
      params: { status, limit },
    });
    return response.data;
  },

  // Create scheduling request
  async createSchedulingRequest(
    params: SchedulingRequestParams
  ): Promise<SchedulingRequest> {
    const response = await api.post("/api/v1/scheduler/create-request", params);
    return response.data;
  },

  // Process scheduling result
  async processSchedulingResult(result: SchedulingResult): Promise<{
    success: boolean;
    message: string;
    updated_orders: any[];
    statistics?: SchedulingStatistics;
  }> {
    const response = await api.post("/api/v1/scheduler/process-result", result);
    return response.data;
  },

  // Get machine type parameters
  async getMachineTypeParams(): Promise<{
    machine_types: Record<string, any>;
  }> {
    const response = await api.get("/api/v1/scheduler/machine-type-params");
    return response.data;
  },

  // Execute scheduling (without applying to work orders)
  async solveSchedule(params: {
    horizon_hours?: number;
    include_running?: boolean;
    include_scheduled?: boolean;
    solver_type?: string;
    time_limit_sec?: number;
    lot_size?: number;
    amr_transfer_time_sec?: number;
    signal?: AbortSignal;
  }): Promise<{
    scheduling_result: SchedulingResult;
    processing_result: null;
  }> {
    const response = await api.post("/api/v1/scheduler/solve", {
      horizon_hours: params.horizon_hours || 24,
      include_running: params.include_running || false,
      include_scheduled: params.include_scheduled || false,
      solver_type: params.solver_type || "OR_TOOLS",
      time_limit_sec: params.time_limit_sec ?? undefined,
      lot_size: params.lot_size ?? 1,
      amr_transfer_time_sec: params.amr_transfer_time_sec ?? 60,
      auto_apply: false,
    }, { signal: params.signal });
    return response.data;
  },

  // Approve and apply scheduling result to work orders
  async approveSchedule(result: SchedulingResult): Promise<{
    success: boolean;
    message: string;
    updated_orders: any[];
    statistics?: SchedulingStatistics;
    quality_metrics?: Record<string, any>;
  }> {
    const response = await api.post("/api/v1/scheduler/process-result", result);
    return response.data;
  },
};
