'use client'

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

interface LatenessChartProps {
  data: Record<string, number>
  total: number
}

export function LatenessChart({ data, total }: LatenessChartProps) {
  const chartData = Object.entries(data).map(([workOrder, lateness]) => ({
    workOrder,
    lateness: parseFloat(lateness.toFixed(2)),
  }))

  const getColor = (value: number) => {
    if (value > 0) return '#FF6B6B' // Late
    return '#95E1D3' // On time
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-2">📅 Work Order Lateness</h2>
      <div className="text-sm text-gray-600 mb-4">Total Lateness: {total.toFixed(2)} hours</div>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="workOrder" />
          <YAxis label={{ value: 'Lateness (hours)', angle: -90, position: 'insideLeft' }} />
          <Tooltip 
            formatter={(value) => `${value}h`}
            contentStyle={{ backgroundColor: '#f3f4f6', border: '1px solid #e5e7eb', borderRadius: '8px' }}
          />
          <Bar dataKey="lateness" radius={[8, 8, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getColor(entry.lateness)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
