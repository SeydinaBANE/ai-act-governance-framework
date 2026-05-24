"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PageShell } from "@/components/layout/PageShell";
import type { AISystemList, SystemStatus, RiskCategory } from "@/types/api";
import { Plus, Search, Cpu } from "lucide-react";

const STATUS_LABELS: Record<SystemStatus, string> = {
  draft: "Brouillon",
  under_review: "En évaluation",
  compliant: "Conforme",
  non_compliant: "Non conforme",
  exempted: "Exempté",
};

const STATUS_COLORS: Record<SystemStatus, string> = {
  draft: "bg-gray-100 text-gray-700",
  under_review: "bg-yellow-100 text-yellow-700",
  compliant: "bg-green-100 text-green-700",
  non_compliant: "bg-red-100 text-red-700",
  exempted: "bg-purple-100 text-purple-700",
};

const RISK_LABELS: Record<RiskCategory, string> = {
  prohibited: "Interdit",
  high_risk: "Haut risque",
  limited_risk: "Risque limité",
  minimal_risk: "Risque minimal",
};

const RISK_COLORS: Record<RiskCategory, string> = {
  prohibited: "bg-red-100 text-red-800",
  high_risk: "bg-orange-100 text-orange-800",
  limited_risk: "bg-yellow-100 text-yellow-800",
  minimal_risk: "bg-green-100 text-green-800",
};

export default function SystemsPage() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<SystemStatus | "">("");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ["systems", page, search, statusFilter],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page), per_page: "20" });
      if (search) params.set("search", search);
      if (statusFilter) params.set("status", statusFilter);
      return api.get<AISystemList>(`/systems?${params}`);
    },
  });

  return (
    <PageShell>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Systèmes IA</h1>
          <p className="mt-1 text-sm text-gray-500">
            Registre de vos systèmes d&apos;intelligence artificielle
          </p>
        </div>
        <Link
          href="/systems/new"
          className="flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          <Plus className="h-4 w-4" />
          Nouveau système
        </Link>
      </div>

      {/* Filters */}
      <div className="mb-4 flex gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Rechercher..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="w-full rounded-md border border-gray-300 pl-9 pr-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value as SystemStatus | ""); setPage(1); }}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        >
          <option value="">Tous les statuts</option>
          {Object.entries(STATUS_LABELS).map(([v, l]) => (
            <option key={v} value={v}>{l}</option>
          ))}
        </select>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center h-48">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
          </div>
        ) : !data || data.items.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 text-gray-400">
            <Cpu className="h-10 w-10 mb-2" />
            <p className="text-sm">Aucun système trouvé</p>
            <Link href="/systems/new" className="mt-2 text-sm text-blue-600 hover:underline">
              Ajouter un premier système
            </Link>
          </div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nom</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Équipe</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Statut</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Risque AI Act</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Version</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.items.map((system) => (
                <tr key={system.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <Link href={`/systems/${system.id}`} className="text-sm font-medium text-blue-600 hover:underline">
                      {system.name}
                    </Link>
                    {system.description && (
                      <p className="text-xs text-gray-400 mt-0.5 line-clamp-1">{system.description}</p>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">{system.owner_team ?? "—"}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[system.status]}`}>
                      {STATUS_LABELS[system.status]}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    {system.current_risk_category ? (
                      <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${RISK_COLORS[system.current_risk_category]}`}>
                        {RISK_LABELS[system.current_risk_category]}
                      </span>
                    ) : (
                      <span className="text-xs text-gray-400">Non évalué</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">{system.version ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {data && data.total > data.per_page && (
        <div className="mt-4 flex items-center justify-between text-sm text-gray-500">
          <span>{data.total} système(s) au total</span>
          <div className="flex gap-2">
            <button
              disabled={page === 1}
              onClick={() => setPage(p => p - 1)}
              className="rounded border border-gray-300 px-3 py-1 disabled:opacity-40 hover:bg-gray-50"
            >
              Précédent
            </button>
            <span className="px-2 py-1">Page {page}</span>
            <button
              disabled={page * data.per_page >= data.total}
              onClick={() => setPage(p => p + 1)}
              className="rounded border border-gray-300 px-3 py-1 disabled:opacity-40 hover:bg-gray-50"
            >
              Suivant
            </button>
          </div>
        </div>
      )}
    </PageShell>
  );
}
