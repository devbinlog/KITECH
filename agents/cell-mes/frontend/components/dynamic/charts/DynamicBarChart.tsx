'use client';

/**
 * Dynamic Bar Chart Component
 * Renders a bar chart using Recharts based on data from the NL Router
 */

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
} from 'recharts';
import { DynamicChartProps } from '@/types/nlm';

const DEFAULT_COLORS = [
  '#3b82f6', // blue
  '#22c55e', // green
  '#f59e0b', // amber
  '#ef4444', // red
  '#8b5cf6', // purple
];

function getColorByValue(
  value: number,
  thresholds?: { red?: number; yellow?: number; green?: number }
): string {
  if (!thresholds) return DEFAULT_COLORS[0];

  const { red = 0, yellow = 50, green = 80 } = thresholds;

  if (value >= green) return '#22c55e'; // green
  if (value >= yellow) return '#f59e0b'; // amber
  return '#ef4444'; // red
}

export function DynamicBarChart({
  title,
  data,
  xKey = 'name',
  yKey = 'value',
  colors = DEFAULT_COLORS,
  targetLine,
  colorByValue = false,
  thresholds,
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
          <BarChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
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
              <Bar dataKey={yKey} radius={[4, 4, 0, 0]}>
                {data.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={
                      colorByValue
                        ? getColorByValue(entry[yKey] as number, thresholds)
                        : colors[0]
                    }
                  />
                ))}
              </Bar>
            ) : (
              dataKeys.map((key, idx) => (
                <Bar
                  key={key}
                  dataKey={key}
                  fill={colors[idx % colors.length]}
                  radius={[4, 4, 0, 0]}
                />
              ))
            )}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default DynamicBarChart;
