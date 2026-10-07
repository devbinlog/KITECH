import api from "@/lib/axios";
import { 
  KPIData, 
  EquipmentUtilization, 
  LotTrace, 
  PaginatedResponse, 
  AnalyticsFilters 
} from "@/types";

export const analyticsService = {
  // KPI Dashboard
  async getKPIData(filters: AnalyticsFilters = {}): Promise<KPIData[]> {
    const response = await api.get<KPIData[]>("/api/v1/analytics/kpi", {
      params: {
        date_from: filters.date_from,
        date_to: filters.date_to,
        period: filters.period || "daily",
        equipment_id: filters.equipment_id,
      },
    });
    return response.data;
  },

  async getKPISummary(date_from?: string, date_to?: string): Promise<{
    overall_oee: number;
    availability: number;
    performance: number;
    quality: number;
    total_production: number;
    defect_rate: number;
    downtime_hours: number;
    trend_data: Array<{
      date: string;
      oee: number;
      availability: number;
      performance: number;
      quality: number;
    }>;
  }> {
    const response = await api.get("/api/v1/analytics/kpi/summary", {
      params: { date_from, date_to },
    });
    return response.data;
  },

  // Equipment Utilization
  async getEquipmentUtilization(filters: AnalyticsFilters = {}): Promise<EquipmentUtilization[]> {
    const response = await api.get<EquipmentUtilization[]>("/api/v1/analytics/equipment/utilization", {
      params: {
        equipment_id: filters.equipment_id,
        date_from: filters.date_from,
        date_to: filters.date_to,
        period: filters.period || "daily",
      },
    });
    return response.data;
  },

  async getEquipmentEfficiency(equipment_id?: number, date_from?: string, date_to?: string): Promise<{
    equipment_name: string;
    planned_time: number;
    actual_time: number;
    downtime_breakdown: Array<{
      reason: string;
      duration: number;
      count: number;
    }>;
    efficiency_trend: Array<{
      date: string;
      efficiency: number;
      utilization: number;
    }>;
    maintenance_schedule: Array<{
      maintenance_type: string;
      scheduled_date: string;
      status: string;
    }>;
  }> {
    const response = await api.get(`/api/v1/analytics/equipment/efficiency`, {
      params: {
        equipment_id,
        date_from,
        date_to,
      },
    });
    return response.data;
  },

  // Lot Tracking
  async getLotTraces(filters: AnalyticsFilters = {}): Promise<PaginatedResponse<LotTrace>> {
    const response = await api.get<PaginatedResponse<LotTrace>>("/api/v1/analytics/lot-trace", {
      params: {
        date_from: filters.date_from,
        date_to: filters.date_to,
        page: filters.page || 1,
        limit: filters.limit || 20,
      },
    });
    return response.data;
  },

  async getLotTraceByLotNo(lot_no: string): Promise<LotTrace> {
    const response = await api.get<LotTrace>(`/api/v1/analytics/lot-trace/${lot_no}`);
    return response.data;
  },

  async getLotTraceHistory(lot_no: string): Promise<{
    lot_info: LotTrace;
    process_flow: Array<{
      process_name: string;
      equipment_name: string;
      start_time: string;
      end_time: string | null;
      duration: number | null;
      status: string;
      parameters: Record<string, any>;
    }>;
    quality_checkpoints: Array<{
      inspection_type: string;
      inspection_date: string;
      judgment: string;
      defects: Array<{
        item_name: string;
        measured_value: number;
        specification: string;
        judgment: string;
      }>;
    }>;
  }> {
    const response = await api.get(`/api/v1/analytics/lot-trace/${lot_no}/history`);
    return response.data;
  },

  // Production Analytics
  async getProductionTrends(date_from?: string, date_to?: string, period: string = "daily"): Promise<{
    production_volume: Array<{
      date: string;
      planned: number;
      actual: number;
      efficiency: number;
    }>;
    quality_trends: Array<{
      date: string;
      pass_rate: number;
      defect_rate: number;
      rework_rate: number;
    }>;
    cycle_time_trends: Array<{
      date: string;
      avg_cycle_time: number;
      planned_cycle_time: number;
      variance: number;
    }>;
  }> {
    const response = await api.get("/api/v1/analytics/production/trends", {
      params: { date_from, date_to, period },
    });
    return response.data;
  },

  // Resource Analytics
  async getResourceUtilization(date_from?: string, date_to?: string): Promise<{
    equipment_utilization: Array<{
      equipment_name: string;
      utilization_rate: number;
      available_hours: number;
      used_hours: number;
      maintenance_hours: number;
    }>;
    workforce_utilization: Array<{
      shift: string;
      planned_hours: number;
      worked_hours: number;
      overtime_hours: number;
      efficiency: number;
    }>;
    material_consumption: Array<{
      material_name: string;
      planned_consumption: number;
      actual_consumption: number;
      variance: number;
    }>;
  }> {
    const response = await api.get("/api/v1/analytics/resources", {
      params: { date_from, date_to },
    });
    return response.data;
  },

  // Energy Analytics
  async getEnergyConsumption(equipment_id?: number, date_from?: string, date_to?: string): Promise<{
    total_consumption: number;
    cost: number;
    consumption_by_equipment: Array<{
      equipment_name: string;
      consumption: number;
      cost: number;
      efficiency_rating: number;
    }>;
    hourly_consumption: Array<{
      hour: string;
      consumption: number;
      peak_demand: number;
    }>;
    energy_efficiency_trends: Array<{
      date: string;
      consumption_per_unit: number;
      benchmark: number;
    }>;
  }> {
    const response = await api.get("/api/v1/analytics/energy", {
      params: {
        equipment_id,
        date_from,
        date_to,
      },
    });
    return response.data;
  },

  // Predictive Analytics
  async getPredictiveInsights(equipment_id?: number): Promise<{
    maintenance_predictions: Array<{
      equipment_name: string;
      predicted_failure_date: string;
      confidence: number;
      recommended_action: string;
      cost_impact: number;
    }>;
    quality_predictions: Array<{
      product_name: string;
      process_name: string;
      predicted_defect_rate: number;
      key_factors: Array<{
        factor: string;
        impact: number;
      }>;
    }>;
    capacity_forecasts: Array<{
      date: string;
      predicted_capacity: number;
      bottlenecks: string[];
      recommendations: string[];
    }>;
  }> {
    const response = await api.get("/api/v1/analytics/predictions", {
      params: { equipment_id },
    });
    return response.data;
  },
};