"use client";

import React from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

type FlaggedData = {
  name: string;
  flagged: number;
};

interface DashboardChartProps {
  data: FlaggedData[];
}

// Simple chart wrapper
export const DashboardChart: React.FC<DashboardChartProps> = ({ data }) => {
  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={data}
          margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
        >
          <defs>
            <linearGradient id="colorFlagged" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#6366F1" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#6366F1" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" vertical={false} />
          <XAxis dataKey="name" stroke="#6B7280" fontSize={12} />
          <YAxis stroke="#6B7280" fontSize={12} />
          <Tooltip
            contentStyle={{
              backgroundColor: "#F9FAFB",
              borderColor: "#D1D5DB",
              borderRadius: "8px",
              boxShadow: "0 4px 6px -1px rgba(0,0,0,0.1)",
            }}
            itemStyle={{ color: "#111827" }}
          />
          <Area
            type="monotone"
            dataKey="flagged"
            stroke="#6366F1"
            strokeWidth={2}
            fill="url(#colorFlagged)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

// Example usage
const chartData: FlaggedData[] = [
  { name: "Mon", flagged: 12 },
  { name: "Tue", flagged: 19 },
  { name: "Wed", flagged: 15 },
  { name: "Thu", flagged: 22 },
  { name: "Fri", flagged: 28 },
  { name: "Sat", flagged: 14 },
  { name: "Sun", flagged: 18 },
];

export const ExampleChart = () => <DashboardChart data={chartData} />;
