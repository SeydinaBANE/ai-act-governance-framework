"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PageShell } from "@/components/layout/PageShell";
import type { RiskAssessment } from "@/types/api";
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle,
  AlertTriangle,
  XCircle,
  AlertOctagon,
} from "lucide-react";
import Link from "next/link";

interface Question {
  id: string;
  text: string;
  type: string;
  ai_act_ref?: string;
  triggers_prohibited?: boolean;
  triggers_high_risk?: boolean;
}
interface Section {
  id: string;
  title: string;
  questions: Question[];
}
interface Questionnaire {
  version: string;
  sections: Section[];
}

const RISK_ICONS = {
  prohibited: AlertOctagon,
  high_risk: XCircle,
  limited_risk: AlertTriangle,
  minimal_risk: CheckCircle,
};
const RISK_COLORS = {
  prohibited: "text-red-700 bg-red-50 border-red-300",
  high_risk: "text-orange-700 bg-orange-50 border-orange-300",
  limited_risk: "text-yellow-700 bg-yellow-50 border-yellow-300",
  minimal_risk: "text-green-700 bg-green-50 border-green-300",
};
const RISK_LABELS = {
  prohibited: "Système INTERDIT",
  high_risk: "Haut risque",
  limited_risk: "Risque limité",
  minimal_risk: "Risque minimal",
};

