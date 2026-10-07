// User types
export interface User {
  id: number;
  username: string;
  role: "ADMIN" | "OPERATOR";
  created_at: string;
}

// Master data types
export interface StdProcess {
  id: number;
  code: string;
  name: string;
  description: string | null;
  process_category: string | null; // MACHINING, ASSEMBLY, INSPECTION, etc.
  equipment_type: string | null;
  required_machines: string[] | null;
  cycle_time_sec: number;
  setup_time_sec: number;
  created_at: string;
}

export interface Product {
  id: number;
  code: string;
  name: string;
  product_category: string | null; // BRACKET, SHAFT, HOUSING, etc.
  unit: string;
  is_deleted: boolean;
  created_at: string;
  current_dt_project?: DtProjectSummary | null;
}

export interface DtProjectWorkplan {
  id: number;
  workplan_id: string;
  parent_workplan_id: string | null;
  display_name: string | null;
  source_path: string;
  level: number;
  sequence: number;
  has_direct_steps: boolean;
}

export interface DtProjectSelect {
  asset_global_id: string;
  asset_id: string;
  element_id: string;
  element_full_id?: string | null;
  element_category?: string;
  external_project_id?: string | null;
  display_name?: string | null;
  uuid?: string | null;
}

export interface DtProjectSummary extends DtProjectSelect {
  id: number;
  platform: string;
  element_category: string;
  workplans: DtProjectWorkplan[];
}

export interface DtProjectLookup extends DtProjectSelect {
  raw_metadata: Record<string, any>;
}

export interface DtFileRef {
  id: number;
  platform: string;
  external_file_id: string;
  asset_global_id: string;
  asset_id: string | null;
  element_id: string | null;
  element_full_id: string | null;
  element_category: string;
  display_name: string | null;
  path: string;
  references: Record<string, any> | null;
  workplan_id: string | null;
}

export interface ProcessRoutingFile {
  id: number;
  process_routing_id: number;
  file_type: "NC" | "IMAGE" | "DOC";
  file_path: string;
  original_filename?: string | null;
  source_type?: "LOCAL_UPLOAD" | "DTP";
  dt_file_ref_id?: number | null;
  dt_file?: DtFileRef | null;
  compatible_machines?: string[] | null;
  sort_order: number;
  created_at: string;
}

export interface ProcessRouting {
  id: number;
  product_id: number;
  std_process_id: number;
  sequence: number;
  revision: string;
  setup_id: string | null;
  dt_workplan_id?: number | null;
  dt_workplan?: DtProjectWorkplan | null;
  required_machines: string[] | null;
  cycle_time_sec: number | null;
  cycle_time_breakdown?: Record<string, any> | null;
  remarks: string | null;
  files: ProcessRoutingFile[];
  std_process: StdProcess | null;
  created_at: string;
}

export interface Scenario {
  id: number;
  code: string;
  product_id: number | null;
  name: string;
  file_path: string;
  is_active: boolean;
  created_at: string;
}

// Equipment types
export interface Equipment {
  id: number;
  eq_code: string;
  aas_id: string | null;
  eq_name: string;
  model_name: string | null;
  equipment_type: "CNC" | "ROBOT" | "AMR" | "PLC" | "RACK" | "FEEDER" | "QCM" | string;
  location: string | null;
  cell_id: number | null;
  connection_config: Record<string, any>;
  spec_data: Record<string, any>;
  last_data: Record<string, any>;
  current_status: "RUN" | "STOP" | "ERROR";
  updated_at: string;
  last_connected_at: string | null;
  is_deleted: boolean;
}

export interface EquipmentStatus {
  id: number;
  aas_id: string | null;
  eq_name: string;
  equipment_type: string;
  current_status: string;
  last_data: Record<string, any>;
  last_connected_at: string | null;
}

export interface EquipmentSync {
  synced_count: number;
  created: string[];
  updated: string[];
  deleted?: string[];
  errors: string[];
}

export interface EquipmentVirtualCopyRequest {
  count: number;
  name_prefix?: string;
  machineType?: string;
  overrides?: Record<string, any>;
}

export interface EquipmentVirtualCopyResult {
  created_count: number;
  created: Equipment[];
}

// Production types
export interface WorkOrder {
  id: number;
  lot_no: string;
  product_id: number;
  scenario_id: number | null;
  target_qty: number;
  qty: number;
  priority: number;
  due_date: string | null;
  plan_start: string | null;
  plan_end: string | null;
  remarks: string | null;
  status: "READY" | "SCHEDULED" | "RUNNING" | "PAUSE" | "DONE" | "ERROR" | "CANCEL";
  created_at: string;
  // Product relation (optional, loaded when needed)
  product?: Product;
  // Scheduled equipment from ProdResult.target_equipment_id
  scheduled_equipment_name?: string | null;
  // Optional fields from backend
  completed_qty?: number;
  current_process?: string;
  start_time?: string;
  end_time?: string;
}

