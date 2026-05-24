"use client";

import { useState, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PageShell } from "@/components/layout/PageShell";
import type { PIIScan } from "@/types/api";
import { Upload, FileText, AlertTriangle, CheckCircle, Loader2 } from "lucide-react";

const RISK_COLORS: Record<string, string> = {
  critical: "bg-red-100 text-red-800",
  high: "bg-orange-100 text-orange-800",
  medium: "bg-yellow-100 text-yellow-800",
  low: "bg-green-100 text-green-800",
  none: "bg-gray-100 text-gray-600",
};

const RISK_LABELS: Record<string, string> = {
  critical: "Critique",
  high: "Élevé",
  medium: "Moyen",
  low: "Faible",
  none: "Aucun",
};

export default function PIIScannerPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<"text" | "file">("text");
  const [text, setText] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [lastScan, setLastScan] = useState<PIIScan | null>(null);

  const { data: scansHistory } = useQuery({
    queryKey: ["pii-scans"],
    queryFn: () => api.get<{ items: PIIScan[]; total: number }>("/pii/scans"),
  });

  const textMutation = useMutation({
    mutationFn: () => api.post<PIIScan>("/pii/scan/text", { text, confidence_threshold: 0.85 }),
    onSuccess: (data) => {
      setLastScan(data);
      queryClient.invalidateQueries({ queryKey: ["pii-scans"] });
    },
  });

  const fileMutation = useMutation({
    mutationFn: () => {
      if (!selectedFile) throw new Error("Aucun fichier sélectionné");
      return api.uploadFile<PIIScan>("/pii/scan/file", selectedFile);
    },
    onSuccess: (data) => {
      setLastScan(data);
      queryClient.invalidateQueries({ queryKey: ["pii-scans"] });
    },
  });

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) setSelectedFile(file);
  }, []);

  const isPending = textMutation.isPending || fileMutation.isPending;

  return (
    <PageShell>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Scanner PII</h1>
        <p className="mt-1 text-sm text-gray-500">
          Détection des données personnelles via Microsoft Presidio
        </p>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Scanner form */}
        <div className="col-span-2 space-y-4">
          {/* Tabs */}
          <div className="flex border-b border-gray-200">
            {(["text", "file"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab
                    ? "border-blue-600 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700"
                }`}
              >
                {tab === "text" ? <><FileText className="h-4 w-4" /> Texte libre</> : <><Upload className="h-4 w-4" /> Fichier</>}
              </button>
            ))}
          </div>

          {activeTab === "text" ? (
            <div className="card p-4 space-y-4">
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={8}
                placeholder="Collez ici un texte à analyser (emails, CVs, contrats, données...)&#10;&#10;Exemple : Jean Dupont, 12 rue de la Paix, Paris. Email : jean.dupont@example.com, Tél : 06 12 34 56 78. NIR : 1 85 12 75 108 337 48"
                className="input w-full resize-none font-mono text-sm"
              />
              <button
                onClick={() => textMutation.mutate()}
                disabled={!text.trim() || isPending}
                className="flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {isPending ? <><Loader2 className="h-4 w-4 animate-spin" /> Analyse...</> : "Analyser le texte"}
              </button>
            </div>
          ) : (
            <div className="card p-4 space-y-4">
              <div
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                className={`rounded-lg border-2 border-dashed p-8 text-center transition-colors ${
                  dragOver ? "border-blue-400 bg-blue-50" : "border-gray-300"
                }`}
              >
                <Upload className="mx-auto h-10 w-10 text-gray-300 mb-3" />
                <p className="text-sm text-gray-600">
                  Glissez un fichier ici ou{" "}
                  <label className="cursor-pointer text-blue-600 hover:underline">
                    parcourir
                    <input
                      type="file"
                      accept=".txt,.csv,.json"
                      className="hidden"
                      onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
                    />
                  </label>
                </p>
                <p className="text-xs text-gray-400 mt-1">TXT, CSV, JSON · max 10 MB</p>
              </div>
              {selectedFile && (
                <div className="flex items-center gap-2 rounded-md bg-gray-50 p-3 text-sm">
                  <FileText className="h-4 w-4 text-gray-400" />
                  <span className="flex-1 truncate">{selectedFile.name}</span>
                  <span className="text-xs text-gray-400">{(selectedFile.size / 1024).toFixed(1)} KB</span>
                  <button onClick={() => setSelectedFile(null)} className="text-gray-400 hover:text-red-500">×</button>
                </div>
              )}
              <button
                onClick={() => fileMutation.mutate()}
                disabled={!selectedFile || isPending}
                className="flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {isPending ? <><Loader2 className="h-4 w-4 animate-spin" /> Analyse...</> : "Scanner le fichier"}
              </button>
            </div>
          )}

          {/* Error */}
          {(textMutation.error || fileMutation.error) && (
            <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">
              {((textMutation.error || fileMutation.error) as Error)?.message}
            </div>
          )}

          {/* Results */}
          {lastScan && (
            <div className="card p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold text-gray-900">Résultats du scan</h2>
                <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${RISK_COLORS[lastScan.risk_level ?? "none"]}`}>
                  Risque {RISK_LABELS[lastScan.risk_level ?? "none"]}
                </span>
              </div>

              {lastScan.pii_found ? (
                <>
                  <div className="flex items-center gap-2 text-sm text-orange-700">
                    <AlertTriangle className="h-4 w-4" />
                    {lastScan.findings.length} occurrence(s) de données personnelles détectées
                  </div>

                  {lastScan.entity_summary && (
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(lastScan.entity_summary).map(([type, count]) => (
                        <span key={type} className="rounded-full bg-orange-50 border border-orange-200 px-3 py-1 text-xs font-medium text-orange-700">
                          {type} × {count}
                        </span>
                      ))}
                    </div>
                  )}

                  <div className="max-h-48 overflow-y-auto space-y-2">
                    {lastScan.findings.slice(0, 20).map((f, i) => (
                      <div key={i} className="flex items-center gap-3 rounded-md bg-gray-50 px-3 py-2 text-xs">
                        <span className="rounded bg-red-100 px-1.5 py-0.5 font-semibold text-red-700">{f.entity_type}</span>
                        <span className="text-gray-500">confiance: {(f.score * 100).toFixed(0)}%</span>
                        {f.context && <span className="text-gray-400 italic truncate">&quot;{f.context}&quot;</span>}
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <div className="flex items-center gap-2 text-sm text-green-700">
                  <CheckCircle className="h-4 w-4" />
                  Aucune donnée personnelle détectée
                </div>
              )}

              {lastScan.recommendations && lastScan.recommendations.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-gray-500 mb-2">Recommandations</p>
                  <ul className="space-y-1">
                    {lastScan.recommendations.map((r, i) => (
                      <li key={i} className="text-xs text-gray-600 flex items-start gap-2">
                        <span className="text-blue-400 mt-0.5">•</span> {r}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* History */}
        <div className="card p-4">
          <h2 className="text-sm font-semibold text-gray-900 mb-3">Historique des scans</h2>
          {!scansHistory || scansHistory.items.length === 0 ? (
            <p className="text-xs text-gray-400 text-center py-8">Aucun scan effectué</p>
          ) : (
            <div className="space-y-2">
              {scansHistory.items.map((scan) => (
                <div key={scan.id} className="rounded-md border border-gray-100 p-2">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-medium capitalize">{scan.source_type}</span>
                    <span className={`rounded-full px-1.5 py-0.5 text-xs ${scan.pii_found ? "bg-red-50 text-red-600" : "bg-green-50 text-green-600"}`}>
                      {scan.pii_found ? `${scan.findings.length} PII` : "Clean"}
                    </span>
                  </div>
                  {scan.source_name && <p className="text-xs text-gray-400 truncate">{scan.source_name}</p>}
                  <p className="text-xs text-gray-300 mt-0.5">{new Date(scan.created_at).toLocaleDateString("fr-FR")}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </PageShell>
  );
}
