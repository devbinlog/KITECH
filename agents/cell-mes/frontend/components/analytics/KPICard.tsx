"use client";

import { LucideIcon, TrendingUp, TrendingDown, Minus } from "lucide-react";

interface KPICardProps {
  title: string;
  value: string | number;
  unit?: string;
  icon: LucideIcon;
  color?: "blue" | "green" | "yellow" | "red" | "purple" | "indigo" | "gray";
  trend?: "up" | "down" | "neutral";
  trendValue?: string | number;
  target?: number;
  description?: string;
  className?: string;
}

const colorClasses = {
  blue: {
    bg: "bg-primary-100",
    icon: "text-primary-600",
    text: "text-primary-900",
  },
  green: {
    bg: "bg-green-100",
    icon: "text-green-600",
    text: "text-green-900",
  },
  yellow: {
    bg: "bg-yellow-100",
    icon: "text-yellow-600",
    text: "text-yellow-900",
  },
  red: {
    bg: "bg-red-100",
    icon: "text-red-600",
    text: "text-red-900",
  },
  purple: {
    bg: "bg-purple-100",
    icon: "text-purple-600",
    text: "text-purple-900",
  },
  indigo: {
    bg: "bg-primary-100",
    icon: "text-primary-600",
    text: "text-primary-900",
  },
  gray: {
    bg: "bg-gray-100",
    icon: "text-gray-600",
    text: "text-gray-900",
  },
};

const trendClasses = {
  up: {
    icon: TrendingUp,
    color: "text-green-600",
    bg: "bg-green-50",
  },
  down: {
    icon: TrendingDown,
    color: "text-red-600",
    bg: "bg-red-50",
  },
  neutral: {
    icon: Minus,
    color: "text-gray-600",
    bg: "bg-gray-50",
  },
};

export function KPICard({
  title,
  value,
  unit,
  icon: Icon,
  color = "blue",
  trend,
  trendValue,
  target,
  description,
  className = "",
}: KPICardProps) {
  const colorClass = colorClasses[color];
  const TrendIcon = trend ? trendClasses[trend].icon : null;
  const trendClass = trend ? trendClasses[trend] : null;

  const formatValue = (val: string | number) => {
    if (typeof val === "number") {
      return val.toLocaleString();
    }
    return val;
  };

  const isTargetMet = target !== undefined && typeof value === "number" && value >= target;

  return (
    <div className={`card p-6 ${className}`}>
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <p className="text-sm font-medium text-gray-600">{title}</p>
            {target !== undefined && (
              <div className={`px-1.5 py-0.5 rounded text-xs font-medium ${
                isTargetMet ? "bg-green-100 text-green-700" : "bg-yellow-100 text-yellow-700"
              }`}>
                목표: {target}{unit}
              </div>
            )}
          </div>
          
          <div className="flex items-baseline gap-1">
            <p className="text-2xl font-bold text-gray-900">
              {formatValue(value)}
            </p>
            {unit && (
              <span className="text-sm text-gray-500 font-medium">{unit}</span>
            )}
          </div>
          
          {description && (
            <p className="text-xs text-gray-500 mt-1">{description}</p>
          )}
        </div>
        
        <div className={`p-3 rounded-full ${colorClass.bg}`}>
          <Icon className={`h-6 w-6 ${colorClass.icon}`} />
        </div>
      </div>
      
      {/* Trend Indicator */}
      {trend && trendValue && TrendIcon && trendClass && (
        <div className="mt-4 flex items-center justify-between">
          <div className={`flex items-center gap-1 px-2 py-1 rounded-full ${trendClass.bg}`}>
            <TrendIcon className={`h-3 w-3 ${trendClass.color}`} />
            <span className={`text-xs font-medium ${trendClass.color}`}>
              {trendValue}
            </span>
          </div>
          
          {target !== undefined && (
            <div className="text-xs text-gray-500">
              {typeof value === "number" && (
                <span>
                  진척률: {((value / target) * 100).toFixed(0)}%
                </span>
              )}
            </div>
          )}
        </div>
      )}

      {/* Progress Bar for Target */}
      {target !== undefined && typeof value === "number" && (
        <div className="mt-3">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>진행률</span>
            <span>{((value / target) * 100).toFixed(0)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all duration-300 ${
                isTargetMet ? "bg-green-500" : "bg-primary-500"
              }`}
              style={{
                width: `${Math.min((value / target) * 100, 100)}%`,
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
}