export default function RiskScorerPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();

  const [currentSection, setCurrentSection] = useState(0);
  const [answers, setAnswers] = useState<Record<string, boolean>>({});
  const [result, setResult] = useState<RiskAssessment | null>(null);

  const { data: questionnaire, isLoading } = useQuery({
    queryKey: ["questionnaire"],
    queryFn: () => api.get<Questionnaire>("/risk/questionnaire"),
  });

  const mutation = useMutation({
    mutationFn: () =>
      api.post<RiskAssessment>(`/risk/assess/${id}`, { answers }),
    onSuccess: (data) => {
      setResult(data);
      queryClient.invalidateQueries({ queryKey: ["system", id] });
      queryClient.invalidateQueries({ queryKey: ["assessments", id] });
    },
  });

  if (isLoading || !questionnaire) {
    return (
      <PageShell>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      </PageShell>
    );
  }

  const sections = questionnaire.sections;
  const section = sections[currentSection];
  const totalSections = sections.length;
  const isLast = currentSection === totalSections - 1;
  const allQuestionsAnswered = section.questions.every(
    (q) => answers[q.id] !== undefined,
  );

  if (result) {
    const riskKey = result.risk_category as keyof typeof RISK_COLORS;
    const Icon = RISK_ICONS[riskKey];
    return (
      <PageShell>
        <div className="max-w-2xl">
          <div className={`rounded-xl border-2 p-8 ${RISK_COLORS[riskKey]}`}>
            <div className="flex items-center gap-3 mb-4">
              <Icon className="h-10 w-10" />
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide opacity-70">
                  Résultat AI Act
                </p>
                <h2 className="text-2xl font-bold">{RISK_LABELS[riskKey]}</h2>
              </div>
            </div>
            <p className="text-sm opacity-80 mb-6">{result.justification}</p>

            {result.ai_act_articles && result.ai_act_articles.length > 0 && (
              <div className="mb-4">
                <p className="text-xs font-semibold uppercase tracking-wide opacity-70 mb-2">
                  Articles applicables
                </p>
                <div className="flex flex-wrap gap-2">
                  {result.ai_act_articles.map((a) => (
                    <span
                      key={a}
                      className="rounded bg-white bg-opacity-50 px-2 py-0.5 text-xs font-mono font-semibold"
                    >
                      {a}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="text-sm opacity-70">
              Score : {result.total_score} / 100
            </div>
          </div>

          {result.required_actions && result.required_actions.length > 0 && (
            <div className="mt-6 card p-6">
              <h3 className="text-sm font-semibold text-gray-900 mb-3">
                Obligations réglementaires ({result.required_actions.length})
              </h3>
              <div className="space-y-3">
                {result.required_actions.map((action, i) => (
                  <div
                    key={i}
                    className="flex gap-3 rounded-md bg-orange-50 p-3"
                  >
                    <span className="shrink-0 rounded bg-orange-200 px-1.5 py-0.5 text-xs font-mono font-semibold text-orange-800">
                      {action.article}
                    </span>
                    <div>
                      <p className="text-sm text-gray-700">
                        {action.obligation}
                      </p>
                      <p className="text-xs text-gray-400 mt-0.5">
                        Échéance : {action.deadline}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="mt-6 flex gap-3">
            <Link
              href={`/systems/${id}`}
              className="flex-1 rounded-md bg-blue-600 px-4 py-2 text-center text-sm font-medium text-white hover:bg-blue-700"
            >
              Retour au système
            </Link>
            <button
              onClick={() => {
                setResult(null);
                setAnswers({});
                setCurrentSection(0);
              }}
              className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Recommencer
            </button>
          </div>
        </div>
      </PageShell>
    );
  }

  return (
    <PageShell>
      <div className="max-w-2xl">
        <div className="mb-6 flex items-center gap-3">
          <Link
            href={`/systems/${id}`}
            className="text-gray-400 hover:text-gray-600"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Évaluation AI Act
            </h1>
            <p className="text-sm text-gray-500 mt-0.5">
              Section {currentSection + 1} / {totalSections}
            </p>
          </div>
        </div>

        {/* Progress bar */}
        <div className="mb-6 h-2 rounded-full bg-gray-200">
          <div
            className="h-2 rounded-full bg-blue-600 transition-all"
            style={{
              width: `${((currentSection + 1) / totalSections) * 100}%`,
            }}
          />
        </div>

        <div className="card p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-4">
            {section.title}
          </h2>

          <div className="space-y-6">
            {section.questions.map((q) => (
              <div
                key={q.id}
                className="border-b border-gray-100 pb-4 last:border-0 last:pb-0"
              >
                <div className="flex items-start gap-2 mb-2">
                  <p className="text-sm text-gray-700 flex-1">{q.text}</p>
                  {q.ai_act_ref && (
                    <span className="shrink-0 rounded bg-blue-50 px-1.5 py-0.5 text-xs font-mono text-blue-600">
                      {q.ai_act_ref}
                    </span>
                  )}
                </div>
                {q.triggers_prohibited && (
                  <p className="text-xs text-red-500 mb-2">
                    ⚠ Une réponse &quot;Oui&quot; entraîne une classification
                    INTERDITE
                  </p>
                )}
                <div className="flex gap-3">
                  {[true, false].map((val) => (
                    <button
                      key={String(val)}
                      onClick={() =>
                        setAnswers((prev) => ({ ...prev, [q.id]: val }))
                      }
                      className={`flex-1 rounded-md border py-2 text-sm font-medium transition-colors ${
                        answers[q.id] === val
                          ? val
                            ? "border-red-400 bg-red-50 text-red-700"
                            : "border-green-400 bg-green-50 text-green-700"
                          : "border-gray-200 text-gray-600 hover:bg-gray-50"
                      }`}
                    >
                      {val ? "Oui" : "Non"}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 flex gap-3">
            {currentSection > 0 && (
              <button
                onClick={() => setCurrentSection((s) => s - 1)}
                className="flex items-center gap-1 rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
              >
                <ArrowLeft className="h-4 w-4" /> Précédent
              </button>
            )}
            <div className="flex-1" />
            {isLast ? (
              <button
                onClick={() => mutation.mutate()}
                disabled={!allQuestionsAnswered || mutation.isPending}
                className="flex items-center gap-2 rounded-md bg-blue-600 px-6 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {mutation.isPending
                  ? "Analyse..."
                  : "Obtenir l'évaluation AI Act"}
              </button>
            ) : (
              <button
                onClick={() => setCurrentSection((s) => s + 1)}
                disabled={!allQuestionsAnswered}
                className="flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                Suivant <ArrowRight className="h-4 w-4" />
              </button>
            )}
          </div>
          {!allQuestionsAnswered && (
            <p className="text-xs text-gray-400 text-center mt-2">
              Répondez à toutes les questions pour continuer
            </p>
          )}
        </div>
      </div>
    </PageShell>
  );
}
