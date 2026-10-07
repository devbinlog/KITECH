'use client'

import { QualityMetrics, Statistics } from '@/app/lib/api'

interface MetricsGridProps {
  metrics: QualityMetrics
  statistics: Statistics
}

export function MetricsGrid({ metrics, statistics }: MetricsGridProps) {
  const cards = [
    {
      icon: '📊',
      title: 'Total Tasks',
      value: metrics.total_scheduled_tasks,
      unit: 'scheduled',
    },
    {
      icon: '⏱️',
      title: 'Makespan',
      value: metrics.makespan_hours.toFixed(2),
      unit: 'hours',
    },
    {
      icon: '📅',
      title: 'Lateness',
      value: metrics.total_lateness_hours.toFixed(2),
      unit: 'hours',
    },
    {
      icon: '⚙️',
      title: 'Avg Utilization',
      value: metrics.avg_machine_utilization.toFixed(2),
      unit: '%',
    },
    {
      icon: '🔧',
      title: 'Machines',
      value: metrics.total_machines,
      unit: 'available',
    },
    {
      icon: '⏰',
      title: 'Solve Time',
      value: statistics.solve_time_sec.toFixed(3),
      unit: 'seconds',
    },
  ]

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 p-6 bg-gray-50 border-b border-gray-200">
      {cards.map((card, index) => (
        <div
          key={index}
          className="bg-white p-4 rounded-lg shadow-md border-l-4 border-primary hover:shadow-lg transition-shadow"
        >
          <div className="text-2xl mb-2">{card.icon}</div>
          <h3 className="text-xs font-bold text-gray-600 uppercase tracking-wide mb-2">
            {card.title}
          </h3>
          <div className="text-2xl font-bold text-primary">{card.value}</div>
          <div className="text-xs text-gray-500 mt-1">{card.unit}</div>
        </div>
      ))}
    </div>
  )
}
