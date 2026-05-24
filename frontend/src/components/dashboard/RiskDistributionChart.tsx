"use client";

import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { RISK_CHART_COLORS, RISK_LABELS } from "@/lib/utils";
import type { RiskCategory } from "@/types/api";

interface RiskDistributionChartProps {
  distribution: Record<RiskCategory, number>;
}

export function RiskDistributionChart({
  distribution,
}: RiskDistributionChartProps) {
  const data = (Object.entries(distribution) as [RiskCategory, number][])
    .filter(([, value]) => value > 0)
    .map(([key, value]) => ({
      name: RISK_LABELS[key],
      value,
      color: RISK_CHART_COLORS[key],
    }));

  if (data.length === 0) {
    return (
      <div className="flex h-48 items-center justify-center text-sm text-gray-400">
        Aucun système évalué
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={90}
          paddingAngle={2}
          dataKey="value"
        >
          {data.map((entry, index) => (
            <Cell key={index} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip
          formatter={(value: number, name: string) => [value, name]}
        />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}
