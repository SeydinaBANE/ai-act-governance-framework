"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm, useFieldArray } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PageShell } from "@/components/layout/PageShell";
import type { AISystem } from "@/types/api";
import { Plus, Minus, ArrowLeft } from "lucide-react";
import Link from "next/link";

const schema = z.object({
  name: z.string().min(2, "Minimum 2 caractères"),
  description: z.string().optional(),
  version: z.string().optional(),
  owner_team: z.string().optional(),
  deployment_env: z.string().optional(),
  use_case: z.string().optional(),
  is_autonomous: z.boolean().default(false),
  affects_persons: z.boolean().default(false),
  tech_stack: z.array(z.object({ value: z.string() })).optional(),
  data_types: z.array(z.object({ value: z.string() })).optional(),
});

type FormValues = z.infer<typeof schema>;

export default function NewSystemPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [serverError, setServerError] = useState<string | null>(null);

  const { register, handleSubmit, control, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { is_autonomous: false, affects_persons: false, tech_stack: [{ value: "" }], data_types: [{ value: "" }] },
  });

  const { fields: techFields, append: appendTech, remove: removeTech } = useFieldArray({ control, name: "tech_stack" });
  const { fields: dataFields, append: appendData, remove: removeData } = useFieldArray({ control, name: "data_types" });

  const mutation = useMutation({
    mutationFn: (data: FormValues) => api.post<AISystem>("/systems", {
      ...data,
      tech_stack: data.tech_stack?.map(t => t.value).filter(Boolean) ?? [],
      data_types: data.data_types?.map(d => d.value).filter(Boolean) ?? [],
    }),
    onSuccess: (system) => {
      queryClient.invalidateQueries({ queryKey: ["systems"] });
      router.push(`/systems/${system.id}`);
    },
    onError: (err: Error) => setServerError(err.message),
  });

  return (
    <PageShell>
      <div className="max-w-2xl">
        <div className="mb-6 flex items-center gap-3">
          <Link href="/systems" className="text-gray-400 hover:text-gray-600">
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Nouveau système IA</h1>
            <p className="mt-1 text-sm text-gray-500">Enregistrez un nouveau système dans le registre</p>
          </div>
        </div>

        <form onSubmit={handleSubmit((d) => mutation.mutate(d))} className="card p-6 space-y-6">
          {serverError && (
            <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">{serverError}</div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">Nom du système *</label>
              <input {...register("name")} className="input w-full" placeholder="Ex: Scoring CV RH" />
              {errors.name && <p className="mt-1 text-xs text-red-600">{errors.name.message}</p>}
            </div>

            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea {...register("description")} rows={3} className="input w-full resize-none" placeholder="Décrivez le système..." />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Version</label>
              <input {...register("version")} className="input w-full" placeholder="1.0.0" />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Équipe propriétaire</label>
              <input {...register("owner_team")} className="input w-full" placeholder="DSI — IA & Data" />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Environnement de déploiement</label>
              <select {...register("deployment_env")} className="input w-full">
                <option value="">Sélectionner...</option>
                <option value="production">Production</option>
                <option value="staging">Staging</option>
                <option value="development">Développement</option>
                <option value="research">Recherche</option>
              </select>
            </div>

            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">Cas d&apos;usage</label>
              <textarea {...register("use_case")} rows={2} className="input w-full resize-none" placeholder="À quoi sert ce système ?" />
            </div>
          </div>

          {/* Tech stack */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-gray-700">Stack technologique</label>
              <button type="button" onClick={() => appendTech({ value: "" })} className="text-xs text-blue-600 hover:underline flex items-center gap-1">
                <Plus className="h-3 w-3" /> Ajouter
              </button>
            </div>
            <div className="space-y-2">
              {techFields.map((field, i) => (
                <div key={field.id} className="flex gap-2">
                  <input {...register(`tech_stack.${i}.value`)} className="input flex-1" placeholder="Python, FastAPI, PostgreSQL..." />
                  {techFields.length > 1 && (
                    <button type="button" onClick={() => removeTech(i)} className="text-gray-400 hover:text-red-500">
                      <Minus className="h-4 w-4" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Data types */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-gray-700">Types de données traitées</label>
              <button type="button" onClick={() => appendData({ value: "" })} className="text-xs text-blue-600 hover:underline flex items-center gap-1">
                <Plus className="h-3 w-3" /> Ajouter
              </button>
            </div>
            <div className="space-y-2">
              {dataFields.map((field, i) => (
                <div key={field.id} className="flex gap-2">
                  <input {...register(`data_types.${i}.value`)} className="input flex-1" placeholder="CV, emails, données biométriques..." />
                  {dataFields.length > 1 && (
                    <button type="button" onClick={() => removeData(i)} className="text-gray-400 hover:text-red-500">
                      <Minus className="h-4 w-4" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Flags */}
          <div className="space-y-3">
            <label className="flex items-center gap-3">
              <input type="checkbox" {...register("is_autonomous")} className="h-4 w-4 rounded border-gray-300 text-blue-600" />
              <div>
                <span className="text-sm font-medium text-gray-700">Système autonome</span>
                <p className="text-xs text-gray-400">Prend des décisions sans intervention humaine</p>
              </div>
            </label>
            <label className="flex items-center gap-3">
              <input type="checkbox" {...register("affects_persons")} className="h-4 w-4 rounded border-gray-300 text-blue-600" />
              <div>
                <span className="text-sm font-medium text-gray-700">Affecte des personnes physiques</span>
                <p className="text-xs text-gray-400">Les décisions ont un impact sur des individus</p>
              </div>
            </label>
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="submit"
              disabled={mutation.isPending}
              className="flex-1 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {mutation.isPending ? "Création..." : "Créer le système"}
            </button>
            <Link href="/systems" className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">
              Annuler
            </Link>
          </div>
        </form>
      </div>
    </PageShell>
  );
}
