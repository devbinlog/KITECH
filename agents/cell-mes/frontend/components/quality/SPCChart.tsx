"use client";

import { SPCData } from "@/types";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ComposedChart,
  Area,
  ReferenceLine
} from "recharts";

interface SPCChartProps {
  data: SPCData[];
  title: string;
  type: "xbar" | "r";
  height?: number;
}

interface CustomDotProps {
  cx?: number;
  cy?: number;
  payload?: any;
}

export function SPCChart({ data, title, type, height = 300 }: SPCChartProps) {
  const processedData = data.map((item, index) => ({
    sample: index + 1,
    value: type === "xbar" ? item.x_bar : item.r_value,
    ucl: type === "xbar" ? item.ucl_x : item.ucl_r,
    lcl: type === "xbar" ? item.lcl_x : item.lcl_r,
    centerLine: type === "xbar" 
      ? (item.ucl_x + item.lcl_x) / 2 
      : (item.ucl_r + item.lcl_r) / 2,
    date: new Date(item.sample_date).toLocaleDateString(),
    isOOC: type === "xbar" 
      ? (item.x_bar > item.ucl_x || item.x_bar < item.lcl_x)
      : (item.r_value > item.ucl_r || item.r_value < item.lcl_r),
  }));

  const CustomDot = ({ cx, cy, payload }: CustomDotProps) => {
    if (cx === undefined || cy === undefined || !payload) return null;
    
    return (
      <circle
        cx={cx}
        cy={cy}
        r={4}
        fill={payload.isOOC ? "#ef4444" : "#3b82f6"}
        stroke={payload.isOOC ? "#dc2626" : "#2563eb"}
        strokeWidth={2}
      />
    );
  };

  const formatValue = (value: any) => typeof value === 'number' ? value.toFixed(3) : value;

  return (
    <div className="w-full" style={{ height }}>
      <div className="mb-2">
        <h3 className="text-sm font-medium text-gray-700">{title}</h3>
      </div>
      
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={processedData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis 
            dataKey="sample" 
            stroke="#6b7280"
            fontSize={12}
            tickLine={false}
          />
          <YAxis 
            stroke="#6b7280"
            fontSize={12}
            tickLine={false}
            tickFormatter={(value) => value.toFixed(2)}
          />
          <Tooltip 
            labelFormatter={(label) => `샘플 #${label}`}
            formatter={(value: any, name: string) => {
              switch(name) {
                case 'value':
                  return [formatValue(value), type === 'xbar' ? 'X̄' : 'R'];
                case 'ucl':
                  return [formatValue(value), 'UCL'];
                case 'lcl':
                  return [formatValue(value), 'LCL'];
                case 'centerLine':
                  return [formatValue(value), 'CL'];
                default:
                  return [formatValue(value), name];
              }
            }}
            contentStyle={{
              backgroundColor: '#ffffff',
              border: '1px solid #e5e7eb',
              borderRadius: '6px',
              fontSize: '12px'
            }}
          />
          
          {/* Control Limits */}
          <Line 
            type="monotone"
            dataKey="ucl" 
            stroke="#f59e0b" 
            strokeDasharray="5 5"
            strokeWidth={2}
            dot={false}
            connectNulls={false}
            name="UCL"
          />
          <Line 
            type="monotone"
            dataKey="lcl" 
            stroke="#f59e0b" 
            strokeDasharray="5 5" 
            strokeWidth={2}
            dot={false}
            connectNulls={false}
            name="LCL"
          />
          <Line 
            type="monotone"
            dataKey="centerLine" 
            stroke="#6b7280" 
            strokeDasharray="2 2" 
            strokeWidth={1}
            dot={false}
            connectNulls={false}
            name="CL"
          />
          
          {/* Data Line with Custom Dots */}
          <Line 
            type="monotone" 
            dataKey="value" 
            stroke="#3b82f6" 
            strokeWidth={2}
            dot={<CustomDot />}
            connectNulls={false}
            name="value"
          />
        </ComposedChart>
      </ResponsiveContainer>
      
      {/* Control Limits Legend */}
      <div className="mt-2 flex justify-center gap-4 text-xs text-gray-600">
        <div className="flex items-center gap-1">
          <div className="w-4 h-0.5 bg-yellow-500 border-dashed" style={{ borderTop: '1px dashed' }} />
          <span>관리한계</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-4 h-0.5 bg-gray-500 border-dashed" style={{ borderTop: '1px dashed' }} />
          <span>중심선</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-primary-500 rounded-full" />
          <span>관리상태</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-red-500 rounded-full" />
          <span>관리이탈</span>
        </div>
      </div>
    </div>
  );
}