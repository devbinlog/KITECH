import api from "@/lib/axios";
import {
  InspectionPlan,
  InspectionResult,
  SPCData,
  NCR,
  PaginatedResponse,
  QualityFilters,
} from "@/types";

export const qualityService = {
  // Inspection Plans
  async getInspectionPlans(filters: QualityFilters = {}): Promise<PaginatedResponse<InspectionPlan>> {
    const response = await api.get<PaginatedResponse<InspectionPlan>>("/api/v1/quality/inspection-plans", {
      params: {
        inspection_type: filters.inspection_type,
        product_id: filters.product_id,
        page: filters.page || 1,
        limit: filters.limit || 20,
      },
    });
    return response.data;
  },

  async getInspectionPlanById(id: number): Promise<InspectionPlan> {
    const response = await api.get<InspectionPlan>(`/api/v1/quality/inspection-plans/${id}`);
    return response.data;
  },

  async createInspectionPlan(data: {
    product_id: number;
    inspection_type: "INCOMING" | "IN_PROCESS" | "FINAL";
    characteristic: string;
    nominal?: number;
    usl?: number;
    lsl?: number;
    unit?: string;
  }): Promise<InspectionPlan> {
    const response = await api.post<InspectionPlan>("/api/v1/quality/inspection-plans", data);
    return response.data;
  },

  async updateInspectionPlan(id: number, data: Partial<InspectionPlan>): Promise<InspectionPlan> {
    const response = await api.put<InspectionPlan>(`/api/v1/quality/inspection-plans/${id}`, data);
    return response.data;
  },

  async deleteInspectionPlan(id: number): Promise<void> {
    await api.delete(`/api/v1/quality/inspection-plans/${id}`);
  },

  // Inspection Results
  async getInspectionResults(filters: QualityFilters = {}): Promise<InspectionResult[]> {
    const response = await api.get<InspectionResult[]>("/api/v1/quality/inspection-results", {
      params: {
        work_order_id: filters.work_order_id,
        inspection_plan_id: filters.inspection_plan_id,
        date_from: filters.date_from,
        date_to: filters.date_to,
        limit: filters.limit || 100,
        offset: filters.offset || 0,
      },
    });
    return response.data;
  },

  async getInspectionResultById(id: number): Promise<InspectionResult> {
    const response = await api.get<InspectionResult>(`/api/v1/quality/inspection-results/${id}`);
    return response.data;
  },

  async createInspectionResult(data: {
    inspection_plan_id: number;
    work_order_id: number;
    lot_no: string;
    measured_values: Array<{
      inspection_item_id: number;
      measured_value: number;
      judgment: "OK" | "NG";
    }>;
    inspector: string;
    inspection_date: string;
    judgment: "OK" | "NG" | "REWORK";
    remarks?: string;
  }): Promise<InspectionResult> {
    // Backend InspectionResultCreate expects a single measured_value (float), not an array.
    // Use first measured_value from the array, or 0 as fallback.
    const measured_value = data.measured_values.length > 0
      ? data.measured_values[0].measured_value
      : 0;
    const payload = {
      inspection_plan_id: data.inspection_plan_id,
      work_order_id: data.work_order_id,
      measured_value,
      lot_no: data.lot_no || null,
      source: "MANUAL",
      measurement_metadata: {
        inspector: data.inspector,
        method: data.remarks || undefined,
        judgment: data.judgment,
        all_measurements: data.measured_values,
      },
    };
    const response = await api.post<InspectionResult>("/api/v1/quality/inspection-results", payload);
    return response.data;
  },

  async updateInspectionResult(id: number, data: Partial<InspectionResult>): Promise<InspectionResult> {
    const response = await api.put<InspectionResult>(`/api/v1/quality/inspection-results/${id}`, data);
    return response.data;
  },

  // SPC Data
  async getSPCData(characteristic: string, date_from?: string, date_to?: string): Promise<SPCData[]> {
    // Backend uses /spc/charts/{characteristic} which returns SPCChartWithDataPoints[]
    const response = await api.get<any[]>(`/api/v1/quality/spc/charts/${encodeURIComponent(characteristic)}`, {
      params: { date_from, date_to },
    });
    // Transform backend chart+dataPoints into frontend SPCData[] format
    const results: SPCData[] = [];
    for (const chart of (response.data || [])) {
      for (const dp of (chart.data_points || [])) {
        results.push({
          id: dp.id,
          inspection_item_id: chart.inspection_plan_id,
          sample_date: dp.created_at,
          sample_values: dp.raw_values || [],
          x_bar: dp.mean_value,
          r_value: dp.range_value ?? 0,
          ucl_x: chart.upper_control_limit,
          lcl_x: chart.lower_control_limit,
          ucl_r: chart.range_upper_control_limit ?? 0,
          lcl_r: chart.range_lower_control_limit ?? 0,
        });
      }
    }
    return results;
  },

  async generateSPCData(_inspection_item_id: number, _sample_size: number = 5): Promise<SPCData[]> {
    // Backend does not have a generate endpoint - SPC data comes from inspection results
    console.warn("SPC data generation not available - data comes from inspection results");
    return [];
  },

  // NCR (Non-Conformance Reports)
  async getNCRs(filters: QualityFilters = {}): Promise<NCR[]> {
    const limit = filters.limit || 20;
    const page = filters.page || 1;
    const offset = filters.offset ?? (page - 1) * limit;
    const response = await api.get<NCR[]>("/api/v1/quality/ncr", {
      params: {
        status: filters.status,
        date_from: filters.date_from,
        date_to: filters.date_to,
        limit,
        offset,
      },
    });
    return response.data;
  },

  async getNCRById(id: number): Promise<NCR> {
    const response = await api.get<NCR>(`/api/v1/quality/ncr/${id}`);
    return response.data;
  },

  async createNCR(data: {
    ncr_no: string;
    work_order_id?: number;
    inspection_result_id?: number;
    defect_type: "DIMENSION" | "SURFACE" | "MATERIAL" | "PROCESS" | "OTHER";
    defect_description: string;
    severity: "CRITICAL" | "MAJOR" | "MINOR";
    root_cause?: string;
    corrective_action?: string;
    preventive_action?: string;
    created_by: string;
    assigned_to?: string;
  }): Promise<NCR> {
    // Backend NonConformanceCreate expects: defect_type, characteristic, description,
    // reported_by, disposition. Does NOT accept ncr_no (auto-generated) or severity.
    const payload = {
      work_order_id: data.work_order_id || null,
      inspection_result_id: data.inspection_result_id || null,
      defect_type: data.defect_type,
      characteristic: data.defect_type, // use defect_type as characteristic label
      description: data.defect_description,
      reported_by: data.created_by,
      assigned_to: data.assigned_to || null,
      root_cause: data.root_cause || null,
      corrective_action: data.corrective_action || null,
      disposition: "PENDING",
    };
    const response = await api.post<NCR>("/api/v1/quality/ncr", payload);
    return response.data;
  },

  async updateNCR(id: number, data: Partial<NCR>): Promise<NCR> {
    const response = await api.put<NCR>(`/api/v1/quality/ncr/${id}`, data);
    return response.data;
  },

  async updateNCRStatus(id: number, status: string): Promise<NCR> {
    const response = await api.patch<NCR>(`/api/v1/quality/ncr/${id}/status`, { status });
    return response.data;
  },

  // Dashboard Data
  async getQualityDashboard(date_from?: string, date_to?: string): Promise<{
    total_inspections: number;
    pass_rate: number;
    fail_rate: number;
    rework_rate: number;
    open_ncrs: number;
    trend_data: Array<{
      date: string;
      pass_rate: number;
      fail_rate: number;
    }>;
    defect_by_type: Array<{
      defect_type: string;
      count: number;
    }>;
    top_issues: Array<{
      product_name: string;
      defect_count: number;
    }>;
  }> {
    // Backend accepts 'days' parameter only, not date_from/date_to
    let days = 7;
    if (date_from && date_to) {
      const diffMs = new Date(date_to).getTime() - new Date(date_from).getTime();
      days = Math.max(1, Math.min(90, Math.ceil(diffMs / (1000 * 60 * 60 * 24))));
    }

    // W3: Fetch summary + inspection results + NCRs in parallel for charts
    const [summaryRes, resultsRes, ncrsRes] = await Promise.all([
      api.get("/api/v1/quality/dashboard/summary", { params: { days } }),
      api.get("/api/v1/quality/inspection-results", {
        params: { date_from, date_to, limit: 500 },
      }).catch(() => ({ data: [] })),
      api.get("/api/v1/quality/ncr", {
        params: { date_from, date_to, limit: 200 },
      }).catch(() => ({ data: [] })),
    ]);

    const data = summaryRes.data;
    const results: any[] = Array.isArray(resultsRes.data) ? resultsRes.data : resultsRes.data?.items || [];
    const ncrs: any[] = Array.isArray(ncrsRes.data) ? ncrsRes.data : ncrsRes.data?.items || [];

    // Compute trend_data: group results by date, calculate pass/fail rate
    const byDate: Record<string, { ok: number; total: number }> = {};
    for (const r of results) {
      const date = (r.inspection_date || r.created_at || "").split("T")[0];
      if (!date) continue;
      if (!byDate[date]) byDate[date] = { ok: 0, total: 0 };
      byDate[date].total++;
      if (r.judgment === "OK") byDate[date].ok++;
    }
    const trend_data = Object.entries(byDate)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([date, { ok, total }]) => ({
        date,
        pass_rate: total > 0 ? (ok / total) * 100 : 0,
        fail_rate: total > 0 ? ((total - ok) / total) * 100 : 0,
      }));

    // Compute defect_by_type from NCRs
    const defectCounts: Record<string, number> = {};
    for (const ncr of ncrs) {
      const type = ncr.defect_type || "OTHER";
      defectCounts[type] = (defectCounts[type] || 0) + 1;
    }
    const defect_by_type = Object.entries(defectCounts).map(([defect_type, count]) => ({
      defect_type,
      count,
    }));

    // Compute top_issues from NCRs grouped by description
    const productCounts: Record<string, number> = {};
    for (const ncr of ncrs) {
      const name = ncr.product_name || ncr.defect_description?.slice(0, 20) || "Unknown";
      productCounts[name] = (productCounts[name] || 0) + 1;
    }
    const top_issues = Object.entries(productCounts)
      .sort(([, a], [, b]) => (b as number) - (a as number))
      .slice(0, 5)
      .map(([product_name, defect_count]) => ({ product_name, defect_count }));

    return {
      total_inspections: data.total_inspections || 0,
      pass_rate: data.quality_rate_percent ?? 0,
      fail_rate: 100 - (data.quality_rate_percent ?? 0),
      rework_rate: 0,
      open_ncrs: data.open_ncrs || 0,
      trend_data,
      defect_by_type,
      top_issues,
    };
  },
};