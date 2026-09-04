import React from "react";
import { formatPercent, getMovementPolarity } from "@/lib/formatters/percentage";
import { ArrowUpRight, ArrowDownRight, Minus } from "lucide-react";

interface MetricProps {
  label: string;
  value: React.ReactNode;
  delta?: number | null;
  deltaLabel?: string;
  subtext?: string;
  size?: "hero" | "medium" | "compact";
  className?: string;
}

export function Metric({
  label,
  value,
  delta,
  deltaLabel,
  subtext,
  size = "medium",
  className = "",
}: MetricProps) {
  const polarity = getMovementPolarity(delta);

  return (
    <div className={`flex flex-col ${className}`}>
      <span className="text-[11px] uppercase tracking-wider font-mono text-[#64748B] font-medium mb-1">
        {label}
      </span>

      <div className="flex items-baseline gap-3">
        <span
          className={`tracking-tight text-[#0F172A] tabular-nums font-bold ${
            size === "hero"
              ? "text-5xl md:text-6xl"
              : size === "medium"
              ? "text-3xl"
              : "text-xl"
          }`}
        >
          {value}
        </span>

        {delta !== undefined && delta !== null && (
          <span
            className={`inline-flex items-center gap-0.5 text-xs font-mono font-semibold px-1.5 py-0.5 rounded-sm ${
              polarity === "positive"
                ? "bg-blue-50 text-[#1D4ED8]"
                : polarity === "negative"
                ? "bg-rose-50 text-[#DC2626]"
                : "bg-slate-100 text-[#64748B]"
            }`}
          >
            {polarity === "positive" && <ArrowUpRight className="h-3 w-3" />}
            {polarity === "negative" && <ArrowDownRight className="h-3 w-3" />}
            {polarity === "neutral" && <Minus className="h-3 w-3" />}
            {formatPercent(delta)}
          </span>
        )}
      </div>

      {(deltaLabel || subtext) && (
        <span className="text-xs text-[#64748B] mt-1 font-sans">
          {deltaLabel && <span className="mr-1">{deltaLabel}</span>}
          {subtext && <span className="opacity-90">{subtext}</span>}
        </span>
      )}
    </div>
  );
}
