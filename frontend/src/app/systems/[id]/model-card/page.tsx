"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PageShell } from "@/components/layout/PageShell";
import {
  ArrowLeft,
  Sparkles,
  Save,
  Send,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

interface ModelCard {
  id: string;
  ai_system_id: string;
  version: string;
  model_name: string;
  model_type: string | null;
  architecture: string | null;
  framework: string | null;
  license: string | null;
  preprocessing_steps: string | null;
  known_biases: string | null;
  evaluation_procedure: string | null;
  limitations: string | null;
  out_of_scope_uses: string | null;
  ethical_considerations: string | null;
  conformity_measures: string | null;
  human_oversight: string | null;
  developer_contact: string | null;
  dpo_contact: string | null;
  status: "draft" | "published" | "archived";
}

interface FormState {
  model_name: string;
  model_type: string;
  architecture: string;
  framework: string;
  license: string;
  preprocessing_steps: string;
  known_biases: string;
  evaluation_procedure: string;
  limitations: string;
  out_of_scope_uses: string;
  ethical_considerations: string;
  conformity_measures: string;
  human_oversight: string;
  developer_contact: string;
  dpo_contact: string;
}

const SECTIONS = [
  {
    id: "s1",
    title: "Informations générales",
    fields: [
      {
        key: "model_name",
        label: "Nom du modèle *",
        type: "input",
        required: true,
      },
      {
        key: "model_type",
        label: "Type de modèle",
        type: "input",
        placeholder: "Classification, NLP, Vision...",
      },
      {
        key: "architecture",
        label: "Architecture",
        type: "input",
        placeholder: "Transformer, CNN, BERT...",
      },
      {
        key: "framework",
        label: "Framework",
        type: "input",
        placeholder: "PyTorch, TensorFlow, scikit-learn...",
      },
      {
        key: "license",
        label: "Licence",
        type: "input",
        placeholder: "Apache 2.0, MIT, propriétaire...",
      },
    ],
  },
  {
    id: "s2",
    title: "Données et entraînement",
    fields: [
      {
        key: "preprocessing_steps",
        label: "Étapes de prétraitement",
        type: "textarea",
      },
      {
        key: "known_biases",
        label: "Biais connus",
        type: "textarea",
        aiGenerated: true,
      },
    ],
  },
  {
    id: "s3",
    title: "Performance et évaluation",
    fields: [
      {
        key: "evaluation_procedure",
        label: "Procédure d'évaluation",
        type: "textarea",
      },
    ],
  },
  {
    id: "s4",
    title: "Limitations et éthique",
    fields: [
      {
        key: "limitations",
        label: "Limitations connues",
        type: "textarea",
        aiGenerated: true,
      },
      {
        key: "out_of_scope_uses",
        label: "Usages hors périmètre",
        type: "textarea",
        aiGenerated: true,
      },
      {
        key: "ethical_considerations",
        label: "Considérations éthiques",
        type: "textarea",
        aiGenerated: true,
      },
    ],
  },
  {
    id: "s5",
    title: "Conformité AI Act",
    fields: [
      {
        key: "conformity_measures",
        label: "Mesures de conformité",
        type: "textarea",
        aiGenerated: true,
      },
      {
        key: "human_oversight",
        label: "Supervision humaine",
        type: "textarea",
        aiGenerated: true,
      },
    ],
  },
  {
    id: "s6",
    title: "Contacts",
    fields: [
      { key: "developer_contact", label: "Contact développeur", type: "input" },
      { key: "dpo_contact", label: "Contact DPO", type: "input" },
    ],
  },
];

export default function ModelCardPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [openSections, setOpenSections] = useState<Set<string>>(
    new Set(["s1"]),
  );
  const [isGenerating, setIsGenerating] = useState(false);
  const [form, setForm] = useState<FormState>({
    model_name: "",
    model_type: "",
    architecture: "",
    framework: "",
    license: "",
    preprocessing_steps: "",
    known_biases: "",
    evaluation_procedure: "",
    limitations: "",
    out_of_scope_uses: "",
    ethical_considerations: "",
    conformity_measures: "",
    human_oversight: "",
    developer_contact: "",
    dpo_contact: "",
  });

  const { data: cards } = useQuery<{ items: ModelCard[]; total: number }>({
    queryKey: ["model-cards", id],
    queryFn: () =>
      api.get<{ items: ModelCard[]; total: number }>(`/model-cards/${id}`),
  });

  useEffect(() => {
    if (cards?.items && cards.items.length > 0) {
      const card = cards.items[0];
      setForm({
        model_name: card.model_name ?? "",
        model_type: card.model_type ?? "",
        architecture: card.architecture ?? "",
        framework: card.framework ?? "",
        license: card.license ?? "",
        preprocessing_steps: card.preprocessing_steps ?? "",
        known_biases: card.known_biases ?? "",
        evaluation_procedure: card.evaluation_procedure ?? "",
        limitations: card.limitations ?? "",
        out_of_scope_uses: card.out_of_scope_uses ?? "",
        ethical_considerations: card.ethical_considerations ?? "",
        conformity_measures: card.conformity_measures ?? "",
        human_oversight: card.human_oversight ?? "",
        developer_contact: card.developer_contact ?? "",
        dpo_contact: card.dpo_contact ?? "",
      });
    }
  }, [cards]);

  const existingCard = cards?.items[0];

  const saveMutation = useMutation({
    mutationFn: () => {
      const payload = {
        ...form,
        model_type: form.model_type || undefined,
        architecture: form.architecture || undefined,
        framework: form.framework || undefined,
        license: form.license || undefined,
        preprocessing_steps: form.preprocessing_steps || undefined,
        known_biases: form.known_biases || undefined,
        evaluation_procedure: form.evaluation_procedure || undefined,
        limitations: form.limitations || undefined,
        out_of_scope_uses: form.out_of_scope_uses || undefined,
        ethical_considerations: form.ethical_considerations || undefined,
        conformity_measures: form.conformity_measures || undefined,
        human_oversight: form.human_oversight || undefined,
        developer_contact: form.developer_contact || undefined,
        dpo_contact: form.dpo_contact || undefined,
      };
      if (existingCard) {
        return api.patch<ModelCard>(`/model-cards/${existingCard.id}`, payload);
      }
      return api.post<ModelCard>(`/model-cards/${id}`, payload);
    },
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["model-cards", id] }),
  });

  const publishMutation = useMutation({
    mutationFn: () => api.post(`/model-cards/${existingCard!.id}/publish`, {}),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["model-cards", id] }),
  });

  async function handleGenerate() {
    setIsGenerating(true);
    try {
      const sections = await api.post<Record<string, string>>(
        `/model-cards/${id}/generate`,
        {},
      );
      setForm((prev) => ({
        ...prev,
        ...Object.fromEntries(
          Object.entries(sections).map(([k, v]) => [
            k,
            v || prev[k as keyof FormState],
          ]),
        ),
      }));
      setOpenSections(new Set(["s1", "s2", "s3", "s4", "s5", "s6"]));
    } catch {
      // silently ignore — error shown via API
    } finally {
      setIsGenerating(false);
    }
  }

  function toggleSection(sectionId: string) {
    setOpenSections((prev) => {
      const next = new Set(prev);
      next.has(sectionId) ? next.delete(sectionId) : next.add(sectionId);
      return next;
    });
  }

  function updateField(key: string, value: string) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  return (
    <PageShell>
      <div className="max-w-3xl">
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              href={`/systems/${id}`}
              className="text-gray-400 hover:text-gray-600"
            >
              <ArrowLeft className="h-5 w-5" />
            </Link>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Model Card</h1>
              <p className="text-sm text-gray-500 mt-0.5">
                {existingCard
                  ? `Statut : ${existingCard.status}`
                  : "Nouvelle model card"}
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleGenerate}
              disabled={isGenerating}
              className="flex items-center gap-2 rounded-md border border-purple-300 bg-purple-50 px-3 py-2 text-sm font-medium text-purple-700 hover:bg-purple-100 disabled:opacity-50"
            >
              <Sparkles className="h-4 w-4" />
              {isGenerating ? "Génération IA..." : "Auto-générer via IA"}
            </button>
            <button
              onClick={() => saveMutation.mutate()}
              disabled={!form.model_name || saveMutation.isPending}
              className="flex items-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              <Save className="h-4 w-4" />
              {saveMutation.isPending ? "Sauvegarde..." : "Sauvegarder"}
            </button>
            {existingCard && existingCard.status === "draft" && (
              <button
                onClick={() => publishMutation.mutate()}
                disabled={publishMutation.isPending}
                className="flex items-center gap-2 rounded-md bg-green-600 px-3 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
              >
                <Send className="h-4 w-4" />
                Publier
              </button>
            )}
          </div>
        </div>

        {saveMutation.isSuccess && (
          <div className="mb-4 rounded-md bg-green-50 p-3 text-sm text-green-700">
            Model card sauvegardée avec succès.
          </div>
        )}

        <div className="space-y-3">
          {SECTIONS.map((section) => {
            const isOpen = openSections.has(section.id);
            return (
              <div key={section.id} className="card overflow-hidden">
                <button
                  onClick={() => toggleSection(section.id)}
                  className="flex w-full items-center justify-between px-5 py-4 text-left"
                >
                  <span className="text-sm font-semibold text-gray-900">
                    {section.title}
                  </span>
                  {isOpen ? (
                    <ChevronUp className="h-4 w-4 text-gray-400" />
                  ) : (
                    <ChevronDown className="h-4 w-4 text-gray-400" />
                  )}
                </button>

                {isOpen && (
                  <div className="border-t border-gray-100 px-5 pb-5 pt-4 space-y-4">
                    {section.fields.map((field) => (
                      <div key={field.key}>
                        <div className="flex items-center gap-2 mb-1">
                          <label className="text-sm font-medium text-gray-700">
                            {field.label}
                          </label>
                          {"aiGenerated" in field && field.aiGenerated && (
                            <span className="rounded-full bg-purple-50 px-1.5 py-0.5 text-xs text-purple-600 border border-purple-200">
                              IA
                            </span>
                          )}
                        </div>
                        {field.type === "textarea" ? (
                          <textarea
                            value={form[field.key as keyof FormState]}
                            onChange={(e) =>
                              updateField(field.key, e.target.value)
                            }
                            rows={3}
                            placeholder={
                              "placeholder" in field
                                ? (field.placeholder as string)
                                : ""
                            }
                            className="input w-full resize-none text-sm"
                          />
                        ) : (
                          <input
                            type="text"
                            value={form[field.key as keyof FormState]}
                            onChange={(e) =>
                              updateField(field.key, e.target.value)
                            }
                            placeholder={
                              "placeholder" in field
                                ? (field.placeholder as string)
                                : ""
                            }
                            className="input w-full text-sm"
                          />
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Export PDF */}
        <div className="mt-6 card p-4 flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-900">
              Rapport de conformité PDF
            </p>
            <p className="text-xs text-gray-500 mt-0.5">
              Inclut le risk assessment, la model card et l&apos;audit trail
            </p>
          </div>
          <a
            href={`${process.env.NEXT_PUBLIC_API_URL}/exports/compliance-report/${id}`}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            onClick={(e) => {
              // Add auth token to download
              e.preventDefault();
              const token = localStorage.getItem("access_token");
              fetch(
                `${process.env.NEXT_PUBLIC_API_URL}/exports/compliance-report/${id}`,
                {
                  headers: { Authorization: `Bearer ${token}` },
                },
              )
                .then((r) => r.blob())
                .then((blob) => {
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement("a");
                  a.href = url;
                  a.download = `conformite_${id}.pdf`;
                  a.click();
                  URL.revokeObjectURL(url);
                });
            }}
          >
            Télécharger PDF
          </a>
        </div>
      </div>
    </PageShell>
  );
}
