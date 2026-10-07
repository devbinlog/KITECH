'use client'

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

interface UtilizationChartProps {
  data: Record<string, number>
  average: number
}

export function UtilizationChart({ data, average }: UtilizationChartProps) {
  const chartData = Object.entries(data).map(([machine, utilization]) => ({
    machine,
    utilization: parseFloat(utilization.toFixed(2)),
  }))

  const getColor = (value: number) => {
    if (value > 80) return '#FF6B6B' // High
    if (value > 50) return '#4ECDC4' // Medium
    return '#95E1D3' // Low
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-2">⚙️ Machine Utilization</h2>
      <div className="text-sm text-gray-600 mb-4">Average: {average.toFixed(2)}%</div>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="machine" />
          <YAxis label={{ value: 'Utilization %', angle: -90, position: 'insideLeft' }} />
          <Tooltip 
            formatter={(value) => `${value}%`}
            contentStyle={{ backgroundColor: '#f3f4f6', border: '1px solid #e5e7eb', borderRadius: '8px' }}
          />
          <Bar dataKey="utilization" radius={[8, 8, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getColor(entry.utilization)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
