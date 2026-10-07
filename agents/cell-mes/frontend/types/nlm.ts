/**
 * NL-Driven MES Types
 * Types for natural language query processing and dynamic UI rendering
 */

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  uiSchema?: UISchema;
  metadata?: QueryMetadata;
  isError?: boolean;
  timestamp?: string;
}

export interface UISchema {
  layout: 'dashboard' | 'grid' | 'single' | 'split' | 'list';
  title?: string;
  components: UIComponent[];
}

export interface UIComponent {
  type: string;
  props: Record<string, unknown>;
}

export interface QueryResult {
  text_response: string;
  ui_schema?: UISchema;
  metadata?: QueryMetadata;
}

export interface QueryMetadata {
  intent: string;
  confidence: number;
  entities: Record<string, unknown>;
  processing_time_ms: number;
}

// KPI Card props
export interface KPICardProps {
  title: string;
  value: number | string;
  unit?: string;
  icon?: string;
  trend?: string;
  trendDirection?: 'up' | 'down' | 'neutral';
  target?: number;
  color?: 'blue' | 'green' | 'amber' | 'red' | 'gray';
}

// Data Table props
export interface DynamicDataTableProps {
  title?: string;
  columns: string[] | { key: string; label: string; sortable?: boolean }[];
  data: Record<string, unknown>[];
  searchable?: boolean;
  pagination?: boolean;
  pageSize?: number;
  exportable?: boolean;
}

// Chart props
export interface ChartDataPoint {
  name: string;
  value: number;
  [key: string]: unknown;
}

export interface DynamicChartProps {
  title?: string;
  data: ChartDataPoint[];
  xKey?: string;
  yKey?: string;
  colors?: string[];
  targetLine?: number;
  colorByValue?: boolean;
  thresholds?: {
    red?: number;
    yellow?: number;
    green?: number;
  };
}

// Status Grid props
export interface StatusGridProps {
  title?: string;
  items: StatusItem[];
  columns?: number;
}

export interface StatusItem {
  id: string;
  name: string;
  status: 'RUN' | 'IDLE' | 'ERROR' | 'MAINTENANCE' | 'OFFLINE';
  type?: string;
  metrics?: Record<string, number>;
  currentJob?: string;
  lastUpdated?: string;
}

// Traceability Timeline props
export interface TraceabilityTimelineProps {
  title?: string;
  lotNo: string;
  product?: string;
  steps: TraceabilityStep[];
}

export interface TraceabilityStep {
  sequence: number;
  operation: string;
  operationName: string;
  equipmentId: string;
  equipmentName: string;
  startTime: string;
  endTime?: string;
  status: 'DONE' | 'RUNNING' | 'PENDING' | 'ERROR';
  operator?: string;
  okQty: number;
  ngQty: number;
  parameters?: Record<string, unknown>;
  qualityData?: Record<string, unknown>;
}

// Status Cards props (similar to StatusGrid)
export interface StatusCardsProps {
  title?: string;
  items: StatusCardItem[];
}

export interface StatusCardItem {
  id: string;
  name: string;
  type?: string;
  status: string;
  metrics?: Record<string, unknown>;
}

// Gantt Chart props
export interface GanttChartProps {
  title?: string;
  data: GanttScheduleData;
}

export interface GanttScheduleData {
  schedule?: GanttTask[];
  availability?: EquipmentAvailability[];
  [key: string]: unknown;
}

export interface GanttTask {
  id: string;
  name: string;
  equipmentId?: string;
  equipmentName?: string;
  startTime: string;
  endTime: string;
  status?: string;
  product?: string;
  lotNo?: string;
}

export interface EquipmentAvailability {
  equipment_id: string;
  equipment_name: string;
  schedule?: ScheduleSlot[];
  summary?: {
    total_slots?: number;
    running_slots?: number;
    utilization?: number;
  };
}

export interface ScheduleSlot {
  slot_start: string;
  slot_end: string;
  status: 'RUNNING' | 'AVAILABLE' | 'MAINTENANCE' | 'OFFLINE';
  work_order_id?: number;
  lot_no?: string;
  product?: string;
}
