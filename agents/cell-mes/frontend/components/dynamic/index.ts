/**
 * Dynamic Component Registry
 * Maps component type names to their implementations for dynamic rendering
 */

import dynamic from 'next/dynamic';
import { ComponentType } from 'react';

// Lazy load all dynamic components
export const ComponentRegistry: Record<string, ComponentType<any>> = {
  KPICard: dynamic(() => import('./KPICard')),
  DataTable: dynamic(() => import('./DynamicDataTable')),
  LineChart: dynamic(() => import('./charts/DynamicLineChart')),
  BarChart: dynamic(() => import('./charts/DynamicBarChart')),
  PieChart: dynamic(() => import('./charts/DynamicPieChart')),
  GanttChart: dynamic(() => import('./charts/GanttChart')),
  StatusGrid: dynamic(() => import('./StatusGrid')),
  StatusCards: dynamic(() => import('./StatusCards')),
  TraceabilityTimeline: dynamic(() => import('./TraceabilityTimeline')),
};

// Re-export components and renderer
export { DynamicRenderer } from './DynamicRenderer';
export { default as KPICard } from './KPICard';
export { default as DynamicDataTable } from './DynamicDataTable';
export { default as StatusGrid } from './StatusGrid';
export { default as StatusCards } from './StatusCards';
export { default as GanttChart } from './charts/GanttChart';
export { default as TraceabilityTimeline } from './TraceabilityTimeline';
