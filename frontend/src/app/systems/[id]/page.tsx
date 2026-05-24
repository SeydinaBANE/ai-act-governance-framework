"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PageShell } from "@/components/layout/PageShell";
import type { AISystem, RiskAssessment, SystemStatus } from "@/types/api";
import { ArrowLeft, Shield, ClipboardList, FileText, Trash2, Edit2, Check, X } from "lucide-react";

const STATUS_LABELS: Record<SystemStatus, string> = {
  draft: "Brouillon",
  under_review: "En évaluation",
  compliant: "Conforme",
  non_compliant: "Non conforme",
  exempted: "Exempté",
};

const RISK_COLORS: Record<string, string> = {
  prohibited: "text-red-700 bg-red-50 border-red-200",
  high_risk: "text-orange-700 bg-orange-50 border-orange-200",
  limited_risk: "text-yellow-700 bg-yellow-50 border-yellow-200",
  minimal_risk: "text-green-700 bg-green-50 border-green-200",
};

const RISK_LABELS: Record<string, string> = {
  prohibited: "Interdit (Art. 5)",
  high_risk: "Haut risque (Annexe III)",
  limited_risk: "Risque limité",
  minimal_risk: "Risque minimal",
};

export default function SystemDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [editStatus, setEditStatus] = useState<SystemStatus | null>(null);

  const { data: system, isLoading } = useQuery({
    queryKey: ["system", id],
    queryFn: () => api.get<AISystem>(`/systems/${id}`),
  });

  const { data: assessments } = useQuery({
    queryKey: ["assessments", id],
    queryFn: () => api.get<{ items: RiskAssessment[]; total: number }>(`/risk/assessments/${id}`),
    enabled: !!id,
  });

  const updateMutation = useMutation({
    mutationFn: (status: SystemStatus) => api.patch<AISystem>(`/systems/${id}`, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["system", id] });
      setEditStatus(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => api.delete(`/systems/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["systems"] });
      router.push("/systems");
    },
  });

  if (isLoading) {
    return (
      <PageShell>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      </PageShell>
    );
  }

  if (!system) return null;

  const latestAssessment = assessments?.items[0];
  const riskKey = system.current_risk_category ?? latestAssessment?.risk_category;

  return (
    <PageShell>
      {/* Header */}
      <div className="mb-6 flex items-start justify-between">
        <div className="flex items-center gap-3">
          <Link href="/systems" className="text-gray-400 hover:text-gray-600">
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{system.name}</h1>
            <p className="text-sm text-gray-500 mt-0.5">
              {system.owner_team ?? "Équipe non renseignée"} · v{system.version ?? "N/A"}
            </p>
          </div>
        </div>
        <button
          onClick={() => { if (confirm("Supprimer ce système ?")) deleteMutation.mutate(); }}
          className="flex items-center gap-1 text-xs text-red-500 hover:text-red-700 border border-red-200 rounded px-2 py-1"
        >
          <Trash2 className="h-3 w-3" /> Supprimer
        </button>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Left col — details */}
        <div className="col-span-2 space-y-6">
          {/* Risk banner */}
          {riskKey && (
            <div className={`rounded-lg border p-4 ${RISK_COLORS[riskKey]}`}>
              <p className="text-xs font-semibold uppercase tracking-wide mb-1">Niveau de risque AI Act</p>
              <p className="text-lg font-bold">{RISK_LABELS[riskKey]}</p>
              {latestAssessment?.justification && (
                <p className="text-sm mt-1 opacity-80">{latestAssessment.justification}</p>
              )}
            </div>
          )}

          {/* Info card */}
          <div className="card p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-gray-900">Informations générales</h2>
              <div className="flex items-center gap-2">
                {editStatus !== null ? (
                  <>
                    <select
                      value={editStatus}
                      onChange={(e) => setEditStatus(e.target.value as SystemStatus)}
                      className="text-xs border border-gray-300 rounded px-2 py-1"
                    >
                      {Object.entries(STATUS_LABELS).map(([v, l]) => (
                        <option key={v} value={v}>{l}</option>
                      ))}
                    </select>
                    <button onClick={() => updateMutation.mutate(editStatus)} className="text-green-600 hover:text-green-700">
                      <Check className="h-4 w-4" />
                    </button>
                    <button onClick={() => setEditStatus(null)} className="text-gray-400 hover:text-gray-600">
                      <X className="h-4 w-4" />
                    </button>
                  </>
                ) : (
                  <button onClick={() => setEditStatus(system.status)} className="text-xs text-gray-400 hover:text-gray-600 flex items-center gap-1">
                    <Edit2 className="h-3 w-3" /> Statut
                  </button>
                )}
              </div>
            </div>

            <dl className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
              <div>
                <dt className="text-gray-500">Statut</dt>
                <dd className="font-medium">{STATUS_LABELS[system.status]}</dd>
              </div>
              <div>
                <dt className="text-gray-500">Environnement</dt>
                <dd className="font-medium capitalize">{system.deployment_env ?? "—"}</dd>
              </div>
              <div>
                <dt className="text-gray-500">Autonome</dt>
                <dd className="font-medium">{system.is_autonomous ? "Oui" : "Non"}</dd>
              </div>
              <div>
                <dt className="text-gray-500">Affecte des personnes</dt>
                <dd className="font-medium">{system.affects_persons ? "Oui" : "Non"}</dd>
              </div>
              {system.use_case && (
                <div className="col-span-2">
                  <dt className="text-gray-500">Cas d&apos;usage</dt>
                  <dd className="font-medium">{system.use_case}</dd>
                </div>
              )}
              {system.description && (
                <div className="col-span-2">
                  <dt className="text-gray-500">Description</dt>
                  <dd className="font-medium">{system.description}</dd>
                </div>
              )}
              {system.tech_stack && system.tech_stack.length > 0 && (
                <div className="col-span-2">
                  <dt className="text-gray-500 mb-1">Stack technique</dt>
                  <dd className="flex flex-wrap gap-1">
                    {system.tech_stack.map((t) => (
                      <span key={t} className="rounded-full bg-blue-50 px-2 py-0.5 text-xs text-blue-700">{t}</span>
                    ))}
                  </dd>
                </div>
              )}
              {system.data_types && system.data_types.length > 0 && (
                <div className="col-span-2">
                  <dt className="text-gray-500 mb-1">Données traitées</dt>
                  <dd className="flex flex-wrap gap-1">
                    {system.data_types.map((d) => (
                      <span key={d} className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">{d}</span>
                    ))}
                  </dd>
                </div>
              )}
            </dl>
          </div>

          {/* Required actions from latest assessment */}
          {latestAssessment?.required_actions && latestAssessment.required_actions.length > 0 && (
            <div className="card p-6">
              <h2 className="text-sm font-semibold text-gray-900 mb-3">Obligations réglementaires</h2>
              <div className="space-y-2">
                {latestAssessment.required_actions.slice(0, 5).map((action, i) => (
                  <div key={i} className="flex gap-3 rounded-md bg-orange-50 p-3">
                    <span className="shrink-0 rounded bg-orange-200 px-1.5 py-0.5 text-xs font-mono font-semibold text-orange-800">
                      {action.article}
                    </span>
                    <div className="min-w-0">
                      <p className="text-xs text-gray-700">{action.obligation}</p>
                      <p className="text-xs text-gray-400 mt-0.5">Échéance : {action.deadline}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right col — actions */}
        <div className="space-y-4">
          <div className="card p-4 space-y-3">
            <h3 className="text-sm font-semibold text-gray-900">Actions</h3>
            <Link
              href={`/systems/${id}/risk`}
              className="flex items-center gap-2 w-full rounded-md border border-gray-200 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
            >
              <Shield className="h-4 w-4 text-blue-500" />
              {latestAssessment ? "Réévaluer le risque" : "Évaluer le risque AI Act"}
            </Link>
            <Link
              href={`/systems/${id}/model-card`}
              className="flex items-center gap-2 w-full rounded-md border border-gray-200 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
            >
              <FileText className="h-4 w-4 text-purple-500" />
              Model Card
            </Link>
            <Link
              href={`/systems/${id}/audit`}
              className="flex items-center gap-2 w-full rounded-md border border-gray-200 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
            >
              <ClipboardList className="h-4 w-4 text-gray-500" />
              Journal d&apos;audit
            </Link>
          </div>

          {/* Assessment history */}
          {assessments && assessments.items.length > 0 && (
            <div className="card p-4">
              <h3 className="text-sm font-semibold text-gray-900 mb-3">Historique évaluations</h3>
              <div className="space-y-2">
                {assessments.items.slice(0, 5).map((a) => (
                  <div key={a.id} className="rounded-md bg-gray-50 p-2 text-xs">
                    <div className="font-medium capitalize">{a.risk_category.replace("_", " ")}</div>
                    <div className="text-gray-400">{new Date(a.created_at).toLocaleDateString("fr-FR")}</div>
                    <div className="text-gray-500">Score: {a.total_score}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </PageShell>
  );
}
