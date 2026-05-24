import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import type { RiskCategory } from "@/types/api";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export const RISK_LABELS: Record<RiskCategory, string> = {
  prohibited: "Interdit",
  high_risk: "Haut risque",
  limited_risk: "Risque limité",
  minimal_risk: "Risque minimal",
};

export const RISK_COLORS: Record<RiskCategory, string> = {
  prohibited: "bg-red-100 text-red-800 border-red-200",
  high_risk: "bg-orange-100 text-orange-800 border-orange-200",
  limited_risk: "bg-yellow-100 text-yellow-800 border-yellow-200",
  minimal_risk: "bg-green-100 text-green-800 border-green-200",
};

export const RISK_CHART_COLORS: Record<RiskCategory, string> = {
  prohibited: "#dc2626",
  high_risk: "#ea580c",
  limited_risk: "#ca8a04",
  minimal_risk: "#16a34a",
};

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
