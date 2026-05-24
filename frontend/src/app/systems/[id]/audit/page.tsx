"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PageShell } from "@/components/layout/PageShell";
import type { AuditLog } from "@/types/api";
import { ArrowLeft } from "lucide-react";

export default function SystemAuditPage() {
  const { id } = useParams<{ id: string }>();

  const { data, isLoading } = useQuery({
    queryKey: ["system-audit", id],
    queryFn: () => api.get<{ items: AuditLog[]; total: number }>(`/audit/ai_system/${id}`),
  });

  return (
    <PageShell>
      <div className="mb-6 flex items-center gap-3">
        <Link href={`/systems/${id}`} className="text-gray-400 hover:text-gray-600">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Journal d&apos;audit</h1>
          <p className="text-sm text-gray-500 mt-0.5">Historique des actions sur ce système</p>
        </div>
      </div>

      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center h-48">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
          </div>
        ) : !data || data.items.length === 0 ? (
          <div className="flex items-center justify-center h-48 text-sm text-gray-400">
            Aucune entrée dans le journal d&apos;audit
          </div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Acteur</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Hash</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.items.map((log) => (
                <tr key={log.id} className="hover:bg-gray-50">
                  <td className="px-6 py-3 text-xs text-gray-500 whitespace-nowrap">
                    {new Date(log.created_at).toLocaleString("fr-FR")}
                  </td>
                  <td className="px-6 py-3 text-xs text-gray-700">{log.actor_email}</td>
                  <td className="px-6 py-3">
                    <span className="rounded bg-blue-50 px-2 py-0.5 text-xs font-mono text-blue-700">
                      {log.action}
                    </span>
                  </td>
                  <td className="px-6 py-3 text-xs text-gray-400 font-mono truncate max-w-[120px]" title={log.payload_hash}>
                    {log.payload_hash.slice(0, 12)}…
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </PageShell>
  );
}
