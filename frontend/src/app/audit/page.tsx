"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PageShell } from "@/components/layout/PageShell";
import type { AuditLog } from "@/types/api";
import { ShieldCheck, ShieldAlert } from "lucide-react";

export default function AuditLogPage() {
  const [page, setPage] = useState(1);
  const [actionFilter, setActionFilter] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["audit-logs", page, actionFilter],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page), per_page: "50" });
      if (actionFilter) params.set("action", actionFilter);
      return api.get<{ items: AuditLog[]; total: number }>(`/audit?${params}`);
    },
  });

  const [verifiedHash, setVerifiedHash] = useState<Record<string, boolean | null>>({});

  async function verifyHash(logId: string) {
    try {
      const res = await api.get<{ valid: boolean }>(`/audit/entry/${logId}/verify`);
      setVerifiedHash(prev => ({ ...prev, [logId]: res.valid }));
    } catch {
      setVerifiedHash(prev => ({ ...prev, [logId]: false }));
    }
  }

  return (
    <PageShell>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Journal d&apos;audit</h1>
          <p className="mt-1 text-sm text-gray-500">Toutes les actions traçées avec intégrité SHA-256</p>
        </div>
        {data && (
          <span className="text-sm text-gray-500">{data.total} entrée(s)</span>
        )}
      </div>

      <div className="mb-4">
        <input
          type="text"
          placeholder="Filtrer par action (ex: ai_system.created)"
          value={actionFilter}
          onChange={(e) => { setActionFilter(e.target.value); setPage(1); }}
          className="w-full max-w-sm rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        />
      </div>

      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center h-48">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
          </div>
        ) : !data || data.items.length === 0 ? (
          <div className="flex items-center justify-center h-48 text-sm text-gray-400">
            Aucune entrée dans le journal
          </div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Acteur</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Ressource</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Intégrité</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.items.map((log) => (
                <tr key={log.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-xs text-gray-500 whitespace-nowrap">
                    {new Date(log.created_at).toLocaleString("fr-FR")}
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-700 max-w-[160px] truncate">{log.actor_email}</td>
                  <td className="px-4 py-3">
                    <span className="rounded bg-blue-50 px-2 py-0.5 text-xs font-mono text-blue-700">{log.action}</span>
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-500">
                    {log.resource_type && (
                      <span>{log.resource_type}</span>
                    )}
                    {log.resource_id && (
                      <span className="text-gray-300 ml-1 font-mono">{log.resource_id.slice(0, 8)}…</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {verifiedHash[log.id] === undefined ? (
                      <button
                        onClick={() => verifyHash(log.id)}
                        className="text-xs text-blue-500 hover:underline"
                      >
                        Vérifier
                      </button>
                    ) : verifiedHash[log.id] ? (
                      <span className="flex items-center gap-1 text-xs text-green-600">
                        <ShieldCheck className="h-3 w-3" /> Valide
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-xs text-red-600">
                        <ShieldAlert className="h-3 w-3" /> Invalide
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {data && data.total > 50 && (
        <div className="mt-4 flex items-center justify-end gap-2 text-sm">
          <button
            disabled={page === 1}
            onClick={() => setPage(p => p - 1)}
            className="rounded border border-gray-300 px-3 py-1 disabled:opacity-40"
          >
            Précédent
          </button>
          <span className="text-gray-500">Page {page}</span>
          <button
            disabled={page * 50 >= data.total}
            onClick={() => setPage(p => p + 1)}
            className="rounded border border-gray-300 px-3 py-1 disabled:opacity-40"
          >
            Suivant
          </button>
        </div>
      )}
    </PageShell>
  );
}