export interface UnitScenario {
  id: number;
  name: string;
  file_path: string;
}

export interface ProductionUnit {
  id: number;
  work_order_id: number;
  unit_no: number;
  scenario_id: number | null;
  status: "READY" | "SCENARIO_HOLD" | "RUNNING" | "PAUSED" | "DONE" | "ERROR" | "CANCEL" | string;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  scenario_hold_started_at?: string | null;
  scenario_hold_by?: string | null;
  scenario?: UnitScenario | null;
}

export type MiddlewareResumeMode = "CURRENT_STEP" | "SKIP_CURRENT_STEP" | "SPECIFIC_STEP";

export interface MiddlewareUnitState {
  unit_no: string;
  mes_unit_id?: number | null;
  mes_status?: string | null;
  middleware_status?: string | null;
  current_step_id?: string | null;
  alarm_step_id?: string | null;
  alarm_message?: string | null;
  pending_stop?: boolean;
  acq_map?: Record<string, any>;
  activity?: Record<string, any> | null;
  recipe_name?: string | null;
  recipe_steps?: Array<Record<string, any>>;
  nc_files?: Array<Record<string, any>>;
  unit_var?: any;
  unit_res?: any;
  unit_loc?: any;
  unit_pos?: any;
  raw?: Record<string, any>;
}

export interface OrderMiddlewareState {
  status: "success";
  order_id: number;
  lot_no: string;
  mes_status: string;
  middleware_lot_status?: string | null;
  sync_status: "SYNCED" | "MISMATCHED" | "MIDDLEWARE_NOT_FOUND" | "ERROR";
  last_synced_at: string;
  units: MiddlewareUnitState[];
  raw?: Record<string, any>;
}

export interface ProdResult {
  id: number;
  work_order_id: number;
  process_routing_id: number | null;
  equipment_id: number | null;
  ok_qty: number;
  ng_qty: number;
  start_time: string | null;
  end_time: string | null;
}

// API response types
export interface Token {
  access_token: string;
  token_type: string;
}

export interface Message {
  message: string;
}

// Paginated response type
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

// Work order filters
export interface OrderFilters {
  status?: string;
  view?: "today" | "upcoming" | "active" | "all";
  dateFrom?: string;
  dateTo?: string;
  page?: number;
  limit?: number;
  sortBy?: "plan_start" | "due_date" | "priority" | "created_at";
  sortOrder?: "asc" | "desc";
}

// Production result filters
export interface ResultFilters {
  workOrderId?: number;
  page?: number;
  limit?: number;
}

// Quality types
export interface InspectionPlan {
  id: number;
  product_id: number;
  process_routing_id: number | null;
  inspection_type: "INCOMING" | "IN_PROCESS" | "FINAL";
  inspection_items: InspectionItem[];
  // Backend flat fields per plan (characteristic-based model)
  characteristic?: string;
  nominal?: number | null;
  usl?: number | null;
  lsl?: number | null;
  is_active: boolean;
  created_at: string;
  product?: Product;
}

export interface InspectionItem {
  id: number;
  inspection_plan_id: number;
  item_name: string;
  specification: string;
  usl: number | null; // Upper Specification Limit
  lsl: number | null; // Lower Specification Limit
  target: number | null;
  measurement_method: string;
  sort_order: number;
}

export interface InspectionItemFormData {
  id?: number;
  inspection_plan_id?: number;
  item_name: string;
  specification: string;
  usl: number | null;
  lsl: number | null;
  target: number | null;
  measurement_method: string;
  sort_order: number;
}

export interface InspectionResult {
  id: number;
  inspection_plan_id: number;
  work_order_id: number;
  equipment_id?: number;
  lot_no: string | null;
  serial_no: string | null;
  source: string;
  device_id?: number;
  measured_value: number;
  deviation: number | null;
  is_conforming: boolean;
  measurement_metadata: Record<string, any> | null;
  measured_at: string;
  created_at: string;
  // Computed fields from backend
  judgment: "OK" | "NG";
  inspector: string | null;
  inspection_date: string | null;
  // Eager-loaded relationships
  inspection_plan?: InspectionPlan;
  work_order?: WorkOrder;
}

export interface MeasuredValue {
  id: number;
  inspection_result_id: number;
  inspection_item_id: number;
  measured_value: number;
  judgment: "OK" | "NG";
  inspection_item?: InspectionItem;
}

export interface SPCData {
  id: number;
  inspection_item_id: number;
  sample_date: string;
  sample_values: number[];
  x_bar: number;
  r_value: number;
  ucl_x: number;
  lcl_x: number;
  ucl_r: number;
  lcl_r: number;
  inspection_item?: InspectionItem;
}

