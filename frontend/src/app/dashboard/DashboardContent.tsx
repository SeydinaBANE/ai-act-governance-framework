"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { RiskDistributionChart } from "@/components/dashboard/RiskDistributionChart";
import type { DashboardSummary } from "@/types/api";
import {
  CheckCircle,
  AlertTriangle,
  XCircle,
  HelpCircle,
} from "lucide-react";

export function DashboardContent() {
  const { data: summary, isLoading } = useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: () => api.get<DashboardSummary>("/dashboard/summary"),
  });

  const { data: actionsData } = useQuery({
    queryKey: ["actions-required"],
    queryFn: () =>
      api.get<{ actions: unknown[]; total: number }>("/dashboard/actions-required"),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (!summary) return null;

  const kpis = [
    {
      label: "Total systèmes",
      value: summary.total_systems,
      icon: HelpCircle,
      color: "text-gray-600",
      bg: "bg-gray-50",
    },
    {
      label: "Conformes",
      value: summary.compliant,
      icon: CheckCircle,
      color: "text-green-600",
      bg: "bg-green-50",
    },
    {
      label: "En évaluation",
      value: summary.under_review,
      icon: AlertTriangle,
      color: "text-yellow-600",
      bg: "bg-yellow-50",
    },
    {
      label: "Non conformes",
      value: summary.non_compliant,
      icon: XCircle,
      color: "text-red-600",
      bg: "bg-red-50",
    },
  ];

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {kpis.map((kpi) => (
          <div key={kpi.label} className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">{kpi.label}</p>
                <p className="mt-1 text-3xl font-bold text-gray-900">
                  {kpi.value}
                </p>
              </div>
              <div className={`rounded-lg p-3 ${kpi.bg}`}>
                <kpi.icon className={`h-6 w-6 ${kpi.color}`} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Risk Distribution */}
        <div className="card p-6">
          <h2 className="text-sm font-semibold text-gray-900 mb-4">
            Distribution par niveau de risque
          </h2>
          <RiskDistributionChart distribution={summary.risk_distribution} />
          <div className="mt-4 text-center">
            <p className="text-sm text-gray-500">
              Taux de conformité global :{" "}
              <span className="font-semibold text-green-600">
                {summary.compliance_rate}%
              </span>
            </p>
          </div>
        </div>

        {/* Actions requises */}
        <div className="card p-6">
          <h2 className="text-sm font-semibold text-gray-900 mb-4">
            Actions réglementaires requises
          </h2>
          {actionsData && actionsData.actions.length > 0 ? (
            <div className="space-y-3 max-h-48 overflow-y-auto">
              {(actionsData.actions as Array<{
                article: string;
                obligation: string;
                deadline: string;
              }>).slice(0, 8).map((action, i) => (
                <div
                  key={i}
                  className="flex items-start gap-3 p-3 rounded-md bg-orange-50 border border-orange-100"
                >
                  <span className="shrink-0 rounded bg-orange-200 px-1.5 py-0.5 text-xs font-mono font-semibold text-orange-800">
                    {action.article}
                  </span>
                  <div className="min-w-0">
                    <p className="text-xs text-gray-700 line-clamp-2">
                      {action.obligation}
                    </p>
                    <p className="mt-0.5 text-xs text-gray-400">
                      Échéance : {action.deadline}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex items-center justify-center h-32 text-sm text-gray-400">
              Aucune action requise
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
