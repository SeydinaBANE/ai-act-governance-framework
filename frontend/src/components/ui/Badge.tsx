import { cn, RISK_COLORS, RISK_LABELS } from "@/lib/utils";
import type { RiskCategory } from "@/types/api";

interface RiskBadgeProps {
  category: RiskCategory;
  className?: string;
}

export function RiskBadge({ category, className }: RiskBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold",
        RISK_COLORS[category],
        className,
      )}
    >
      {RISK_LABELS[category]}
    </span>
  );
}

interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "success" | "warning" | "danger" | "info";
  className?: string;
}

const BADGE_VARIANTS: Record<NonNullable<BadgeProps["variant"]>, string> = {
  default: "bg-gray-100 text-gray-800 border-gray-200",
  success: "bg-green-100 text-green-800 border-green-200",
  warning: "bg-yellow-100 text-yellow-800 border-yellow-200",
  danger: "bg-red-100 text-red-800 border-red-200",
  info: "bg-blue-100 text-blue-800 border-blue-200",
};

export function Badge({
  children,
  variant = "default",
  className,
}: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold",
        BADGE_VARIANTS[variant],
        className,
      )}
    >
      {children}
    </span>
  );
}
