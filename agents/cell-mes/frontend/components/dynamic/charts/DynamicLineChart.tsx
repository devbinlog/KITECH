'use client';

/**
 * Dynamic Line Chart Component
 * Renders a line chart using Recharts based on data from the NL Router
 */

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { DynamicChartProps } from '@/types/nlm';

const DEFAULT_COLORS = [
  '#3b82f6', // blue
  '#22c55e', // green
  '#f59e0b', // amber
  '#ef4444', // red
  '#8b5cf6', // purple
  '#06b6d4', // cyan
];

export function DynamicLineChart({
  title,
  data,
  xKey = 'name',
  yKey = 'value',
  colors = DEFAULT_COLORS,
  targetLine,
}: DynamicChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        {title && <h3 className="font-semibold text-gray-800 mb-4">{title}</h3>}
        <div className="h-64 flex items-center justify-center text-gray-500">
          데이터가 없습니다
        </div>
      </div>
    );
  }

  // Detect multiple data series
  const dataKeys = Object.keys(data[0]).filter(
    (key) => key !== xKey && typeof data[0][key] === 'number'
  );

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      {title && <h3 className="font-semibold text-gray-800 mb-4">{title}</h3>}
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey={xKey}
              tick={{ fontSize: 12 }}
              tickLine={false}
              axisLine={{ stroke: '#e5e7eb' }}
            />
            <YAxis
              tick={{ fontSize: 12 }}
              tickLine={false}
              axisLine={{ stroke: '#e5e7eb' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                fontSize: '12px',
              }}
            />
            {dataKeys.length > 1 && <Legend />}

            {targetLine !== undefined && (
              <ReferenceLine
                y={targetLine}
                stroke="#ef4444"
                strokeDasharray="5 5"
                label={{
                  value: `목표: ${targetLine}`,
                  position: 'right',
                  fontSize: 12,
                  fill: '#ef4444',
                }}
              />
            )}

            {dataKeys.length <= 1 ? (
              <Line
                type="monotone"
                dataKey={yKey}
                stroke={colors[0]}
                strokeWidth={2}
                dot={{ fill: colors[0], strokeWidth: 2 }}
                activeDot={{ r: 6 }}
              />
            ) : (
              dataKeys.map((key, idx) => (
                <Line
                  key={key}
                  type="monotone"
                  dataKey={key}
                  stroke={colors[idx % colors.length]}
                  strokeWidth={2}
                  dot={{ fill: colors[idx % colors.length], strokeWidth: 2 }}
                  activeDot={{ r: 6 }}
                />
              ))
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default DynamicLineChart;