export interface NCR {
  id: number;
  ncr_no: string;
  work_order_id: number | null;
  inspection_result_id: number | null;
  machine_id: number | null;
  lot_no: string | null;
  serial_no: string | null;
  defect_type: "DIMENSION" | "SURFACE" | "MATERIAL" | "PROCESS" | "OTHER";
  characteristic: string;
  specified_value: number | null;
  actual_value: number | null;
  disposition: string;
  description: string;
  defect_description?: string;
  severity?: "CRITICAL" | "MAJOR" | "MINOR";
  root_cause: string | null;
  corrective_action: string | null;
  preventive_action?: string | null;
  reported_by: string;
  created_by?: string;
  assigned_to: string | null;
  due_date: string | null;
  status: "OPEN" | "INVESTIGATING" | "CORRECTIVE_ACTION" | "IN_PROGRESS" | "CLOSED" | "CANCELLED";
  reported_at: string;
  closed_at: string | null;
  is_auto_generated: boolean;
  trigger_data: Record<string, any> | null;
  created_at: string;
  updated_at: string;
  work_order?: WorkOrder;
  inspection_result?: InspectionResult;
}

// Downtime types
export interface DowntimeReason {
  id: number;
  category: "PLANNED" | "UNPLANNED" | "MAINTENANCE" | "SETUP" | "OTHER";
  code: string;
  name: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
}

export interface Downtime {
  id: number;
  equipment_id: number;
  reason_id: number;
  start_time: string;
  end_time: string | null;
  duration_sec: number | null;
  remarks: string | null;
  recorded_by: string;
  created_at: string;
  equipment?: Equipment;
  reason?: DowntimeReason;
}

export interface DowntimeFilters {
  equipment_id?: number;
  reason_id?: number;
  category?: string;
  status?: "ACTIVE" | "COMPLETED" | "all";
  date_from?: string;
  date_to?: string;
  page?: number;
  limit?: number;
}

export interface DowntimeSummary {
  category: string;
  count: number;
  total_duration_sec: number;
}

// Alarm types
export interface AlarmDefinition {
  id: number;
  equipment_type: string | null;
  alarm_code: string;
  name: string;
  description: string | null;
  severity: "EMERGENCY" | "CRITICAL" | "MAJOR" | "WARNING" | "MINOR" | "INFO";
  recommended_action: string | null;
  is_active: boolean;
  created_at: string;
}

export interface Alarm {
  id: number;
  definition_id: number;
  equipment_id: number;
  work_order_id: number | null;
  occurred_at: string;
  message: string;
  value: number | null;
  status: string;
  acknowledged_at: string | null;
  acknowledged_by: string | null;
  resolved_at: string | null;
  resolved_by: string | null;
  resolution_note: string | null;
  created_at: string;
  duration_minutes: number | null;
  definition?: {
    id: number;
    code: string;
    name: string;
    severity: "EMERGENCY" | "CRITICAL" | "MAJOR" | "WARNING" | "MINOR" | "INFO";
    category: string;
    description: string | null;
    recommended_action: string | null;
    auto_stop: boolean;
    is_active: boolean;
    created_at: string;
  };
  equipment?: Equipment;
}

export interface AlarmFilters {
  equipment_id?: number;
  severity?: string;
  status?: "ACTIVE" | "ACKNOWLEDGED" | "RESOLVED" | "all";
  date_from?: string;
  date_to?: string;
  page?: number;
  limit?: number;
}

export interface AlarmSummary {
  severity: string;
  count: number;
  equipment_counts: Record<string, number>;
}

// Analytics types
export interface KPIData {
  period: string;
  oee: number; // Overall Equipment Effectiveness
  availability: number;
  performance: number;
  quality: number;
  mtbf: number; // Mean Time Between Failures
  mttr: number; // Mean Time To Repair
  yield_rate: number;
  defect_rate: number;
}

export interface EquipmentUtilization {
  equipment_id: number;
  equipment_name: string;
  equipment_type: string;
  planned_time: number;
  running_time: number;
  idle_time: number;
  maintenance_time: number;
  error_time: number;
  utilization_rate: number;
  availability_rate: number;
  equipment?: Equipment;
}

export interface LotTrace {
  lot_no: string;
  product_id: number;
  start_time: string;
  end_time: string | null;
  current_process: string | null;
  current_equipment: string | null;
  status: "IN_PROGRESS" | "COMPLETED" | "ON_HOLD";
  process_history: ProcessStep[];
  quality_results: InspectionResult[];
  product?: Product;
}

export interface ProcessStep {
  id: number;
  lot_no: string;
  process_name: string;
  equipment_name: string;
  start_time: string;
  end_time: string | null;
  status: "COMPLETED" | "IN_PROGRESS" | "ERROR";
  cycle_time: number | null;
  remarks: string | null;
}

// Filter types for Quality & Analytics
export interface QualityFilters {
  inspection_type?: string;
  product_id?: number;
  work_order_id?: number;
  inspection_plan_id?: number;
  status?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  limit?: number;
  offset?: number;
}

export interface AnalyticsFilters {
  equipment_id?: number;
  date_from?: string;
  date_to?: string;
  period?: "daily" | "weekly" | "monthly";
  page?: number;
  limit?: number;
}
