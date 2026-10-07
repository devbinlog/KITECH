"use client";

import { EquipmentUtilization } from "@/types";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
  ComposedChart,
  Line,
  LineChart
} from "recharts";

interface UtilizationChartProps {
  data: EquipmentUtilization[];
  type?: "bar" | "pie" | "detailed";
  height?: number;
  showLegend?: boolean;
  maxItems?: number;
}

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4'];

export function UtilizationChart({ 
  data = [], 
  type = "bar", 
  height = 300, 
  showLegend = true,
  maxItems = 10 
}: UtilizationChartProps) {
  
  if (!data || data.length === 0) {
    return (
      <div 
        className="flex items-center justify-center text-gray-500 bg-gray-50 rounded-lg"
        style={{ height }}
      >
        <div className="text-center">
          <div className="text-2xl mb-2">📊</div>
          <p>데이터가 없습니다</p>
        </div>
      </div>
    );
  }

  const chartData = data.slice(0, maxItems).map((item, index) => ({
    ...item,
    color: COLORS[index % COLORS.length],
    utilizationLevel: item.utilization_rate >= 85 ? "우수" : 
                     item.utilization_rate >= 70 ? "보통" : "미흡",
  }));

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-semibold text-gray-900">{data.equipment_name}</p>
          <p className="text-sm text-gray-600 mb-2">{data.equipment_type}</p>
          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">가동률:</span>
              <span className="font-medium">{(data.utilization_rate || 0).toFixed(1)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">가동시간:</span>
              <span className="font-medium">{(data.running_time || 0).toFixed(1)}h</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">대기시간:</span>
              <span className="font-medium">{(data.idle_time || 0).toFixed(1)}h</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">오류시간:</span>
              <span className="font-medium text-red-600">{(data.error_time || 0).toFixed(1)}h</span>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  const PieTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-semibold text-gray-900">{data.equipment_name}</p>
          <p className="text-sm font-medium">{(data.utilization_rate || 0).toFixed(1)}%</p>
        </div>
      );
    }
    return null;
  };

  if (type === "bar") {
    return (
      <div style={{ width: "100%", height }}>
        <ResponsiveContainer>
          <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis 
              dataKey="equipment_name" 
              angle={-45} 
              textAnchor="end" 
              height={80}
              fontSize={12}
              stroke="#6B7280"
            />
            <YAxis 
              domain={[0, 100]} 
              fontSize={12}
              stroke="#6B7280"
            />
            <Tooltip content={<CustomTooltip />} />
            {showLegend && <Legend />}
            <Bar 
              dataKey="utilization_rate" 
              name="가동률 (%)"
              shape={(props: any) => {
                const { payload } = props;
                const fill = payload.utilization_rate >= 85 ? "#10B981" : 
                            payload.utilization_rate >= 70 ? "#F59E0B" : "#EF4444";
                return <Bar {...props} fill={fill} />;
              }}
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (type === "pie") {
    const pieData = chartData.map(item => ({
      name: item.equipment_name,
      value: item.utilization_rate,
      equipment_name: item.equipment_name,
      utilization_rate: item.utilization_rate,
    }));

    return (
      <div style={{ width: "100%", height }}>
        <ResponsiveContainer>
          <PieChart>
            <Pie
              data={pieData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, value }) => value > 10 ? `${name}: ${value.toFixed(1)}%` : ''}
              outerRadius={Math.min(height * 0.35, 120)}
              fill="#8884d8"
              dataKey="value"
            >
              {pieData.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={COLORS[index % COLORS.length]} 
                />
              ))}
            </Pie>
            <Tooltip content={<PieTooltip />} />
            {showLegend && (
              <Legend 
                verticalAlign="bottom" 
                height={36}
                formatter={(value, entry: any) => (
                  <span style={{ color: entry.color }}>
                    {entry.payload.equipment_name}
                  </span>
                )}
              />
            )}
          </PieChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (type === "detailed") {
    const detailedData = chartData.map(item => ({
      name: item.equipment_name.length > 10 
        ? item.equipment_name.slice(0, 8) + "..." 
        : item.equipment_name,
      fullName: item.equipment_name,
      running: item.running_time,
      idle: item.idle_time,
      error: item.error_time,
      maintenance: item.maintenance_time,
      utilization_rate: item.utilization_rate,
      availability_rate: item.availability_rate,
    }));

    return (
      <div style={{ width: "100%", height }}>
        <ResponsiveContainer>
          <ComposedChart data={detailedData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis 
              dataKey="name" 
              angle={-45} 
              textAnchor="end" 
              height={80}
              fontSize={12}
              stroke="#6B7280"
            />
            <YAxis 
              yAxisId="left"
              fontSize={12}
              stroke="#6B7280"
            />
            <YAxis 
              yAxisId="right" 
              orientation="right" 
              domain={[0, 100]}
              fontSize={12}
              stroke="#6B7280"
            />
            <Tooltip 
              formatter={(value: any, name: string) => {
                if (name.includes("rate")) {
                  return [`${value.toFixed(1)}%`, name];
                }
                return [`${value.toFixed(1)}h`, name];
              }}
            />
            {showLegend && <Legend />}
            
            {/* Time Bars */}
            <Bar yAxisId="left" dataKey="running" stackId="a" fill="#10B981" name="가동시간" />
            <Bar yAxisId="left" dataKey="idle" stackId="a" fill="#F59E0B" name="대기시간" />
            <Bar yAxisId="left" dataKey="error" stackId="a" fill="#EF4444" name="오류시간" />
            <Bar yAxisId="left" dataKey="maintenance" stackId="a" fill="#8B5CF6" name="정비시간" />
            
            {/* Utilization Line */}
            <Line 
              yAxisId="right" 
              type="monotone" 
              dataKey="utilization_rate" 
              stroke="#3B82F6" 
              strokeWidth={3}
              name="가동률 (%)"
              dot={{ r: 4, fill: "#3B82F6" }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    );
  }

  return null;
}